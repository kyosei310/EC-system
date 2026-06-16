from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from .models import Category, Item, ItemsInCart, Purchase, PurchaseDetail
from account.models import AccountUser


# ====================================================================
# カート編集機能
# ====================================================================

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

        # 在庫超過チェック
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


# ====================================================================
# 購入機能（3段階：入力 → 確認 → 完了）
# ====================================================================

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
        # デフォルトは会員登録住所
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

    # 配送先選択
    destination_type = request.POST.get('destination_type', 'registered')
    if destination_type == 'other':
        destination = request.POST.get('other_address', '').strip()
    else:
        destination = login_user.address

    # 配送先が空ならエラーで戻す
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

    # セッションに退避（PRGパターン）
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

    # ===== 在庫チェック（再確認） =====
    for ci in cart_items:
        if ci.amount > ci.item.stock:
            request.session['purchase_destination'] = destination  # 戻す
            return render(request, 'shopping/purchase.html', {
                'login_user': login_user,
                'cart_items': cart_items,
                'total': sum(c.item.price * c.amount for c in cart_items),
                'default_address': login_user.address,
                'message': f'「{ci.item.name}」の在庫が不足しています。',
            })

    # ===== 注文ID採番（アプリ側採番のため max+1） =====
    last_purchase = Purchase.objects.order_by('-purchase_id').first()
    new_purchase_id = (last_purchase.purchase_id + 1) if last_purchase else 1

    # ===== Purchase 作成 =====
    purchase = Purchase()
    purchase.purchase_id = new_purchase_id
    purchase.destination = destination
    purchase.cancel = False
    purchase.user = login_user
    purchase.save()

    # ===== PurchaseDetail 採番開始値 =====
    last_detail = PurchaseDetail.objects.order_by('-purchase_detail_id').first()
    next_detail_id = (last_detail.purchase_detail_id + 1) if last_detail else 1

    # ===== PurchaseDetail 作成 ＆ 在庫減算 =====
    for ci in cart_items:
        detail = PurchaseDetail()
        detail.purchase_detail_id = next_detail_id
        detail.amount = ci.amount
        detail.item = ci.item
        detail.purchase = purchase
        detail.save()
        next_detail_id += 1

        # 在庫減算
        ci.item.stock -= ci.amount
        ci.item.save()

    # ===== カートクリア =====
    ItemsInCart.objects.filter(user=login_user).delete()

    context = {
        'login_user': login_user,
        'purchase': purchase,
    }
    return render(request, 'shopping/purchaseCommit.html', context)


# ====================================================================
# 購入履歴
# ====================================================================
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

    # 各注文の合計金額、商品詳細、商品点数を計算
    history = []
    for p in purchases:
        details = PurchaseDetail.objects.filter(purchase=p).select_related('item')
        total = sum(d.item.price * d.amount for d in details)
        item_count = sum(d.amount for d in details)  # 商品点数を修正
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
            'item_count': item_count,  # 修正した商品点数
            'items': items,
            'destination': p.destination,  # 配送先を追加
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