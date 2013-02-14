from django import forms
from django.forms.models import inlineformset_factory

from orders.models import Product, Order, OrderItem


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['loru', ]

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ['loru', ]

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        exclude=['price']

OrderItemFormset = inlineformset_factory(Order, OrderItem, form=OrderItemForm)