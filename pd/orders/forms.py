# coding=utf-8

from django import forms
from django.utils.translation import ugettext_lazy as _

from orders.models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order

    def clean(self):
        if not self.cleaned_data.get('client_org') and not self.cleaned_data.get('client_person'):
            raise forms.ValidationError(_(u'Нужно указать клиента'))
        return self.cleaned_data