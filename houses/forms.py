from django import forms
from .models import House, HouseImage

class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ['name', 'description', 'location', 'latitude', 'longitude', 'contact', 'is_taken', 'video']

class HouseImageForm(forms.ModelForm):
    class Meta:
        model = HouseImage
        fields = ['image']
