from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Category, Item, ItemsInCart
from account.models import AccountUser


def get_login_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    return AccountUser.objects.filter(pk=user_id).first()


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
        selected_category_obj = Category.objects.filter(pk=category_id)
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
        # 未ログイン → ログイン画面へ（ログイン後に元の商品詳細へ戻れるようnextを付与する）
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

    # 同一ユーザー・同一商品が既にカートにある場合は数量を加算
    cart_item = ItemsInCart.objects.filter(user=login_user, item=item).first()
    if cart_item:
        cart_item.amount += amount
        cart_item.save()
    else:
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