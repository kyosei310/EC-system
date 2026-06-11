from django import forms
from account.models import AccountUser

class LoginForm(forms.Form):
    user_id = forms.CharField(label= "会員ID", max_length=128)
    password = forms.CharField(label="パスワード", max_length=256, widget=forms.PasswordInput(render_value=False))

    
class RegisterForm(forms.Form):
    user_id = forms.CharField(label= "会員ID", max_length=128)
    password = forms.CharField(label="パスワード", max_length=256, widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label="パスワード(確認)", max_length=256, widget=forms.PasswordInput(render_value=False))
    name = forms.CharField(label= "ユーザー名", max_length=128)
    address = forms.CharField(label= "住所", max_length=256)
    
    
    def clean(self):
        cleaned_data = super().clean()
        
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password != confirm_password:
            raise forms.ValidationError("パスワードが一致しません")
        
        return cleaned_data