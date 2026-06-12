from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Category, Item, ItemsInCart
from account.models import AccountUser


def _get_login_user(request):
    """セッションからログイン中ユーザーを取得（未ログインならNone）"""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    return AccountUser.objects.filter(pk=user_id).first()


# ===== 商品検索画面（main.html） =====
def main(request):
    categories = Category.objects.all().order_by('category_id')
    context = {
        'categories': categories,
        'login_user': _get_login_user(request),
    }
    return render(request, 'shopping/main.html', context)


# ===== 検索結果画面（searchResult.html） =====
def search_result(request):
    categories = Category.objects.all().order_by('category_id')

    category_id = request.GET.get('category', '')
    keyword = request.GET.get('keyword', '').strip()

    selected_category_obj = None
    items = Item.objects.all()
    if category_id:
        items = items.filter(category_id=category_id)
        selected_category_obj = Category.objects.filter(pk=category_id).first()
    if keyword:
        items = items.filter(name__icontains=keyword)
    items = items.order_by('-recommended', 'item_id')

    context = {
        'categories': categories,
        'selected_category': category_id,
        'selected_category_obj': selected_category_obj,
        'keyword': keyword,
        'items': items,
        'login_user': _get_login_user(request),
    }
    return render(request, 'shopping/searchResult.html', context)


# ===== 商品詳細画面（itemDetail.html） =====
def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # 数量プルダウン用：在庫数 or 最大10個まで
    max_qty = min(item.stock, 10) if item.stock > 0 else 0
    quantity_range = range(1, max_qty + 1)

    context = {
        'item': item,
        'quantity_range': quantity_range,
        'login_user': _get_login_user(request),
    }
    return render(request, 'shopping/itemDetail.html', context)


# ===== カートへ追加 =====
def add_to_cart(request, item_id):
    login_user = _get_login_user(request)
    if not login_user:
        # 未ログイン → ログイン画面へ（ログイン後に元の商品詳細へ戻れるようnext付与）
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
        ItemsInCart.objects.create(user=login_user, item=item, amount=amount)

    return redirect('shopping:cart')


# ===== ショッピングカート画面（cart.html） =====
def cart(request):
    login_user = _get_login_user(request)
    if not login_user:
        return redirect('/account/login/?next=' + reverse('shopping:cart'))

    cart_items = (
        ItemsInCart.objects
        .filter(user=login_user)
        .select_related('item')
        .order_by('booked_date')
    )

    total = sum(ci.item.price * ci.amount for ci in cart_items)

    context = {
        'cart_items': cart_items,
        'total': total,
        'login_user': login_user,
    }
    return render(request, 'shopping/cart.html', context)