# coding=utf-8
from django import forms
from django.db.models.deletion import ProtectedError
from django.db.models.query_utils import Q
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext as _

from burials.models import Burial
from geo.forms import LocationForm
from orders.models import Product, Order, OrderItem, CatafalqueData, CoffinData
from burials.forms import OPF_CHOICES, EMPTY
from pd.forms import ChildrenJSONMixin
from persons.forms import AlivePersonForm, PersonIDForm
from persons.models import AlivePerson, PersonID


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['loru', ]

class OrderForm(ChildrenJSONMixin, forms.ModelForm):
    opf = forms.ChoiceField(label=_(u'ОПФ'), choices=OPF_CHOICES, widget=forms.RadioSelect, initial='person')

    class Meta:
        model = Order
        exclude = ['loru', 'person', 'org', ]

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder.insert(0, self.fields.keyOrder.pop(-1))

        if self.instance.applicant:
            self.initial['opf'] = 'person'
        else:
            self.initial['opf'] = 'org'

        self.fields['payment'].widget = forms.RadioSelect(choices=Order.PAYMENT_CHOICES)

        self.fields['agent'].queryset = self.fields['agent'].queryset.select_related('user')
        self.fields['dover'].queryset = self.fields['dover'].queryset.select_related('agent', 'agent__user')

        self.forms = self.construct_forms()

    def is_valid(self):
        return super(OrderForm, self).is_valid() and all([f.is_valid() for f in self.forms])

    def construct_forms(self):
        data = self.data or None
        applicant = self.instance and self.instance.applicant
        self.applicant_form = AlivePersonForm(data=data, prefix='applicant', instance=applicant)
        applicant_addr = applicant and applicant.address
        self.applicant_address_form = LocationForm(data=data, prefix='applicant-address', instance=applicant_addr)
        try:
            applicant_id = self.instance and self.instance.applicant and self.instance.applicant.personid
        except PersonID.DoesNotExist:
            applicant_id = None
        self.applicant_id_form = PersonIDForm(data=data, prefix='applicant-pid', instance=applicant_id)

        return [self.applicant_form, self.applicant_address_form, self.applicant_id_form]

    def save(self, commit=True, *args, **kwargs):
        self.instance = super(OrderForm, self).save(*args, **kwargs)

        if self.cleaned_data.get('opf') == 'person':
            if self.applicant_form.is_valid_data():
                applicant = self.applicant_form.save(commit=False)
                if self.applicant_address_form.is_valid_data():
                    applicant.address = self.applicant_address_form.save()
                applicant.save()

                if self.applicant_id_form.is_valid_data():
                    pid = self.applicant_id_form.save(commit=False)
                    pid.person = applicant
                    pid.save()
                self.instance.applicant = applicant
            else:
                self.instance.applicant = None

            self.instance.applicant_organization = None
        else:
            try:
                self.instance.applicant.delete()
            except (AttributeError, ProtectedError):
                pass
            self.instance.applicant = None

        self.instance.save()

        return self.instance

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        exclude=['price']

    def clean(self):
        p = self.cleaned_data['product']
        if p and p.ptype and p.ptype != Product.PRODUCT_CATAFALQUE:
            self.cleaned_data['quantity'] = 1
        return self.cleaned_data

class BaseOrderItemFormset(BaseInlineFormSet):
    def __init__(self, request, *args, **kwargs):
        super(BaseOrderItemFormset, self).__init__(*args, **kwargs)
        for f in self.forms:
            f.fields['product'].queryset = Product.objects.filter(loru=request.user.profile.org)

    def get_same_product(self, form):
        p = form.cleaned_data['product']

        q = Q(product=p)
        if p.ptype:
            q |= Q(product__ptype=p.ptype)
        same_product = OrderItem.objects.filter(q, order=self.instance)

        if same_product.exists():
            if p.ptype:
                if p.ptype == Product.PRODUCT_CATAFALQUE:
                    same_product.update(quantity=form.cleaned_data['quantity'])
                else:
                    same_product.update(quantity=1)
            try:
                return same_product[0]
            except IndexError:
                pass

    def save_existing(self, form, instance, commit=True):
        return self.get_same_product(form) or super(BaseOrderItemFormset, self).save_existing(form, instance, commit)
    
    def save_new(self, form, commit=True):
        return self.get_same_product(form) or super(BaseOrderItemFormset, self).save_new(form, commit)

OrderItemFormset = inlineformset_factory(Order, OrderItem, form=OrderItemForm, formset=BaseOrderItemFormset)

class CatafalqueForm(forms.ModelForm):
    class Meta:
        model = CatafalqueData

    def __init__(self, *args, **kwargs):
        super(CatafalqueForm, self).__init__(*args, **kwargs)
        self.fields['start_place'].widget = forms.TextInput()

class CoffinForm(forms.ModelForm):
    size = forms.CharField(label=_(u'Размер'))

    class Meta:
        model = CoffinData

class OrderSearchForm(forms.Form):
    """
    Форма поиска заказов
    """

    PAGE_CHOICES = (
        (10, 10),
        (25, 25),
        (50, 50),
        (100, 100),
    )

    fio = forms.CharField(required=False, max_length=100, label=_(u"ФИО"))
    no_last_name = forms.BooleanField(required=False, initial=False, label=_(u"Неизв."))
    birth_date_from = forms.DateField(required=False, label=_(u"Дата рожд. с"))
    birth_date_to = forms.DateField(required=False, label=_(u"по"))
    death_date_from = forms.DateField(required=False, label=_(u"Дата смерти с"))
    death_date_to = forms.DateField(required=False, label=_(u"по"))
    burial_date_from = forms.DateField(required=False, label=_(u"Дата захор. с"))
    burial_date_to = forms.DateField(required=False, label=_(u"по"))
    account_number_from = forms.IntegerField(required=False, label=_(u"Уч. номер с"))
    account_number_to = forms.IntegerField(required=False, label=_(u"по"))
    applicant_org = forms.CharField(required=False, max_length=30, label=_(u"Заявитель-ЮЛ"))
    applicant_person = forms.CharField(required=False, max_length=30, label=_(u"Заявитель-ФЛ"))
    responsible = forms.CharField(required=False, max_length=30, label=_(u"Ответственный"))
    cemetery = forms.CharField(required=False, label=_(u"Кладбища"))
    area = forms.CharField(required=False, label=_(u"Участок"))
    row = forms.CharField(required=False, label=_(u"Ряд"))
    place = forms.CharField(required=False, label=_(u"Место"))
    no_responsible = forms.BooleanField(required=False, initial=False, label=_(u"Без отв."))
    status = forms.TypedChoiceField(required=False, label=_(u"Статус"), choices=EMPTY + Burial.STATUS_CHOICES)
    annulated = forms.BooleanField(required=False, initial=False, label=_(u"Аннулированы"))
    order_num_from = forms.IntegerField(required=False, label=_(u"Номер с"))
    order_num_to = forms.IntegerField(required=False, label=_(u"по"))
    order_cost_from = forms.IntegerField(required=False, label=_(u"Стоимость с"))
    order_cost_to = forms.IntegerField(required=False, label=_(u"по"))
    per_page = forms.ChoiceField(label=_(u"На странице"), choices=PAGE_CHOICES, initial=25, required=False)

