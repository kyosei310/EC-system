from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from .models import Category, Item, ItemsInCart, Purchase, PurchaseDetail
from account.models import AccountUser


def update_cart(request, cart_id):
    """カート内商品の数量変更"""
    login_user = get_login_user(request)
    if not login_user:
        return redirect('/account/login/')

    cart_item = get_object_or_404(ItemsInCart, pk=cart_id, user=login_user)

    if request.method == 'POST':
        try:
            new_amount = int(request.POST.get('amount', 1))
        except ValueError:
            new_amount = 1

        if new_amount < 1:
            new_amount = 1
        if new_amount > cart_item.item.stock:
            new_amount = cart_item.item.stock

        cart_item.amount = new_amount
        cart_item.save()

    return redirect('shopping:cart')


def delete_cart(request, cart_id):
    """カート内商品の削除"""
    login_user = get_login_user(request)
    if not login_user:
        return redirect('/account/login/')

    cart_item = get_object_or_404(ItemsInCart, pk=cart_id, user=login_user)

    if request.method == 'POST':
        cart_item.delete()

    return redirect('shopping:cart')



def purchase(request):
    """配送先入力画面"""
    login_user = get_login_user(request)
    if not login_user:
        return redirect('/account/login/')

    cart_items = ItemsInCart.objects.filter(user=login_user).select_related('item')
    if not cart_items.exists():
        return redirect('shopping:cart')

    total = sum(ci.item.price * ci.amount for ci in cart_items)

    context = {
        'login_user': login_user,
        'cart_items': cart_items,
        'total': total,
        'default_address': login_user.address,
    }
    return render(request, 'shopping/purchase.html', context)


def purchase_confirm(request):
    """購入確認画面"""
    login_user = get_login_user(request)
    if not login_user:
        return redirect('/account/login/')

    if request.method != 'POST':
        return redirect('shopping:purchase')

    destination_type = request.POST.get('destination_type', 'registered')
    if destination_type == 'other':
        destination = request.POST.get('other_address', '').strip()
    else:
        destination = login_user.address

    if not destination:
        cart_items = ItemsInCart.objects.filter(user=login_user).select_related('item')
        total = sum(ci.item.price * ci.amount for ci in cart_items)
        context = {
            'login_user': login_user,
            'cart_items': cart_items,
            'total': total,
            'default_address': login_user.address,
            'message': '配送先住所を入力してください。',
        }
        return render(request, 'shopping/purchase.html', context)

    request.session['purchase_destination'] = destination

    cart_items = ItemsInCart.objects.filter(user=login_user).select_related('item')
    total = sum(ci.item.price * ci.amount for ci in cart_items)

    context = {
        'login_user': login_user,
        'cart_items': cart_items,
        'total': total,
        'destination': destination,
        'payment_method': '代金引換',
    }
    return render(request, 'shopping/purchaseConfirm.html', context)


@transaction.atomic
def purchase_commit(request):
    """購入確定処理"""
    login_user = get_login_user(request)
    if not login_user:
        return redirect('/account/login/')

    if request.method != 'POST':
        return redirect('shopping:purchase')

    destination = request.session.pop('purchase_destination', None)
    if not destination:
        return redirect('shopping:purchase')

    cart_items = list(
        ItemsInCart.objects.filter(user=login_user).select_related('item')
    )
    if not cart_items:
        return redirect('shopping:cart')

    for ci in cart_items:
        if ci.amount > ci.item.stock:
            request.session['purchase_destination'] = destination  
            return render(request, 'shopping/purchase.html', {
                'login_user': login_user,
                'cart_items': cart_items,
                'total': sum(c.item.price * c.amount for c in cart_items),
                'default_address': login_user.address,
                'message': f'「{ci.item.name}」の在庫が不足しています。',
            })

    last_purchase = Purchase.objects.order_by('-purchase_id').first()
    new_purchase_id = (last_purchase.purchase_id + 1) if last_purchase else 1

    purchase = Purchase()
    purchase.purchase_id = new_purchase_id
    purchase.destination = destination
    purchase.cancel = False
    purchase.user = login_user
    purchase.save()

    last_detail = PurchaseDetail.objects.order_by('-purchase_detail_id').first()
    next_detail_id = (last_detail.purchase_detail_id + 1) if last_detail else 1

    for ci in cart_items:
        detail = PurchaseDetail()
        detail.purchase_detail_id = next_detail_id
        detail.amount = ci.amount
        detail.item = ci.item
        detail.purchase = purchase
        detail.save()
        next_detail_id += 1

        ci.item.stock -= ci.amount
        ci.item.save()

    ItemsInCart.objects.filter(user=login_user).delete()

    context = {
        'login_user': login_user,
        'purchase': purchase,
    }
    return render(request, 'shopping/purchaseCommit.html', context)



