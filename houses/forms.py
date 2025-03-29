from django import forms
from .models import House, HouseImage

class HouseForm(forms.ModelForm):
    images = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)

    class Meta:
        model = House
        fields = ['name', 'description', 'location', 'latitude', 'longitude', 'contact', 'rent', 'video']

    def save(self, commit=True):
        house = super().save(commit=False)
        if commit:
            house.save()
        return house
class HouseImageForm(forms.ModelForm):
    class Meta:
        model = HouseImage
        fields = ['image']
