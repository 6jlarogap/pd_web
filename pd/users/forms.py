# coding=utf-8
import re

from django.conf import settings
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _
from django.db import IntegrityError, transaction
from django.db.models.query_utils import Q
from django.db.models.fields.files import FieldFile

from geo.forms import LocationForm
from pd.forms import ChildrenJSONMixin, LoggingFormMixin, OurReCaptchaField, StrippedStringsMixin, \
                     CustomUploadModelForm, CustomClearableFileInput
from pd.models import validate_phone_as_number, validate_username
from pd.utils import host_country_code, EmailMessage
from burials.models import Cemetery, PlaceSize, Reason, Burial
from logs.models import write_log

from users.models import Profile, ProfileLORU, Org, BankAccount, RegisterProfile, OrgCertificate, \
                         Role, UserPhoto, Store, \
                         get_mail_footer, is_cabinet_user, is_trade_user

User._meta.get_field_by_name('email')[0]._unique = True
User._meta.get_field_by_name('email')[0].null=True

class LoruItemForm(forms.ModelForm):

    class Meta:
        model = ProfileLORU
        fields = ('loru',)

    def __init__(self, *args, **kwargs):
        super(LoruItemForm, self).__init__(*args, **kwargs)
        self.fields['loru'].queryset = self.fields['loru'].queryset.order_by('name')

    def clean(self):
        passed_forms = []
        for f in self.formset:
            if f['DELETE'].value():
                continue
            if f is not self and \
            f['loru'].value() == self['loru'].value() and \
            self not in passed_forms:
                raise forms.ValidationError(_(u'Уже есть выше это ЛОРУ:'))
            else:
                passed_forms.append(f)
        return self.cleaned_data


