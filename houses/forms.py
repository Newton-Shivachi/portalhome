from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import House, HouseImage, CustomUser

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

# -------- USER FORMS (Because you're using CustomUser) --------
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "can_post")  # You can remove can_post if not needed during registration

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "can_post")

# Optional login form using CustomUser
class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=100)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
