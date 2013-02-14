from django import forms

from orders.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['loru', ]