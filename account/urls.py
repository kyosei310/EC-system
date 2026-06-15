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
]