class BaseLoruFormset(BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        super(BaseLoruFormset, self).__init__(*args, **kwargs)
        for f in self.forms:
            f.formset = self

    @property
    def changed_data(self):
        for f in self.forms:
            if f.is_valid() and any(f.cleaned_data.values()):
                yield f.cleaned_data

LoruFormset = inlineformset_factory(Org, ProfileLORU, form=LoruItemForm, fk_name='ugh', formset=BaseLoruFormset)

BankAccountFormset = inlineformset_factory(Org, BankAccount, formset=BaseLoruFormset, extra=2)

class UserPhotoForm(CustomUploadModelForm):
    class Meta:
        model = UserPhoto
        fields = ('bfile', )
        widgets = {
            'bfile': CustomClearableFileInput(show_clear_checkbox_=True),
        }

    def __init__(self, *args, **kwargs):
        super(UserPhotoForm, self).__init__(*args, **kwargs)
        self.init_bfile()
        self.fields['bfile'].label = _(u'Фото пользователя')
        self.MAX_UPLOAD_SIZE_MB = 5
        self.CHECK_IF_IMAGE = True

class ProfileDataForm(ChildrenJSONMixin, LoggingFormMixin, forms.ModelForm):

    username = forms.CharField(label=_(u"Логин"), required=True)
    is_active = forms.BooleanField(required=False)
    email = forms.EmailField(required=False)

    password1 = forms.CharField(label=_(u"Пароль"), widget=forms.PasswordInput(), required=False)
    password2 = forms.CharField(label=_(u"Пароль (повторите)"), widget=forms.PasswordInput(), required=False)

    class Meta:
        model = Profile
        fields = (
            'username',
            'is_active',
            'user_last_name', 'user_first_name', 'user_middle_name',
            'email',
            'title',
            'phones',
            'is_agent',
            'out_of_staff',
            'password1', 'password2',
            'cemetery', 'area',
            'role', 'cemeteries',
            'store',
        )

    def __init__(self, request, my_profile, *args, **kwargs):
        super(ProfileDataForm, self).__init__(*args, **kwargs)
        self.request = request
        self.fields['phones'].widget = forms.TextInput()
        if not request.user.profile.org.is_loru():
            del self.fields['is_agent']

        if request.user.profile.org.is_ugh() and \
           not request.user.profile.is_admin() and \
           self.instance.pk and \
           self.instance.pk == request.user.profile.pk:
            my_profile = True
        self.my_profile = my_profile
        if my_profile:
            del self.fields['username']
        else:
            self.fields['username'].help_text=Profile.USERNAME_HELPTEXT

        self.fields['email'].label = User._meta.get_field('email').verbose_name.capitalize()
        self.fields['email'].help_text=User._meta.get_field('email').help_text

        if self.instance.pk and int(self.instance.pk) == int(request.user.profile.pk):
            del self.fields['is_active']
        else:
            self.fields['is_active'].label = User._meta.get_field('is_active').verbose_name.capitalize()
            self.fields['is_active'].help_text=User._meta.get_field('is_active').help_text

        if request.user.profile.is_loru():
            cemetery_qs  = Cemetery.objects.filter(
                ugh__loru_list__loru=self.request.user.profile.org
            )
        elif request.user.profile.is_ugh():
            q = Q(ugh=request.user.profile.org)
            if my_profile or not request.user.profile.is_admin():
                q &= Q(pk__in=[c.pk for c in Cemetery.editable_ugh_cemeteries(request.user)])
            cemetery_qs = Cemetery.objects.filter(q)
        else:
            cemetery_qs = Cemetery.objects.none()

        self.fields['cemetery'].queryset = cemetery_qs.distinct()

        store_qs = Store.objects.filter(loru=request.user.profile.org)
        if store_qs:
            self.fields['store'].queryset = store_qs
        else:
            del self.fields['store']

        self.fields['user_last_name'].required = True
        self.fields['user_first_name'].required = True
        self.fields['user_middle_name'].required = False

        if self.instance.pk:
            self.initial['username'] = self.instance.user.username
            self.initial['email'] = self.instance.user.email
            if 'is_active' in self.fields:
                self.initial['is_active'] = self.instance.user.is_active
        else:
            self.initial['is_active'] = True
            if 'is_agent' in self.fields:
                self.initial['is_agent'] = True
            self.fields['password1'].required = True
            self.fields['password2'].required = True

        if request.user.profile.is_loru() or \
           my_profile or \
           not request.user.profile.is_admin():
            del self.fields['role']
            del self.fields['cemeteries']
        else:
            cemeteries_qs = Cemetery.objects.filter(ugh=request.user.profile.org)
            self.fields['cemeteries'].queryset = cemeteries_qs
            self.fields['role'].widget.attrs.update({'size': str(min(Role.objects.all().count()+1, 20))})
            self.fields['cemeteries'].widget.attrs.update({'size': str(min(cemeteries_qs.count()+1, 20))})
            # По умолчанию новому пользователю ОМС назначаем все роли и все кладбища
            if not self.instance or not self.instance.pk:
                self.initial['role'] = [Role.objects.get(name=Role.ROLE_REGISTRATOR)]

        photo = None
        if self.instance.pk:
            try:
                photo = UserPhoto.objects.get(user=self.instance.user)
            except UserPhoto.DoesNotExist:
                pass
        self.photo_form = UserPhotoForm(request, prefix='user-photo', instance = photo, files=request.FILES)

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        validate_username(username)
        f_username = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            f_username = f_username.exclude(pk=self.instance.user.pk)
        if f_username.exists():
            raise forms.ValidationError(_(u"Этот логин уже используется"))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip() or None
        if email:
            f_email = User.objects.filter(email__iexact=email)
            if self.instance.pk:
                f_email = f_email.exclude(pk=self.instance.user.pk)
            if f_email.exists():
                raise forms.ValidationError(_(u"Этот email уже используется"))
        return email
    
    def clean_role(self):
        # Нельзя удалить последнего администратора 
        role = self.cleaned_data.get('role')
        if self.instance.pk and self.instance.is_admin():
            role_admin = Role.objects.get(name=Role.ROLE_ADMIN)
            if role_admin not in role and not Profile.objects.filter(
                    org=self.instance.org,
                    role=role_admin,
                ).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError(_(u"Нельзя удалять последнего администратора в организации"))
        return role

    def is_valid(self):
        return super(ProfileDataForm, self).is_valid() and self.photo_form.is_valid()

    def clean(self):
        if self.is_valid():
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_(u"Пароли не совпадают"))
            cemetery = self.cleaned_data.get('cemetery')
            cemeteries = self.cleaned_data.get('cemeteries')
            if cemeteries is not None and cemetery and cemetery not in cemeteries:
                raise forms.ValidationError(_(u"Кладбище по умолчанию не из доступных для пользователя"))
        return self.cleaned_data

    @transaction.commit_on_success
    def save(self):
        if self.instance.pk:
            self.collect_log_data()
            profile = super(ProfileDataForm, self).save()
            save_user = False
            for f in self.changed_data:
                if f in ('username', 'email', 'is_active',):
                    setattr(profile.user, f, self.cleaned_data[f])
                    save_user = True
            if not profile.user.email:
                profile.user.email = None
            if self.cleaned_data.get('password1'):
                profile.user.set_password(self.cleaned_data['password1'])
                save_user = True
            if save_user:
                try:
                    profile.user.save()
                except IntegrityError:
                    transaction.rollback()
                    # метод form_valid из view покажет message.error
                    return None
            self.put_log_data(
                msg=_(u'Изменены данные пользователя %(fio)s (%(username)s)') % dict(
                    fio=profile,
                    username=profile.user.username,
                ),
                log_instance=profile.org,
            )
            self.put_log_data(
                msg=_(u'Изменены данные'),
                log_instance=profile,
            )
            if self.cleaned_data['password1']:
                write_log(self.request, profile, _(u'Установлен пароль'))
                write_log(
                    self.request,
                    profile.org,
                    _(u'Установлен пароль пользователя %(fio)s (%(username)s)') % dict(
                        fio=profile,
                        username=profile.user.username,
                ))
        else:
            try:
                user = User.objects.create(
                    username=self.cleaned_data['username'],
                    email=self.cleaned_data['email'],
                    is_active=self.cleaned_data['is_active'],
                    password=make_password(self.cleaned_data['password1'])
                )
            except IntegrityError:
                transaction.rollback()
                # метод form_valid из view покажет message.error
                return None
            profile = super(ProfileDataForm, self).save(commit=False)
            profile.user = user
            profile.org = self.request.user.profile.org
            profile.save(force_insert=True)
            roles = self.cleaned_data.get('role', [])
            for role in roles:
                profile.role.add(role)
            cemeteries = self.cleaned_data.get('cemeteries', [])
            for cemetery in cemeteries:
                profile.cemeteries.add(cemetery)
            write_log(self.request, profile.org, _(u'Добавлен пользователь %s') % user.username)

        photo_uploaded = photo_clear = False
        if self.photo_form.is_valid():
            self.photo_form.clean()
            bfile = self.photo_form.cleaned_data.get('bfile')
            # FieldFile -- это еще не UploadedFile
            photo_uploaded = bfile and not isinstance(bfile, FieldFile)
            photo_clear = self.request.POST.get(self.photo_form.prefix+'-bfile-clear')

            if self.photo_form.instance.pk:
                if photo_clear and not photo_uploaded:
                    self.photo_form.instance.delete()
                    write_log(self.request, self.instance.user, _(u'Фото удалено'))
                    write_log(
                        self.request,
                        self.instance.user.profile.org,
                        _(u'Изменены данные пользователя %(fio)s (%(username)s)\nФото удалено') % dict(
                            fio=profile,
                            username=profile.user.username,
                    ))
                    return profile
                if photo_clear or photo_uploaded:
                    UserPhoto.objects.get(pk=self.photo_form.instance.pk).delete_from_media()
            if photo_uploaded:
                photo = self.photo_form.save(commit=False)
                photo.user = self.instance.user
                photo.save()
                write_log(self.request, self.instance.user, _(u'Прикреплено фото: %s') % photo.original_name)
                write_log(
                    self.request,
                    self.instance.user.profile.org,
                    _(u'Изменены данные пользователя %(fio)s (%(username)s)\nПрикреплено фото: %(photo)s') % dict(
                        fio=profile,
                        username=profile.user.username,
                        photo=photo.original_name,
                ))

        return profile

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
        country_code = host_country_code(request)
        if country_code == 'by':
            if 'inn' in self.fields:
                self.fields['inn'].label = _(u'УНП')
            if 'ogrn' in self.fields:
                self.fields['ogrn'].label = _(u'ОКПО')
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
                    if profile_type[0] in (Org.PROFILE_LORU, Org.PROFILE_ZAGS, Org.PROFILE_MEDIC, Org.PROFILE_COMPANY, ):
                        choices.append(profile_type)
                elif request.user.profile.is_loru():
                    if profile_type[0] in (Org.PROFILE_ZAGS, Org.PROFILE_MEDIC, Org.PROFILE_COMPANY, ):
                        choices.append(profile_type)
                    # если лорику попался для редактирования другой лору:
                    elif self.instance and self.instance.pk and \
                         self.instance.type == Org.PROFILE_LORU and profile_type[0] == Org.PROFILE_LORU:
                        choices.append(profile_type)
                else:
                    if profile_type[0] in (Org.PROFILE_ZAGS, Org.PROFILE_MEDIC, ):
                        choices.append(profile_type)
            label = self.fields['type'].label
            self.fields['type'] = forms.fields.TypedChoiceField(choices = choices)
            self.fields['type'].label = label

        #type_posted = request.POST.get("%s-type" % self.prefix if self.prefix else "type")
        #if type_posted and type_posted == Org.PROFILE_ZAGS or \
           #add_org_with_type and add_org_with_type == Org.PROFILE_ZAGS:
            #for f in ('full_name', 'inn', ):
                #if f in self.fields:
                    #self.fields[f].required = False

    def clean_inn(self):
        inn = self.cleaned_data.get('inn', '').strip()
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
ReasonFormset = inlineformset_factory(Org, Reason, formset=BaseInlineFormSet, can_delete=True, extra=2)

