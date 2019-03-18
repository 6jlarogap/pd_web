# coding=utf-8
import datetime

from django import forms
from django.db.models.deletion import ProtectedError
from django.db.models.query_utils import Q
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext as _

from burials.models import Burial
from geo.forms import LocationForm
from orders.models import Product, Order, OrderItem, CatafalqueData, CoffinData, AddInfoData, ProductCategory
from burials.forms import EMPTY
from pd.forms import ChildrenJSONMixin, StrippedStringsMixin
from persons.forms import AlivePersonForm, PersonIDForm
from persons.models import AlivePerson, PersonID
from users.models import Org, Profile
from pd.models import SafeDeleteMixin
from pd.forms import AppOrgFormMixin, CustomClearableFileInput
from pd.utils import reorder_form_fields

class ProductForm(StrippedStringsMixin, forms.ModelForm):

    NAME_POPUP = """
    <br />Длина названия ограничена %d символами.
    <br />
    <br />Пожалуйста, не применяйте в названии СЛОВА ИЗ ПРОПИСНЫХ БУКВ без необходимости.
    <br />
    """ % Product.PRODUCT_NAME_MAXLEN
    NAME_TITLE = ""

    DESCRIPTION_POPUP = """
    <br />Для поднятия товаров в результатах поисковых систем рекомендуется при написании ОПИСАНИЯ
    Памятников, по мере необходимости, использовать (но не переусердствовать) следующие слова:
    <br />
    <br />.. купить
    <br />.. изготовление
    <br />.. произвести
    <br />.. заказать
    <br />.. приобрести
    <br />.. установка
    <br />.. предложения
    <br />.. ремонт
    <br />.. примеры
    <br />.. перечислить материалы (гранит)
    <br />.. восстановление
    <br />.. доставка (если есть)
    <br />
    <br />Для оптовиков:
    <br />
    <br />.. оптовая торговля
    <br />.. купить оптом
    <br />.. поставщики
    <br />.. производители
    <br />
    <br />Допускается использование слов в виде разных частей речи - восстановить, восстановление,...
    <br />
    <br />Составляйте уникальные описания - копирование текста определяется поисковыми системами и отбрасываются
    <br />
    """
    DESCRIPTION_TITLE = ""

    class Meta:
        model = Product
        exclude = ('loru', )
        widgets = {
            'photo': CustomClearableFileInput,
        }

    def __init__(self, request, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs = dict(
            maxlength=Product.PRODUCT_NAME_MAXLEN,
            size=Product.PRODUCT_NAME_MAXLEN,
        )
        self.NAME_TITLE = self.NAME_POPUP.replace('\n', '').replace('<br />','\n').strip()
        self.DESCRIPTION_TITLE = self.DESCRIPTION_POPUP.replace('\n', '').replace('<br />','\n').strip()
        self.fields['description'].required = True
        if not self.instance or not self.instance.pk:
            try:
                category_default = ProductCategory.objects.get(
                    name=_('Прочие товары и услуги'),
                )
                self.initial.update({'productcategory': category_default})
            except ProductCategory.DoesNotExist:
                pass

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description or not description.strip():
            raise forms.ValidationError(_('Обязательное поле'))
        return description

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) > Product.PRODUCT_NAME_MAXLEN:
            raise forms.ValidationError(_('Не больше %d символов') % Product.PRODUCT_NAME_MAXLEN)
        return name

class OrderForm(ChildrenJSONMixin, SafeDeleteMixin, AppOrgFormMixin, forms.ModelForm):

    class Meta:
        model = Order
        exclude = ['loru', 'applicant', ]

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(OrderForm, self).__init__(*args, **kwargs)
        self.init_app_org_label()
        reorder_form_fields(self.fields, old_pos=-1, new_pos=0)

        remove_opf_empty = request.user.profile.org.opf_order_customer_mandatory
        if self.instance.pk:
            if self.instance.applicant:
                opf_initial = Org.OPF_PERSON
            elif self.instance.applicant_organization:
                opf_initial = Org.OPF_ORG
            else:
                opf_initial = Org.OPF_EMPTY
                remove_opf_empty = False
        else:
            if request.user.profile.org.opf_order_customer_mandatory:
                opf_initial = request.user.profile.org.opf_order
            else:
                opf_initial = Org.OPF_EMPTY
            self.initial.update({'dt': datetime.date.today()})
            
        choices=list(Org.OPF_CHOICES)
        if remove_opf_empty:
            for i, choice in enumerate(choices):
                if choice[0] == Org.OPF_EMPTY:
                    choices.pop(i)
                    break
        self.fields['opf'] = forms.ChoiceField(label='', widget=forms.RadioSelect,
                                               choices=choices, initial = opf_initial)

        self.fields['payment'].widget = forms.RadioSelect(choices=Order.PAYMENT_CHOICES)

        self.fields['applicant_organization'].queryset = Org.objects.all()
        self.fields['applicant_organization'].inactive_queryset = \
            Org.objects.filter(Q(profile=None) | ~Q(profile__user__is_active=True)).distinct()
        self.fields['agent'].queryset = Profile.objects.filter(is_agent=True).select_related('user')
        self.fields['dover'].queryset = self.fields['dover'].queryset.select_related('agent', 'agent__user')

        # Отсутствие выбора будет в выпадающем списке не "---", а ""
        self.fields['applicant_organization'].empty_label = ''
        
        self.forms = self.construct_forms()

    def is_valid(self):
        return self.opf_valid(OrderForm)

    def clean(self):
        if self.cleaned_data.get('opf') == Org.OPF_ORG:
            if not (self.cleaned_data.get('agent_director') or \
                    self.cleaned_data.get('agent') and self.cleaned_data.get('dover')
                   ):
                raise forms.ValidationError(_('Нет данных об агенте и/или доверенности для заявителя-ЮЛ. Изменения не сохранены'))
            dover = self.cleaned_data.get('dover')
            if dover and not dover.begin <= self.cleaned_data.get('dt') <= dover.end:
                    raise forms.ValidationError(_('Дата заказа не соответствует сроку действия доверенности. Изменения не сохранены'))
        elif self.cleaned_data.get('opf') == Org.OPF_PERSON:
            if not self.applicant_form.is_valid_data():
                raise forms.ValidationError(_("Нужно указать Заявителя-ФЛ"))
        return self.cleaned_data
            
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
        self.instance = super(OrderForm, self).save(commit=False)
        
        if self.cleaned_data.get('opf') == Org.OPF_PERSON:
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
        elif self.cleaned_data.get('opf') == Org.OPF_ORG:
            self.safe_delete('applicant', self.instance)
            if self.cleaned_data.get('agent_director'):
                self.instance.agent = None
                self.instance.dover = None
        elif self.cleaned_data.get('opf') == Org.OPF_EMPTY:
            self.safe_delete('applicant', self.instance)
            self.instance.applicant_organization = None
            self.instance.agent_director = False
            self.instance.agent = None
            self.instance.dover = None

        self.instance.save()

        return self.instance

class OrderServicesForm(forms.Form):
    do_photo = forms.BooleanField(
        required=False,
        label=_("Фотографирование"),
    )
    price_photo = forms.CharField(required=False, widget=forms.HiddenInput)

class OrderItemForm(forms.ModelForm):

    class Meta:
        model = OrderItem
        fields = ('product', 'cost', 'quantity',)
        
    def __init__(self, *args, **kwargs):
        super(OrderItemForm, self).__init__(*args, **kwargs)
        self.instance_ = kwargs.get('instance')
        self.fields['cost'].required = False

    #def clean(self):
        #p = self.cleaned_data['product']
        #if p and p.ptype and p.ptype != Product.PRODUCT_CATAFALQUE:
            #self.cleaned_data['quantity'] = 1
        #return self.cleaned_data
        
    def clean(self):
        for f in self.formset:
            if (f is not self) and f['product'].value() == self['product'].value():
                raise forms.ValidationError(_('Нельзя добавить два или более одинаковых товаров/услуг'))
        return self.cleaned_data

class BaseOrderItemFormset(BaseInlineFormSet):

    def __init__(self, request, *args, **kwargs):
        super(BaseOrderItemFormset, self).__init__(*args, **kwargs)
        q_loru = Q(loru=request.user.profile.org)
        q_actual = Q(is_archived=False)
        for f in self.forms:
            if request.method == 'GET':
                if hasattr(f, 'instance_') and f.instance_ and f.instance_.pk and f.instance_.product.is_archived:
                    # Если попался архивный товар в заказе, показать его
                    q = Q(pk=f.instance_.product.pk) | q_loru & q_actual
                else:
                    q = q_loru & q_actual
            else:
                # в POST не передается instance. Чтоб можно было сохранить
                # архивный продукт в заказе:
                q = q_loru
            f.fields['product'].queryset = Product.objects.filter(q)
            f.formset = self

    #def get_same_product(self, form):
        #p = form.cleaned_data['product']

        #q = Q(product=p)
        #if p.ptype:
            #q |= Q(product__ptype=p.ptype)
        #same_product = OrderItem.objects.filter(q, order=self.instance)

        #if same_product.exists():
            #if p.ptype:
                #if p.ptype == Product.PRODUCT_CATAFALQUE:
                    #same_product.update(quantity=form.cleaned_data['quantity'])
                #else:
                    #same_product.update(quantity=1)
            #try:
                #return same_product[0]
            #except IndexError:
                #pass

    #def save_existing(self, form, instance, commit=True):
        #return self.get_same_product(form) or super(BaseOrderItemFormset, self).save_existing(form, instance, commit)
    
    #def save_new(self, form, commit=True):
        #return self.get_same_product(form) or super(BaseOrderItemFormset, self).save_new(form, commit)

OrderItemFormset = inlineformset_factory(Order, OrderItem, form=OrderItemForm, formset=BaseOrderItemFormset, extra=1)

class CatafalqueForm(forms.ModelForm):
    class Meta:
        model = CatafalqueData
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CatafalqueForm, self).__init__(*args, **kwargs)
        self.fields['start_place'].widget = forms.TextInput()

class AddInfoForm(forms.ModelForm):
    class Meta:
        model = AddInfoData
        fields = '__all__'

class CoffinForm(forms.ModelForm):
    size = forms.CharField(label=_('Размер'))

    class Meta:
        model = CoffinData
        fields = '__all__'

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

    fio_order_deadman = forms.CharField(required=False, max_length=100, label=_("ФИО усопшего"))
    no_last_name = forms.BooleanField(required=False, initial=False, label=_("Неизв."))
    birth_date_from = forms.DateField(required=False, label=_("Дата рожд. с"))
    birth_date_to = forms.DateField(required=False, label=_("по"))
    death_date_from = forms.DateField(required=False, label=_("Дата смерти с"))
    death_date_to = forms.DateField(required=False, label=_("по"))
    burial_date_from = forms.DateField(required=False, label=_("Дата захор. с"))
    burial_date_to = forms.DateField(required=False, label=_("по"))
    account_number_from = forms.IntegerField(required=False, label=_("Номер Заказа с"))
    account_number_to = forms.IntegerField(required=False, label=_("по"))
    applicant_org = forms.CharField(required=False, max_length=60, label=_("Заказчик-ЮЛ"))
    applicant_person = forms.CharField(required=False, max_length=40, label=_("Заказчик-ФЛ"))
    responsible = forms.CharField(required=False, max_length=40, label=_("Ответственный"))
    cemetery = forms.CharField(required=False, label=_("Кладбища"))
    area = forms.CharField(required=False, label=_("Участок"))
    row = forms.CharField(required=False, label=_("Ряд"))
    place = forms.CharField(required=False, label=_("Место"))
    no_responsible = forms.BooleanField(required=False, initial=False, label=_("Без отв."))
    status = forms.TypedChoiceField(required=False, label=_("Статус"), choices=EMPTY + Burial.STATUS_CHOICES)
    annulated = forms.BooleanField(required=False, initial=False, label=_("Аннулированы"))
    order_num_from = forms.IntegerField(required=False, label=_("Номер Заказа с"))
    order_num_to = forms.IntegerField(required=False, label=_("по"))
    order_cost_from = forms.IntegerField(required=False, label=_("Стоимость с"))
    order_cost_to = forms.IntegerField(required=False, label=_("по"))
    per_page = forms.ChoiceField(label=_("На странице"), choices=PAGE_CHOICES, initial=25, required=False)
    burial_num_from = forms.IntegerField(required=False, label=_("Номер Захоронения с"))
    burial_num_to = forms.IntegerField(required=False, label=_("по"))
    reg_number_from = forms.IntegerField(required=False, label=_("Рег № с"))
    reg_number_to = forms.IntegerField(required=False, label=_(" по "))
    burial_container = forms.TypedChoiceField(required=False, label=_("Тип захоронения"), choices=EMPTY + Burial.BURIAL_CONTAINERS)

class OrderBurialForm(forms.ModelForm):
    """
    Форма создания или привязки захоронения к заказу
    """
    class Meta:
        model = Order
        fields = ()

    NB_CHOICES = (('new', _('Новое захоронение')), ('bind', _('Существующее')))
    
    nb_choice = forms.ChoiceField(label='', choices=NB_CHOICES, widget=forms.RadioSelect, initial='new')
    nb_burial = forms.IntegerField(required=False, label=_("Номер захоронения"))
    
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(OrderBurialForm, self).__init__(*args, **kwargs)

    def clean(self):
        cd = self.cleaned_data
        if self.is_valid():
            if cd['nb_choice'] == 'bind':
                if not cd['nb_burial']:
                    raise forms.ValidationError(_('Задайте номер захоронения'))
                try:
                    burial = Burial.objects.get(pk=cd['nb_burial'])
                    if burial.is_annulated() and \
                       burial.is_full() and burial.loru and burial.loru == self.request.user.profile.org:
                        # своё аннулированное. Чужие проверяются ниже
                        raise forms.ValidationError(_('Анулированное захоронение нельзя прикрепить к заказу'))
                    elif not burial.can_bind_to_order(self.request.user.profile.org):
                        raise forms.ValidationError(_('Это захоронение недоступно вашей организации'))
                    self.instance.burial = burial
                    self.instance.save()
                except Burial.DoesNotExist:
                    raise forms.ValidationError(_('Нет такого захоронения'))
        return cd

