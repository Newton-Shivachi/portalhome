from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import House, HouseImage, CustomUser
import re

# -------- HOUSE FORMS --------
class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ['name', 'description', 'location', 'latitude', 'longitude', 'contact', 'rent', 'video', 'is_taken']

class HouseImageForm(forms.ModelForm):
    image = forms.FileField(required=True)

    class Meta:
        model = HouseImage
        fields = ['image']

# -------- USER FORMS --------
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "can_post")  # can_post is optional if used

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        username = self.cleaned_data.get("username")

        if username and username.lower() in password.lower():
            raise ValidationError("Password should not contain your username.")

        if not re.search(r"\d", password):
            raise ValidationError("Password must contain at least one number.")

        if not re.search(r"[^\w\s]", password):  # checks for special characters
            raise ValidationError("Password must contain at least one special character (e.g., @, #, $, %, etc.).")

        return password

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "can_post")

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=100)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
