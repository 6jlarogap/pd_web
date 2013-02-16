# coding=utf-8
from django import forms
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext as _

from orders.models import Product, Order, OrderItem
from burials.forms import OPF_CHOICES


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['loru', ]

class OrderForm(forms.ModelForm):
    opf = forms.ChoiceField(label=_(u'ОПФ'), choices=OPF_CHOICES, widget=forms.RadioSelect, initial='person')

    class Meta:
        model = Order
        exclude = ['loru', ]

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder.insert(0, self.fields.keyOrder.pop(-1))

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        exclude=['price']

OrderItemFormset = inlineformset_factory(Order, OrderItem, form=OrderItemForm)