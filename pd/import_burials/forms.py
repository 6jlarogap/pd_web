# coding=utf-8
from django import forms
from django.utils.translation import ugettext_lazy as _


class ImportCsvForm(forms.Form):
    csv = forms.FileField(label=_("Файл CSV"))

class ImportCsvMinskForm(forms.Form):
    cemetery = forms.CharField(label=_("Кладбище"), required=True)
    csv = forms.FileField(label=_("Файл CSV"), required=True)
