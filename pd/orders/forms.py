# coding=utf-8
from django import forms
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext as _

from orders.models import Product, Order, OrderItem, CatafalqueData, CoffinData
from burials.forms import OPF_CHOICES
from persons.models import AlivePerson


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['loru', ]

class OrderForm(forms.ModelForm):
    opf = forms.ChoiceField(label=_(u'ОПФ'), choices=OPF_CHOICES, widget=forms.RadioSelect, initial='person')

    person_last_name = forms.CharField(label=_(u"Фамилия"), required=False)
    person_first_name = forms.CharField(label=_(u"Имя"), required=False)
    person_middle_name = forms.CharField(label=_(u"Отчество"), required=False)

    class Meta:
        model = Order
        exclude = ['loru', 'person' ]

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder.insert(0, self.fields.keyOrder.pop(-4))

        if self.instance.person:
            self.initial['person_last_name'] = self.instance.person.last_name or u""
            self.initial['person_first_name'] = self.instance.person.first_name or u""
            self.initial['person_middle_name'] = self.instance.person.middle_name or u""

        if self.data and self.data.get('opf') == 'person':
            self.fields['person_last_name'].required = True
            self.fields['person_first_name'].required = True
            self.fields['person_middle_name'].required = True

    def save(self, commit=True, *args, **kwargs):
        self.instance = super(OrderForm, self).save(*args, **kwargs)

        if self.cleaned_data['opf'] == 'person':
            person = self.instance.person or AlivePerson()

            person.last_name = self.cleaned_data['person_last_name']
            person.first_name = self.cleaned_data['person_first_name']
            person.middle_name = self.cleaned_data['person_middle_name']
            person.save()

            self.instance.person = person
            self.instance.org = None
        else:
            self.instance.person = None
        self.instance.save()

        return self.instance

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        exclude=['price']

    def clean(self):
        p = self.cleaned_data['product']
        if p and p.ptype:
            self.cleaned_data['quantity'] = 1
        return self.cleaned_data

    def save(self, commit=True, *args, **kwargs):
        if self.is_valid():
            p = self.cleaned_data['product']

            q = Q(product=p)
            if p.ptype:
                q |= Q(product__ptype=p.ptype)
            same_product = OrderItem.objects.filter(q)

            if p.ptype:
                same_product.update(quantity=1)
            try:
                return same_product[0]
            except IndexError:
                pass

            return super(OrderItemForm, self).save(commit=commit, *args, **kwargs)

class BaseOrderItemFormset(BaseInlineFormSet):
    def __init__(self, request, *args, **kwargs):
        super(BaseOrderItemFormset, self).__init__(*args, **kwargs)
        for f in self.forms:
            f.fields['product'].queryset = Product.objects.filter(loru=request.user.profile.org)

OrderItemFormset = inlineformset_factory(Order, OrderItem, form=OrderItemForm, formset=BaseOrderItemFormset)

class CatafalqueForm(forms.ModelForm):
    class Meta:
        model = CatafalqueData

class CoffinForm(forms.ModelForm):
    class Meta:
        model = CoffinData