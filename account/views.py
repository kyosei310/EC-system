from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from account import models
from account import forms


# Create your views here.

def login(request):
    if request.session.get("is_login", None):
        return redirect("/")
    if request.method == "POST":
        login_form = forms.LoginForm(request.POST)
        message = "入力した内容を再度確認してください"
        if login_form.is_valid():
            user_id = login_form.cleaned_data.get("user_id")
            password = login_form.cleaned_data.get("password")
            try:
                user = models.AccountUser.objects.get(user_id = user_id)
            except:
                message = "ユーザーが存在しません"
                return render(request, "account/login.html", locals())
            if user.password == password:
                request.session["is_login"] = True
                request.session["user_id"] = user.user_id
                return redirect("/")
            else:
                message = "パスワードが正しくありません。"
                return render(request, "account/login.html", locals())
        else:
            return render(request, "account/login.html", locals())
    login_form = forms.LoginForm()
    return render(request, "account/login.html", locals())

def logout(request):
    if not request.session.get("is_login", None):
        return redirect("/")
    request.session.flush()
    return redirect("/")

def register(request):
    if request.method == "GET":
        register_form = forms.RegisterForm()
        return render(request, "account/register.html", locals())
    if request.method == "POST":
        register_form = forms.RegisterForm(request.POST)
        
        if register_form.is_valid():
            user = models.AccountUser()
            user.user_id = register_form.cleaned_data["user_id"]
            user.password = register_form.cleaned_data["password"]            
            user.name = register_form.cleaned_data["name"]            
            user.address = register_form.cleaned_data["address"]            
            user.save()
            context = {
                "name": user.name
            }
            return render(request, "account/user_create_commit.html", context)
        else:
            return render(request, "account/register.html", locals())