class OrgCertificateForm(CustomUploadModelForm):
    class Meta:
        model = OrgCertificate
        fields = ('bfile', )
        widgets = {
            'bfile': CustomClearableFileInput(show_clear_checkbox_=False),
        }

    def __init__(self, *args, **kwargs):
        super(OrgCertificateForm, self).__init__(*args, **kwargs)
        self.init_bfile()
        self.fields['bfile'].label = _(u'Скан свидетельства о регистрации')
        self.MAX_UPLOAD_SIZE_MB = 5

class OrgForm(StrippedStringsMixin, BaseOrgForm):
    class Meta:
        model = Org
        exclude = ('off_address', )

    def __init__(self, request, *args, **kwargs):
        super(OrgForm, self).__init__(request, *args, **kwargs)
        self.user_qs = []
        self.address_form = LocationForm(data=self.data or None, prefix='address', instance=self.instance.off_address)
        self.forms = [self.address_form, ]
        # self.bank_formset = BankAccountFormset(data=request.POST or None, instance=request.user.profile.org)
        if not self.is_own_org:
            del self.fields['death_date_offer']
            del self.fields['opf_burial']
            del self.fields['hide_deadman_address']
            del self.fields['plan_time_required']
        if not self.is_own_org or not is_trade_user(self.request.user):
            del self.fields['sms_phone']
        if not self.is_own_org or not self.request.user.profile.is_ugh():
            del self.fields['numbers_algo']
            del self.fields['plan_date_days_before']
            del self.fields['max_graves_count']
        if not self.is_own_org or not self.request.user.profile.is_loru():
            del self.fields['opf_order']
            del self.fields['opf_order_customer_mandatory']
            del self.fields['is_wholesale_with_vat']
        if 'currency' in self.fields and \
           not (self.instance and self.instance.pk and self.instance.type == Org.PROFILE_LORU):
            self.fields['currency'].help_text = None
        if self.is_own_org and request.user.profile.is_ugh():
            self.placesize_formset = PlaceSizeFormset(data=request.POST or None, instance=self.instance)
        else:
            self.placesize_formset = None

        self.scan_form = scan = None
        if self.is_own_org:
            self.user_qs = self.instance.profile_set.all().order_by('user__username')
            self.reason_formset = ReasonFormset(data=request.POST or None, instance=self.instance)
            choices = [('', '---------')]
            for reason_type in Reason.TYPE_CHOICES:
                if request.user.profile.is_ugh():
                    if reason_type[0] in Reason.TYPES_UGH:
                        choices.append(reason_type)
                elif request.user.profile.is_loru():
                    if reason_type[0] in Reason.TYPES_LORU:
                        choices.append(reason_type)
            label = self.reason_formset.forms[0].fields['reason_type'].label
            for f in self.reason_formset.forms:
                f.fields['reason_type'] = forms.fields.TypedChoiceField(choices = choices, label=label)
                # f.prefix += '-reason'

            try:
                scan = self.instance.orgcertificate
            except OrgCertificate.DoesNotExist:
                pass
            self.scan_form = OrgCertificateForm(request, prefix='org-scan', instance = scan, files=request.FILES)

        else:
            self.reason_formset = None

    def clean_numbers_algo(self):
        """
        Если выбрали рег. номер "ост. пустым", то у этого угх не должно быть кладбищ с местом "по рег. №", 
        """
        numbers_algo = self.cleaned_data.get('numbers_algo')
        if numbers_algo and numbers_algo == Org.NUM_EMPTY:
            q = Q(ugh=self.request.user.profile.org) & \
                (Q(places_algo=Cemetery.PLACE_BURIAL_ACCOUNT_NUMBER) |
                 Q(places_algo_archive=Cemetery.PLACE_ARCHIVE_BURIAL_ACCOUNT_NUMBER)
                )
            if Cemetery.objects.filter(q).exists():
                raise forms.ValidationError(_(u"Указанный способ недопустим, т.к. есть кладбища "
                                              u"с расстановкой номеров мест (в т.ч. архивных) "
                                              u"по рег. номеру захоронения"))
        return numbers_algo

    def is_valid(self):
        return super(OrgForm, self).is_valid() and self.address_form.is_valid() and \
                    (not self.placesize_formset or self.placesize_formset.is_valid()) and \
                    (not self.reason_formset or self.reason_formset.is_valid()) and \
                    (not self.scan_form or self.scan_form.is_valid())
                    # and self.bank_formset.is_valid()

    def save(self, commit=True):
        self.collect_log_data()
        org = super(OrgForm, self).save(commit=False)
        # self.bank_formset.save()
        if self.placesize_formset:
            self.placesize_formset.save()
        if self.reason_formset:
            self.reason_formset.save()
        old_addr = org.off_address
        org.off_address = self.address_form.save()

        scan_uploaded = scan_clear = False
        if self.scan_form:
            bfile = self.scan_form.cleaned_data.get('bfile')
            # FieldFile -- это еще не UploadedFile
            scan_uploaded = bfile and not isinstance(bfile, FieldFile)
            scan_clear = self.request.POST.get(self.scan_form.prefix+'-bfile-clear')

        if commit and self.scan_form:
            if self.scan_form.instance.pk:
                if scan_clear and not scan_uploaded:
                    self.scan_form.instance.delete()
                    write_log(self.request, org, _(u'Скан свидетельства о регистрации удален'))
                if scan_uploaded:
                    OrgCertificate.objects.get(pk=self.scan_form.instance.pk).delete_from_media()
            if scan_uploaded:
                scan = self.scan_form.save(commit=False)
                scan.org = org
                scan.save()
                write_log(self.request, org, _(u'Прикреплен скан свидетельства о регистрации: %s') % scan.original_name)

        if commit:
            org.save()
            if old_addr and not org.off_address:
                try:
                    old_addr.delete()
                except IntegrityError:
                    pass
            self.put_log_data(msg=_(u'Изменены данные организации'))
        return org