def purchase_history(request):
    """購入履歴一覧"""
    login_user = get_login_user(request)
    if not login_user:
        return redirect('/account/login/')

    purchases = (
        Purchase.objects
        .filter(user=login_user)
        .order_by('-booked_date')
    )

    history = []
    for p in purchases:
        details = PurchaseDetail.objects.filter(purchase=p).select_related('item')
        total = sum(d.item.price * d.amount for d in details)
        item_count = sum(d.amount for d in details) 
        items = [
            {
                'name': d.item.name,
                'price': d.item.price,
                'amount': d.amount,
            }
            for d in details
        ]
        history.append({
            'purchase': p,
            'total': total,
            'item_count': item_count, 
            'items': items,
            'destination': p.destination, 
        })

    context = {
        'login_user': login_user,
        'history': history,
    }
    return render(request, 'shopping/purchaseHistory.html', context)


def purchase_detail(request, purchase_id):
    """購入履歴詳細"""
    login_user = get_login_user(request)
    if not login_user:
        return redirect('/account/login/')

    purchase = get_object_or_404(Purchase, pk=purchase_id, user=login_user)
    details = PurchaseDetail.objects.filter(purchase=purchase).select_related('item')
    total = sum(d.item.price * d.amount for d in details)

    context = {
        'login_user': login_user,
        'purchase': purchase,
        'details': details,
        'total': total,
    }
    return render(request, 'shopping/purchaseHistoryDetail.html', context)



def get_login_user(request):
    if not request.session.get("is_login", None):
        return None
    user_id = request.session.get("user_id")
    return AccountUser.objects.get(pk=user_id)


def main(request):
    categories = Category.objects.all().order_by('category_id')
    context = {
        'categories': categories,
        'login_user': get_login_user(request),
    }
    return render(request, 'shopping/main.html', context)


def search_result(request):
    category_id = request.GET.get('category', '')
    keyword = request.GET.get('keyword', '')

    selected_category_obj = None
    items = Item.objects.all()
    if category_id:
        items = items.filter(category_id=category_id)
        selected_category_obj = Category.objects.get(pk=category_id)
    if keyword:
        items = items.filter(name__icontains=keyword)
    items = items.order_by('-recommended', 'item_id')

    context = {
        'selected_category_obj': selected_category_obj,
        'keyword': keyword,
        'items': items,
        'login_user': get_login_user(request),
    }
    return render(request, 'shopping/searchResult.html', context)


def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if item.stock > 0:
        max_qty = item.stock
    else:
        max_qty = 0
    quantity_range = range(1, max_qty + 1)

    context = {
        'item': item,
        'quantity_range': quantity_range,
        'login_user': get_login_user(request),
    }
    return render(request, 'shopping/itemDetail.html', context)


def add_to_cart(request, item_id):
    login_user = get_login_user(request)
    if not login_user:
        next_url = reverse('shopping:item_detail', args=[item_id])
        return redirect(f'/account/login/?next={next_url}')

    if request.method != 'POST':
        return redirect('shopping:item_detail', item_id=item_id)

    item = get_object_or_404(Item, pk=item_id)
    try:
        amount = int(request.POST.get('amount', 1))
    except ValueError:
        amount = 1
    if amount < 1:
        amount = 1


    new_cart_item = ItemsInCart()
    new_cart_item.user = login_user
    new_cart_item.item = item
    new_cart_item.amount = amount
    new_cart_item.save()

    return redirect('shopping:cart')


def cart(request):
    login_user = get_login_user(request)
    if not login_user:
        return redirect('/account/login/?next=' + reverse('shopping:cart'))

    cart_items = ItemsInCart.objects.filter(user=login_user).select_related('item').order_by('booked_date')

    total = sum(ci.item.price * ci.amount for ci in cart_items)

    context = {
        'cart_items': cart_items,
        'total': total,
        'login_user': login_user,
    }
    return render(request, 'shopping/cart.html', context)