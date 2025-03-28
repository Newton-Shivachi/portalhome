from django import forms
from .models import House, HouseImage

class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ['name', 'description', 'location', 'latitude', 'longitude', 'contact', 'rent', 'video']

class HouseImageForm(forms.ModelForm):
    image = forms.FileField(required=True)

    class Meta:
        model = HouseImage
        fields = ['image']
