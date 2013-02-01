from django import forms

from geo.models import Location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location