class FromToPageForm(forms.Form):

    PAGE_CHOICES = (
        (10, 10),
        (25, 25),
        (50, 50),
        (100, 100),
    )

    date_from = forms.DateField(required=False, label=_(u"С"))
    date_to = forms.DateField(required=False, label=_(u"по"))
    per_page = forms.ChoiceField(label=_(u"На странице"), choices=PAGE_CHOICES, initial=25, required=False)

OrgLogForm = FromToPageForm

class OrgLogForm(FromToPageForm):

    users = forms.MultipleChoiceField(label=_(u"Пользователи"),choices=())

# Никакой разницы в этих формах пока нет.
LoginLogForm = FromToPageForm

# В этой форме во view заменяем required для дат
OmsOperStats = FromToPageForm

class RegisterForm(forms.ModelForm):

    class Meta:
        model = RegisterProfile
        # Задаем порядок полей:
        #fields = ('user_name', 'password1', 'password2',
                  #'user_last_name', 'user_first_name', 'user_middle_name', 'user_email',
                  #'org_type', 'org_name', 'org_full_name', 'org_currency', 'org_inn', 'org_ogrn',
                  #'org_director', 'org_basis', 'org_phones', 'org_fax', 
                  #'captcha',
                 #)
        fields = ('user_name', 'password1', 'password2',
                  'user_last_name', 'user_first_name', 'user_middle_name', 'user_email',
                  'org_type', 'org_name', 'org_full_name',
                  'org_director',               'org_phones', 'org_fax', 
                  'captcha',
                 )

    captcha = OurReCaptchaField(label='')
    password1 = forms.CharField(label=_(u"Пароль"), widget=forms.PasswordInput())
    password2 = forms.CharField(label=_(u"Пароль (повторите)"), widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.address_form = LocationForm(data=self.data or None, prefix='address', instance=self.instance.org_address)
        self.address_form.fields['country_name'].required = True
        self.address_form.fields['region_name'].required = True
        self.address_form.fields['city_name'].required = True
        
    def clean_org_name(self):
        org_name=self.cleaned_data.get('org_name', '').strip()
        if not org_name:
            raise forms.ValidationError(_(u"Пустое название организации"))
        if re.search(r'^[\d\s]+$', org_name):
            raise forms.ValidationError(_(u"Невозможное название организации (только из цифр)"))
        return org_name

    def clean_user_name(self):
        user_name=self.cleaned_data['user_name']
        if User.objects.filter(username=user_name).exists():
            raise forms.ValidationError(_(u"Это имя уже используется в системе"))
        q = Q(user_name=user_name) & \
            ~Q(status__in=(RegisterProfile.STATUS_DECLINED, RegisterProfile.STATUS_APPROVED, ))
        if RegisterProfile.objects.filter(q).exists():
            raise forms.ValidationError(_(u"Это имя уже используется среди кандидатов на регистрацию"))
        return user_name

    def clean_user_email(self):
        user_email=self.cleaned_data['user_email']
        if User.objects.filter(email=user_email).exists():
            raise forms.ValidationError(_(u"Этот почтовый адрес уже используется в системе"))
        q = Q(user_email=user_email) & \
            ~Q(status__in=(RegisterProfile.STATUS_DECLINED, RegisterProfile.STATUS_APPROVED, ))
        if RegisterProfile.objects.filter(q).exists():
            raise forms.ValidationError(_(u"Этот почтовый адрес уже используется среди кандидатов на регистрацию"))
        return user_email

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

    def is_valid(self):
        return super(RegisterForm, self).is_valid() and self.address_form.is_valid()

class OrgBurialStatsForm(forms.Form):

    EMPTY = (('', _(u'Закрытые и эксгумированные')),)

    date_from = forms.DateField(required=False, label=_(u"С"))
    date_to = forms.DateField(required=False, label=_(u"по"))
    status = forms.TypedChoiceField(required=False, label=_(u"Статус"), choices=EMPTY + Burial.STATUS_CHOICES)

class LoruOrdersStatsForm(forms.Form):

    date_from = forms.DateField(required=False, label=_(u"С"))
    date_to = forms.DateField(required=False, label=_(u"по"))
    supplier = forms.CharField(required=False, max_length=60, label=_(u"Поставщик"))

class SupportForm(forms.Form):
    user_last_name = forms.CharField(label=_(u"Фамилия"), max_length=100, required=True)
    user_first_name = forms.CharField(label=_(u"Имя"), max_length=100, required=False)
    user_middle_name = forms.CharField(label=_(u"Отчество"), max_length=255, required=False)
    subject = forms.CharField(label=_(u'Тема'), max_length=100, required=False)
    message = forms.CharField(label=_(u'Вопрос'), widget=forms.Textarea, required=False)
    sender = forms.EmailField(label=_(u'Email для получения ответа'), required=False)
    callback = forms.BooleanField(label=_(u"Заказать обратный звонок"), required=False)
    phone = forms.CharField(
        label=_(u"Телефон"),
        help_text=_(u'В международном формате: +код-страны-код-города-номер-телефона'),
        required=False,
    )
    captcha = OurReCaptchaField(label='', required=True)

    def __init__(self, request, *args, **kwargs):
        super(SupportForm, self).__init__(*args, **kwargs)
        self.request = request
        self.save_user_email = False
        self.save_org_phone = False
        self.fio = ('user_last_name', 'user_first_name', 'user_middle_name', )
        if request.user.is_authenticated():
            del self.fields['captcha']
            self.initial['sender'] = request.user.email or \
                                     not is_cabinet_user(request.user) and request.user.profile.org.email or \
                                     ''
            if not self.initial['sender']:
                self.fields['sender'].label = _(u'Email для получения ответа (будет сохранен как Ваш контактный)')
                self.save_user_email = not request.user.email
            self.initial['phone'] = re.split(r'\s+', request.user.profile.org.phones or '')[0]
            if not self.initial['phone']:
                self.fields['phone'].label = _(u'Телефон (будет сохранен как телефон Вашей организации)')
                self.save_org_phone = True
            for f in self.fio:
                self.initial[f] = getattr(request.user.profile, f)
            user_request = request.GET.get('request')
            if user_request and user_request == u'add_doctype':
                self.initial['subject'] = _(u'Добавить тип документа')
                self.initial['message'] = _(u'Прошу добавить следующий тип документа:\n'
                                            u'________________________.\n\n'
                                            u'Пока новый тип не добавлен, вношу запись о документе '
                                            u'физического лица как об удостоверении.\n'
                )
                burial_path = request.GET.get('burial_path')
                if burial_path:
                    burial_path = u"%s://%s%s" % (
                        'https' if request.is_secure() else 'http',
                        request.get_host(),
                        burial_path,
                    )
                    self.initial['message'] = u"%sПравилось захоронение:\n%s\n" % \
                        (self.initial['message'], burial_path, )

    def clean(self):
        if self.is_valid():
            if self.cleaned_data.get('callback'):
                try:
                    validate_phone_as_number(self.cleaned_data.get('phone', '').lstrip('+'))
                except ValidationError:
                    raise forms.ValidationError(_(u"Не указан или неверен телефон для обратного звонка"))
            elif not self.cleaned_data.get('message') or not self.cleaned_data.get('sender'):
                raise forms.ValidationError(_(u"Если не требуется обратный звонок, то задайте вопрос и укажите Email"))
            if not self.cleaned_data.get('user_first_name', '').strip() and \
               self.cleaned_data.get('user_middle_name', '').strip():
                raise forms.ValidationError(_(u"Не указано имя при указанном отчестве"))
        return self.cleaned_data
        
    def save(self):
        if self.cleaned_data.get('subject'):
            email_subject = self.cleaned_data['subject']
        else:
            email_subject = _(u'Вопрос в поддержку')
        email_from = self.cleaned_data.get('sender')
        if self.save_user_email and email_from:
            self.request.user.email = email_from
            try:
                self.request.user.save()
            except IntegrityError:
                pass
        org_phone = self.cleaned_data.get('phone')
        if self.save_org_phone and org_phone and self.cleaned_data.get('callback'):
            self.request.user.profile.org.phones = org_phone
            self.request.user.profile.org.save()
        if self.request.user.is_authenticated():
            changed_ = False
            for f in self.fio:
                if f in self.changed_data:
                    changed_ = True
                    break
            if changed_:
                self.request.user.profile.user_last_name = self.cleaned_data.get('user_last_name', '')
                self.request.user.profile.user_first_name = self.cleaned_data.get('user_first_name', '')
                self.request.user.profile.user_middle_name = self.cleaned_data.get('user_middle_name', '')
                self.request.user.profile.save()
        email_text = self.cleaned_data.get('message', '')
        email_text += u"\n----------\n\n%s: %s %s %s" % (
                        _(u'Запрос от'),
                        self.cleaned_data.get('user_last_name', ''),
                        self.cleaned_data.get('user_first_name', ''),
                        self.cleaned_data.get('user_middle_name', ''),
                      )
        if self.cleaned_data.get('callback'):
            email_text += u"\n\n%s\n%s %s" % (
                _(u'ЗАКАЗАН ОБРАТНЫЙ ЗВОНОК'),
                _(u'телефон'),
                self.cleaned_data['phone'],
            )
        email_text += get_mail_footer(self.request.user)
        email_to = settings.SUPPORT_EMAILS
        headers = {}
        if email_from:
            headers['Reply-To'] = email_from
        # Если в From: поставить задавшего вопрос, например, user@yandex.ru,
        # то письмо придет в email_to (адреса гугловской почты) с "замечаниями"
        # в заголовке, что письмо пришло не от yandex, так и в спам может попасть.
        # Посему реальный отправитель будет в Reply-To:
        #
        email_from = _(u"Вопрос в поддержку <%s>") % settings.DEFAULT_FROM_EMAIL
        EmailMessage(email_subject, email_text, email_from, email_to, headers=headers, ).send()

class TestCaptchaForm(forms.Form):
    captcha = OurReCaptchaField(label='')

class VideoSearchForm(forms.Form):
    PAGE_CHOICES = (
        (5, 5),
        (10, 10),
        (25, 25),
        (50, 50),
    )

    per_page = forms.ChoiceField(label=_(u"На странице"), choices=PAGE_CHOICES, initial=25, required=False)
