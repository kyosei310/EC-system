from django.urls import path
from . import views

app_name = "account"

urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("register/", views.register, name="register"),
    path("registerCommit/", views.register_commit, name="register_commit"),
    path("userInfo/", views.user_info, name="user_info"),
    path("updateUser/", views.update_user, name="update_user"),
    path("updateUserCommit/", views.update_user_commit, name="update_user_commit"),
    path("withdrawConfirm/", views.withdraw_confirm, name="withdraw_confirm"),
    path("withdrawCommit/", views.withdraw_commit, name="withdraw_commit"),
    # 管理者用URL
    path("adminLogin/", views.admin_login, name="admin_login"),
    path("adminMain/", views.admin_main, name="admin_main"),
    path("adminLogout/", views.admin_logout, name="admin_logout"),
    path("adminItems/", views.admin_items, name="admin_items"),
    path("adminItemAdd/", views.admin_item_add, name="admin_item_add"),
    path("adminItemEdit/<int:item_id>/", views.admin_item_edit, name="admin_item_edit"),
    path("adminItemDelete/<int:item_id>/", views.admin_item_delete, name="admin_item_delete"),
    path("adminPurchaseHistory/", views.admin_purchase_history, name="admin_purchase_history"),
    path("adminCancelPurchase/<int:purchase_id>/", views.admin_cancel_purchase, name="admin_cancel_purchase"),
]