from django import forms
from django.utils.translation import gettext_lazy as _


class ImportCsvMinskForm(forms.Form):
    cemetery = forms.CharField(label=_("Кладбище"), required=True)
    csv = forms.FileField(label=_("Файл CSV"), required=True)
