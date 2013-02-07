from django import forms

from geo.models import Location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        self.fields['city'].widget = forms.TextInput()
        self.fields['street'].widget = forms.TextInput()

