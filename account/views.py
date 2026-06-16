from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import View
from account import models
from account import forms
from django.contrib.auth.hashers import check_password
from shopping.models import Item, Purchase, PurchaseDetail, Category


def admin_login(request):
    if request.method == "POST":
        admin_id = request.POST.get("admin_id")
        password = request.POST.get("password")
        try:
            admin = models.Admin.objects.get(admin_id=admin_id)
            if check_password(password, admin.password):
                request.session["is_admin"] = True
                request.session["admin_id"] = admin.admin_id
                return redirect("account:admin_main")
            else:
                message = "パスワードが正しくありません。"
        except models.Admin.DoesNotExist:
            message = "管理者が存在しません。"
        return render(request, "account/adminLogin.html", {"message": message})
    return render(request, "account/adminLogin.html")


def admin_logout(request):
    request.session.flush()
    return redirect("account:admin_login")


def admin_main(request):
    if not request.session.get("is_admin"):
        return redirect("account:admin_login")
    return render(request, "account/adminMain.html")


def admin_items(request):
    if not request.session.get("is_admin"):
        return redirect("account:admin_login")
    items = Item.objects.all()
    return render(request, "account/adminItems.html", {"items": items})


def admin_item_add(request):
    if not request.session.get("is_admin"):
        return redirect("account:admin_login")
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        name = request.POST.get("name")
        manufacturer = request.POST.get("manufacturer")
        color = request.POST.get("color")
        price = int(request.POST.get("price"))
        stock = int(request.POST.get("stock"))
        recommended = request.POST.get("recommended") == "on"
        category_id = request.POST.get("category_id")
        category = Category.objects.get(pk=category_id)
        
        
        errors = []
        if Item.objects.filter(pk=item_id).exists():
            errors.append(f"商品ID「{item_id}」は既に登録されています。別のIDを入力してください。")
            
        if errors:
            categories = Category.objects.all()
            form_data = {
                "item_id": item_id,
                "name": name,
                "manufacturer": manufacturer,
                "color": color,
                "price": price,
                "stock": stock,
                "recommended": recommended,
                "category_id": category_id,
            }

            return render(request, "account/adminItemAdd.html", {
                "categories": categories,
                "errors": errors,
                "form_data": form_data,
            })


        
        Item.objects.create(
            item_id=item_id,
            name=name,
            manufacturer=manufacturer,
            color=color,
            price=price,
            stock=stock,
            recommended=recommended,
            category=category,
        )
        return redirect("account:admin_items")
    categories = Category.objects.all()
    return render(request, "account/adminItemAdd.html", {"categories": categories})


def admin_item_edit(request, item_id):
    if not request.session.get("is_admin"):
        return redirect("account:admin_login")
    item = get_object_or_404(Item, pk=item_id)
    if request.method == "POST":
        item.name = request.POST.get("name")
        item.manufacturer = request.POST.get("manufacturer")
        item.color = request.POST.get("color")
        item.price = int(request.POST.get("price"))
        item.stock = int(request.POST.get("stock"))
        item.recommended = request.POST.get("recommended") == "on"
        item.category = Category.objects.get(pk=request.POST.get("category_id"))
        item.save()
        return redirect("account:admin_items")
    categories = Category.objects.all()
    return render(request, "account/adminItemEdit.html", {"item": item, "categories": categories})


def admin_item_delete(request, item_id):
    if not request.session.get("is_admin"):
        return redirect("account:admin_login")
    item = get_object_or_404(Item, pk=item_id)
    item.delete()
    return redirect("account:admin_items")


def admin_purchase_history(request):
    if not request.session.get("is_admin"):
        return redirect("account:admin_login")
    purchases = Purchase.objects.all().order_by("-booked_date")
    return render(request, "account/adminPurchaseHistory.html", {"purchases": purchases})


def admin_cancel_purchase(request, purchase_id):
    if not request.session.get("is_admin"):
        return redirect("account:admin_login")
    purchase = get_object_or_404(Purchase, pk=purchase_id)
    purchase.cancel = True
    purchase.save()
    return redirect("account:admin_purchase_history")


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
    request.session.flush() 

    return render(request, "account/withdrawCommit.html", {"name": name})