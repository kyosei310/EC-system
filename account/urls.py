from django.urls import path
from . import views

app_name = "account"

urlpatterns = [
    #path("/", views.),
    path("login/", views.login),
    path("logout/", views.logout),
    path("register/", views.register)
]