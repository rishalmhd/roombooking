from django import forms
from customer_app.models import User

class ManagerRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["first_name", "username", "email", "mobile", "password"]

    def clean(self):
        cleaned = super().clean()
        if cleaned["password"] != cleaned["confirm_password"]:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned
