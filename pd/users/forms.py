# coding=utf-8
import re

from django import forms
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _
from django.db.models.query_utils import Q

from captcha.fields import ReCaptchaField

from geo.forms import LocationForm
# from geo.models import DFiasAddrobj
from pd.forms import ChildrenJSONMixin, LoggingFormMixin
from burials.models import Cemetery, PlaceSize

from users.models import Profile, ProfileLORU, Org, BankAccount, RegisterProfile


class UserAddForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

    username = forms.SlugField(label=_(u"Логин"))
    password1 = forms.CharField(label=_(u"Пароль"), widget=forms.PasswordInput())
    password2 = forms.CharField(label=_(u"Пароль (повторите)"), widget=forms.PasswordInput())

    def clean_username(self):
        if User.objects.filter(username=self.cleaned_data['username']).exists():
            raise forms.ValidationError(_(u"Это имя уже используется"))
        return self.cleaned_data['username']

    def clean(self):
        if self.is_valid() and self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError(_(u"Пароли не совпадают"))
        return self.cleaned_data

    def save(self, *args, **kwargs):
        user = User.objects.create_user(
            self.cleaned_data['username'],
            self.cleaned_data['email'],
            self.cleaned_data['password1']
        )
        user.is_active = True
        user.save()
        Profile.objects.create(user=user)
        return user

class BaseLoruFormset(BaseInlineFormSet):
    @property
    def changed_data(self):
        for f in self.forms:
            if f.is_valid() and any(f.cleaned_data.values()):
                yield f.cleaned_data

LoruFormset = inlineformset_factory(Org, ProfileLORU, fk_name='ugh', formset=BaseLoruFormset)

BankAccountFormset = inlineformset_factory(Org, BankAccount, formset=BaseLoruFormset, extra=2)

# FIAS_REGIONS = DFiasAddrobj.objects.filter(parentguid='').order_by('formalname')

class ProfileForm(ChildrenJSONMixin, forms.ModelForm):

    org_type = forms.ChoiceField(label=_(u"Тип"), choices=Org.PROFILE_TYPES)
    org_name = forms.CharField(label=_(u"Краткое название организации"))
    org_full_name = forms.CharField(label=_(u"Полное название организации"), required=False)
    org_inn = forms.CharField(label=_(u"ИНН организации"))
    org_kpp = forms.CharField(label=_(u"КПП организации"), required=False)
    org_ogrn = forms.CharField(label=_(u"ОГРН организации"), required=False)
    org_director = forms.CharField(label=_(u"Директор"), required=False)
    org_email = forms.EmailField(label=_(u"Email"), required=False)
    org_phones = forms.CharField(label=_(u"Телефоны"), required=False)

    class Meta:
        model = Profile
        exclude = ['org', 'is_agent', 'region_fias', 'user', 'country', 'cemetery', 'area', ]

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        if self.instance.org:
            for f in self.fields:
                if f.startswith('org_'):
                    self.initial.update({f: getattr(self.instance.org, f[4:])})
            del self.fields['org_type']

    def clean_org_inn(self):
        inn = self.cleaned_data['org_inn']
        if inn:
            orgs = Org.objects.filter(inn=inn)
            if self.instance and self.instance.org:
                orgs = orgs.exclude(pk=self.instance.org.pk)
            if orgs.exists():
                raise forms.ValidationError(_(u"ИНН уже зарегистрирован"))
        return inn

    def save(self, commit=True, *args, **kwargs):
        obj = super(ProfileForm, self).save(commit=False, *args, **kwargs)
        params = dict([(k[4:], v) for k,v in self.cleaned_data.items() if v and k.startswith('org_')])
        if not obj.org:
            obj.org, _created = Org.objects.get_or_create(**params)
        else:
            Org.objects.filter(pk=obj.org.pk).update(**params)
        if commit:
            obj.save()
        return obj

class UserProfileForm(ChildrenJSONMixin, forms.ModelForm):
    # region = forms.ModelChoiceField(label=_(u"Регион"), queryset=FIAS_REGIONS, required=False)

    class Meta:
        model = Profile
        exclude = ['org', 'is_agent', 'region_fias', 'country', 'user']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['cemetery'].queryset = Cemetery.objects.filter(
            Q(ugh__isnull=True) |
            Q(ugh__loru_list__loru=self.instance.org) |
            Q(ugh=self.instance.org)
        ).distinct()    
        #if self.instance.region_fias:
            #self.initial['region'] = self.instance.get_region()

    #def save(self, commit=True, *args, **kwargs):
        #obj = super(UserProfileForm, self).save(commit=False, *args, **kwargs)
        #if self.cleaned_data['region']:
            #obj.region_fias = self.cleaned_data['region'].aoguid
        #if commit:
            #obj.save()
        #return obj

class UserDataForm(forms.ModelForm):
    is_agent = forms.BooleanField(label=_(u"Агент"), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'is_active' ,]

    def __init__(self, *args, **kwargs):
        super(UserDataForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.profile:
            self.initial['is_agent'] = self.instance.profile.is_agent
        if self.instance and self.instance.profile and self.instance.profile.is_ugh():
            del self.fields['is_agent']

    def save(self, *args, **kwargs):
        user = super(UserDataForm, self).save(*args, **kwargs)
        if not user.profile.is_ugh():
            user.profile.is_agent = self.cleaned_data['is_agent']
            user.profile.save()
        return user

class ChangePasswordForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['id', ] # guaranteed to be invisible and non-editable

    password1 = forms.CharField(label=_(u"Пароль"), widget=forms.PasswordInput())
    password2 = forms.CharField(label=_(u"Пароль (повторите)"), widget=forms.PasswordInput())

    def clean(self):
        if self.is_valid() and self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError(_(u"Пароли не совпадают"))
        return self.cleaned_data

    def save(self, commit=True, *args, **kwargs):
        self.instance.set_password(self.cleaned_data['password1'])
        if commit:
            self.instance.save()
        return self.instance

class BaseOrgForm(LoggingFormMixin, forms.ModelForm):

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(BaseOrgForm, self).__init__(*args, **kwargs)
        # требуется для self.collect_log_data():
        self.forms = []
        # Сделаем поле типа организации в зависимости от различных условий
        self.is_own_org = self.instance and self.instance.pk and self.instance.pk == request.user.profile.org.pk
        # Добавить новый ЗАГС, в форму передается пустой instance с заданным типом
        add_org_with_type = self.instance and not self.instance.pk and self.instance.type
        if self.is_own_org or add_org_with_type:
            del self.fields['type']
            self.fields['type_'] = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}),
                                                   initial = self.instance.get_type_display(),
                                                   required = False)
            self.fields['type_'].label = u'Тип'
            self.fields.keyOrder.insert(0, self.fields.keyOrder.pop(-1))
        else:
            choices = []
            for profile_type in Org.PROFILE_TYPES:
                if request.user.profile.is_ugh():
                    if profile_type[0] in (Org.PROFILE_LORU, Org.PROFILE_ZAGS, Org.PROFILE_COMPANY, ):
                        choices.append(profile_type)
                elif request.user.profile.is_loru():
                    if profile_type[0] in (Org.PROFILE_ZAGS, Org.PROFILE_COMPANY, ):
                        choices.append(profile_type)
                    # если лорику попался для редактирования другой лору:
                    elif self.instance and self.instance.pk and \
                         self.instance.type == Org.PROFILE_LORU and profile_type[0] == Org.PROFILE_LORU:
                        choices.append(profile_type)
                else:
                    if profile_type[0] in (Org.PROFILE_ZAGS, ):
                        choices.append(profile_type)
            label = self.fields['type'].label
            self.fields['type'] = forms.fields.TypedChoiceField(choices = choices)
            self.fields['type'].label = label

        type_posted = request.POST.get("%s-type" % self.prefix if self.prefix else "type")
        if type_posted and type_posted == Org.PROFILE_ZAGS or \
           add_org_with_type and add_org_with_type == Org.PROFILE_ZAGS:
            for f in ('full_name', 'inn', 'director', ):
                self.fields[f].required = False

    def clean_inn(self):
        inn = self.cleaned_data.get('inn')
        if inn:
            orgs = Org.objects.filter(inn=inn)
            if self.instance and self.instance.pk:
                orgs = orgs.exclude(pk=self.instance.pk)
            if orgs.exists():
                raise forms.ValidationError(_(u"ИНН уже зарегистрирован"))
        return inn

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            orgs = Org.objects.filter(name=name)
            if self.instance and self.instance.pk:
                orgs = orgs.exclude(pk=self.instance.pk)
            if orgs.exists():
                raise forms.ValidationError(_(u"Есть уже такая организация"))
        return name

PlaceSizeFormset = inlineformset_factory(Org, PlaceSize, formset=BaseInlineFormSet, can_delete=True, extra=2)

class OrgForm(BaseOrgForm):
    class Meta:
        model = Org
        exclude = ['off_address', ]

    def __init__(self, request, *args, **kwargs):
        super(OrgForm, self).__init__(request, *args, **kwargs)
        self.address_form = LocationForm(data=self.data or None, prefix='address', instance=self.instance.off_address)
        self.forms = [self.address_form, ]
        # self.bank_formset = BankAccountFormset(data=request.POST or None, instance=request.user.profile.org)
        if not self.is_own_org or not self.request.user.profile.is_ugh():
            del self.fields['numbers_algo']
            del self.fields['plan_date_days_before']
            del self.fields['archive_burial_fact_date_required']
        if not self.is_own_org or not self.request.user.profile.is_loru():
            del self.fields['opf_order']
            del self.fields['opf_order_customer_mandatory']
        if self.is_own_org and request.user.profile.is_ugh():
            self.placesize_formset = PlaceSizeFormset(data=request.POST or None, instance=self.instance)
        else:
            self.placesize_formset = None

    def is_valid(self):
        return super(OrgForm, self).is_valid() and self.address_form.is_valid() and \
                    (not self.placesize_formset or self.placesize_formset.is_valid())
                    # and self.bank_formset.is_valid()

    def save(self, commit=True):
        self.collect_log_data()
        org = super(OrgForm, self).save(commit=False)
        # self.bank_formset.save()
        if self.placesize_formset:
            self.placesize_formset.save()
        if any(self.address_form.cleaned_data.values()):
            org.off_address = self.address_form.save()
        if commit:
            org.save()
            self.put_log_data(msg=_(u'Изменены данные организации'))
        return org

class OrgLogForm(forms.Form):

    PAGE_CHOICES = (
        (10, 10),
        (25, 25),
        (50, 50),
        (100, 100),
    )

    log_date_from = forms.DateField(required=False, label=_(u"С"))
    log_date_to = forms.DateField(required=False, label=_(u"по"))
    per_page = forms.ChoiceField(label=_(u"На странице"), choices=PAGE_CHOICES, initial=25, required=False)

# Никакой разницы в этих формах пока нет.
LoginLogForm = OrgLogForm

class RegisterForm(forms.ModelForm):

    class Meta:
        model = RegisterProfile
        # Задаем порядок полей:
        fields = ('user_name', 'password1', 'password2',
                  'user_last_name', 'user_first_name', 'user_middle_name', 'user_email',
                  'org_type', 'org_name', 'org_full_name', 'org_inn', 'org_director',
                  'org_phone', 'org_fax',
                  'captcha',
                 )

    captcha = ReCaptchaField(label='')
    password1 = forms.CharField(label=_(u"Пароль"), widget=forms.PasswordInput())
    password2 = forms.CharField(label=_(u"Пароль (повторите)"), widget=forms.PasswordInput())

    def __init__(self, request, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['captcha'].error_messages['captcha_invalid'] = _(u'Неверно. Попробуйте еще раз.')

    def clean_user_name(self):
        user_name=self.cleaned_data['user_name'].strip()
        if not re.match(r'^[A-Za-z0-9_-]+$', user_name):
            raise forms.ValidationError(_(u"Имя может состоять только из латинских букв, "
                                          u"цифр, знаков подчеркивания или дефиса"))
        if User.objects.filter(username=user_name).exists():
            raise forms.ValidationError(_(u"Это имя уже используется в системе"))
        q = Q(user_name=user_name) & \
            ~Q(status__in=(RegisterProfile.STATUS_DECLINED, RegisterProfile.STATUS_APPROVED, ))
        if RegisterProfile.objects.filter(q).exists():
            raise forms.ValidationError(_(u"Это имя уже используется среди кандидатов на регистрацию"))
        return user_name

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_(u"Пароли не совпадают"))
        for field in cleaned_data:
            if field not in ('password1', 'password2') and \
              isinstance(cleaned_data[field], basestring):
                cleaned_data[field] = cleaned_data[field].strip()
        return cleaned_data
