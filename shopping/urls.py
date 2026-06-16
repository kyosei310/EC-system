from django.urls import path
from . import views

app_name = 'shopping'

urlpatterns = [
    path('', views.main, name='main'),
    path('search/', views.search_result, name='search_result'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('item/<int:item_id>/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),

    # ▼ カート編集
    path('cart/update/<int:cart_id>/', views.update_cart, name='update_cart'),
    path('cart/delete/<int:cart_id>/', views.delete_cart, name='delete_cart'),

    # ▼ 購入処理（3段階：宛先入力 → 確認 → 完了）
    path('purchase/', views.purchase, name='purchase'),
    path('purchaseConfirm/', views.purchase_confirm, name='purchase_confirm'),
    path('purchaseCommit/', views.purchase_commit, name='purchase_commit'),

    # ▼ 購入履歴
    path('purchaseHistory/', views.purchase_history, name='purchase_history'),
]