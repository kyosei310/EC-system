from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import View
from account import models
from account import forms


def get_login_user(request):
    if not request.session.get("is_login", None):
        return None
    user_id = request.session.get("user_id")
    return models.AccountUser.objects.get(pk=user_id)


def login(request):
    if request.session.get("is_login", None):
        return redirect("/shopping/")
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
                return redirect("/shopping/")
            else:
                message = "パスワードが正しくありません。"
                return render(request, "account/login.html", locals())
        else:
            return render(request, "account/login.html", locals())
    login_form = forms.LoginForm()
    return render(request, "account/login.html", locals())

def logout(request):
    if not request.session.get("is_login", None):
        return redirect("/shopping/")
    request.session.flush()
    return redirect("/shopping/")

def register(request):
    if request.method == "GET":
        register_form = forms.RegisterForm()
        return render(request, "account/registerUser.html", locals())
    if request.method == "POST":
        register_form = forms.RegisterForm(request.POST)
        
        if register_form.is_valid():
            masked_password = '●' * len(register_form.cleaned_data['password'])
            context = {
                "register_form": register_form.cleaned_data,
                "masked_password": masked_password
            }
            return render(request, "account/registerUserConfirm.html", context)
        else:
            return render(request, "account/registerUser.html", locals())



def register_commit(request):
    if request.method == "GET":
        register_form = forms.RegisterForm()
        return render(request, "account/registerUser.html", locals())
    if request.method == "POST":
        register_form = forms.RegisterConfirmForm(request.POST)
        
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
            return render(request, "account/registerUserCommit.html", context)
        else:
            return render(request, "account/registerUser.html", locals())


def user_info(request):
    user = get_login_user(request)
    if not user:
        return redirect("/account/login/")
    return render(request, "account/UserInfo.html", {"user": user})


def update_user(request):
    user = get_login_user(request)
    if not user:
        return redirect("/account/login/")

    if request.method == "POST":
        update_form = forms.RegisterForm(request.POST)
        if update_form.is_valid():
            request.session["update_password"] = update_form.cleaned_data.get("password")
            masked_password = "*" * len(update_form.cleaned_data.get("password"))
            context = {
                "update_form": update_form.cleaned_data,
                "masked_password": masked_password,
            }
            return render(request, "account/updateUserConfirm.html", context)
        message = "入力した内容を再度確認してください"
        return render(request, "account/updateUser.html", locals())

    update_form = forms.RegisterForm(initial={
        "user_id": user.user_id,
        "name": user.name,
        "address": user.address,
    })
    return render(request, "account/updateUser.html", {"update_form": update_form})


def update_user_commit(request):
    user = get_login_user(request)
    if not user:
        return redirect("/account/login/")

    if request.method != "POST":
        return redirect("/account/updateUser/")

    user.name = request.POST.get("name", user.name)
    user.address = request.POST.get("address", user.address)
    user.password = request.session["update_password"]
    user.save()

    return render(request, "account/updateUserCommit.html", {"user": user})


def withdraw_confirm(request):
    user = get_login_user(request)
    if not user:
        return redirect("/account/login/")

    return render(request, "account/withdrawConfirm.html", {"user": user})






def withdraw_commit(request):
    user = get_login_user(request)
    if not user:
        return redirect("/account/login/")
    
    name = user.name
    user.delete()
    request.session.flush()  # セッションを全クリア

    return render(request, "account/withdrawCommit.html", {"name": name})