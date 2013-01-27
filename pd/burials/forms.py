from django import forms

from burials.models import BurialRequest


class BurialRequestCreateForm(forms.ModelForm):
    class Meta:
        model = BurialRequest
        exclude = ['number']