# coding=utf-8
import datetime
import json
import random
import string
import re

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.aggregates import Max
from django.db.models.deletion import ProtectedError
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.db.models.query_utils import Q

from burials.models import Cemetery, Area, Burial, Place, ExhumationRequest, BurialFiles
from geo.forms import LocationForm
from orders.models import Order
from pd.forms import PartialFormMixin, ChildrenJSONMixin, LoggingFormMixin
from persons.forms import DeadPersonForm, DeathCertificateForm, AlivePersonForm, PersonIDForm, StrippedStringsMixin
from persons.models import DeathCertificate, PersonID, IDDocumentType, SafeDeleteMixin
from users.forms import BaseOrgForm
from users.models import Org, Profile, Dover
from logs.models import write_log


OPF_CHOICES = (('person', _(u'ФЛ')), ('org', _(u'ЮЛ')))

class BaseCemeteryForm(forms.ModelForm):
    def clean_time_slots(self):
        slots = self.cleaned_data['time_slots'].split('\n')
        slots = filter(lambda s: s.strip(), slots)
        try:
            slots = map(lambda s: datetime.datetime.strptime(s.strip(), '%H:%M'), slots)
        except ValueError:
            raise forms.ValidationError(_(u'Формат должен быть: по одному времени в формате ЧЧ:ММ на строку'))
        return u'\n'.join([s.strftime('%H:%M') for s in slots])

class CemeteryForm(BaseCemeteryForm):
    class Meta:
        model = Cemetery
        exclude = ['ugh', ]

    def __init__(self, *args, **kwargs):
        super(CemeteryForm, self).__init__(*args, **kwargs)
        address = self.instance and self.instance.address
        self.address_form = LocationForm(data=self.data or None, instance=address, prefix='address')
        #self.address_form.fields['country_name'].required = True
        if self.instance and self.instance.pk:
            self.area_formset = AreaFormset(data=self.data or None, instance=self.instance)
        else:
            self.area_formset = None

    def is_valid(self):
        return super(CemeteryForm, self).is_valid() and self.address_form.is_valid() and (not self.area_formset or self.area_formset.is_valid())

    def save(self, commit=True, *args, **kwargs):
        obj = super(CemeteryForm, self).save(commit=False, *args, **kwargs)
        if obj.pk and self.area_formset:
            self.area_formset.save()
        obj.address = None
        if self.address_form.is_valid_data():
            obj.address = self.address_form.save()
        if commit:
            obj.save()
        return obj


class CemeteryAdminForm(BaseCemeteryForm):
    class Meta:
        model = Cemetery

class BaseAreaFormset(BaseInlineFormSet):
    def clean(self):
        for df in getattr(self, 'deleted_forms', []):
            if df.instance:
                if df.instance.burial_set.exists():
                    msg = _(u'Участок %s с <a href="/burials/?area=%s" target="_blank">захоронениями</a> удалить нельзя')
                    raise forms.ValidationError(mark_safe(msg % (df.instance.name, df.instance.name)))

AreaFormset = inlineformset_factory(Cemetery, Area, formset=BaseAreaFormset, can_delete=True)

class PlaceEditForm(forms.ModelForm):
    class Meta:
        model = Place
#        fields = ['places_count']

#    def __init__(self, *args, **kwargs):
#        super(PlaceEditForm, self).__init__(*args, **kwargs)
#        if not self.instance.places_count:
#            if self.instance.area:
#                self.initial['places_count'] = self.instance.area.places_count
#            else:
#                self.initial['places_count'] = 1

#    def clean_places_count(self):
#        burials = self.instance.burials_available()
#        max_num = burials.aggregate(max=Max('grave_number')).get('max') or 1
#        if self.cleaned_data['places_count'] < max_num:
#            raise forms.ValidationError(_(u"Нельзя установить меньше %s, столько могил уже занято") % max_num)
#        return self.cleaned_data['places_count']

EMPTY = (('', '--------'),)

class BurialSearchForm(forms.Form):
    """
    Форма поиска на главной странице.
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
    account_number_from = forms.IntegerField(required=False, label=_(u"Рег. № с"))
    account_number_to = forms.IntegerField(required=False, label=_(u"по"))
    applicant_org = forms.CharField(required=False, max_length=60, label=_(u"Заявитель-ЮЛ"))
    applicant_person = forms.CharField(required=False, max_length=40, label=_(u"Заявитель-ФЛ"))
    responsible = forms.CharField(required=False, max_length=40, label=_(u"Ответственный"))
    operation = forms.ChoiceField(required=False, choices=EMPTY + Burial.BURIAL_TYPES, label=_(u"Вид захоронения"))
    burial_container = forms.TypedChoiceField(required=False, label=_(u"Тип захоронения"), choices=EMPTY + Burial.BURIAL_CONTAINERS)
    cemetery = forms.CharField(required=False, label=_(u"Кладбище"))
    area = forms.CharField(required=False, label=_(u"Участок"))
    row = forms.CharField(required=False, label=_(u"Ряд"))
    place = forms.CharField(required=False, label=_(u"Место"))
    no_responsible = forms.BooleanField(required=False, initial=False, label=_(u"Без отв."))
    source = forms.TypedChoiceField(required=False, label=_(u"Источник"), choices=EMPTY + Burial.SOURCE_TYPES)
    status = forms.TypedChoiceField(required=False, label=_(u"Статус"), choices=EMPTY + Burial.STATUS_CHOICES)
    annulated = forms.BooleanField(required=False, initial=False, label=_(u"Аннулировано"))
    per_page = forms.ChoiceField(label=_(u"На странице"), choices=PAGE_CHOICES, initial=25, required=False)

class ResponsibleForm(AlivePersonForm):
    WHERE_FROM_PLACE = u'place'
    WHERE_FROM_APPLICANT = u'applicant'
    WHERE_NEW = u'new'
    WHERE_CHOICES = (
        (WHERE_FROM_PLACE, _(u'Существующий (из места)')),
        (WHERE_FROM_APPLICANT, _(u'Заявитель')),
        (WHERE_NEW, _(u'Новый')),
    )

    take_from = forms.ChoiceField(label=_(u"Где берем Ответственного?"), choices=WHERE_CHOICES,
                                  widget=forms.RadioSelect, required=True, initial=WHERE_NEW)
    place = forms.ModelChoiceField(queryset=Place.objects.all(), widget=forms.HiddenInput, required=False)
    order = forms.ModelChoiceField(queryset=Order.objects.all().select_related('loru'), widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(ResponsibleForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields['take_from']
        else:
            self.fields.keyOrder.insert(0, self.fields.keyOrder.pop(-3))

        self.initial.setdefault('take_from', self.WHERE_NEW)

    def clean(self):
        if self.cleaned_data.get('take_from') == self.WHERE_FROM_PLACE:
            if not self.cleaned_data.get('place'):
                raise forms.ValidationError(_(u'Нет Места'))
            if not self.cleaned_data.get('place').responsible:
                raise forms.ValidationError(_(u'Нет Ответственного у Места'))
        return self.cleaned_data

    def save(self, *args, **kwargs):
        if self.instance.pk:
            return super(ResponsibleForm, self).save(*args, **kwargs)
        elif self.cleaned_data.get('take_from') == self.WHERE_FROM_PLACE:
            return self.cleaned_data['place'].responsible.deep_copy()
        else:
            return super(ResponsibleForm, self).save(*args, **kwargs)

    def is_valid_data(self):
        if self.is_valid():
            return self.cleaned_data.get('last_name') or self.cleaned_data.get('take_from') != self.WHERE_NEW
        else:
            return False

class BurialPublicListForm(forms.Form):
    """
    Форма поиска захоронений для ЛОРУ, не только среди своих заказов
    """

    PAGE_CHOICES = (
        (10, 10),
        (25, 25),
        (50, 50),
        (100, 100),
    )

    fio = forms.CharField(required=True, max_length=100, label=_(u"ФИО"))
    birth_date_from = forms.DateField(required=False, label=_(u"Дата рожд. с"))
    birth_date_to = forms.DateField(required=False, label=_(u"по"))
    death_date_from = forms.DateField(required=False, label=_(u"Дата смерти с"))
    death_date_to = forms.DateField(required=False, label=_(u"по"))
    burial_date_from = forms.DateField(required=False, label=_(u"Дата захор. с"))
    burial_date_to = forms.DateField(required=False, label=_(u"по"))
    account_number_from = forms.IntegerField(required=False, label=_(u"Рег. № с"))
    account_number_to = forms.IntegerField(required=False, label=_(u"по"))
    cemetery = forms.CharField(required=True, label=_(u"Кладбище"))
    area = forms.CharField(required=False, label=_(u"Участок"))
    row = forms.CharField(required=False, label=_(u"Ряд"))
    place = forms.CharField(required=False, label=_(u"Место"))
    per_page = forms.ChoiceField(label=_(u"На странице"), choices=PAGE_CHOICES, initial=25, required=False)

class BurialForm(PartialFormMixin, ChildrenJSONMixin, LoggingFormMixin, SafeDeleteMixin, StrippedStringsMixin, forms.ModelForm):
    COFFIN = 'coffin'
    URN = 'urn'

    burial_container = forms.ChoiceField(label=_(u"Тип захоронения"), choices=Burial.BURIAL_CONTAINERS, widget=forms.RadioSelect,  required=False)
    burial_type = forms.ChoiceField(label=_(u"Вид захоронения"), choices=Burial.BURIAL_TYPES, widget=forms.RadioSelect,  required=False)
    opf = forms.ChoiceField(label=_(u'ОПФ'), choices=OPF_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = Burial
        exclude = ['place', 'deadman', 'responsible', 'applicant', 'annulated', ]

    def __init__(self, request, *args, **kwargs):
        super(BurialForm, self).__init__(*args, **kwargs)
        self.request = request
        self.fields['cemetery'].queryset = Cemetery.objects.filter(
            Q(ugh__isnull=True) |
            Q(ugh__loru_list__loru=self.request.user.profile.org) |
            Q(ugh=self.request.user.profile.org)
        ).distinct()
        if self.instance and self.instance.cemetery and self.instance.cemetery.time_slots:
            choices = [('', '----------')] + self.instance.cemetery.get_time_choices(
                date=self.instance.plan_date,
                request=self.request,
            )
            self.fields['plan_time'].widget = forms.Select(choices=choices)
        if self.instance.plan_time:
            self.initial['plan_time'] = self.instance.plan_time.strftime('%H:%M')

        if not self.instance.plan_date:
            date_diff = 1
            if datetime.date.today().weekday() == 5 and request.user.profile.is_ugh():
                date_diff = 2 # Saturday
            self.initial['plan_date'] = datetime.date.today() + datetime.timedelta(date_diff)

        self.order = None
        order_pk = self.request.REQUEST.get('order')
        if self.request.user.profile.is_loru() and order_pk:
            self.order = Order.objects.get(pk=order_pk, loru=self.request.user.profile.org)

        # Отсутствие выбора будет в выпадающем списке не "---", а ""
        self.fields['applicant_organization'].empty_label = ''
        
        places_count = 1
        if self.instance.place_number and self.instance.get_place():
            places_count = self.instance.get_place().get_graves_count()
        elif self.instance.area:
            places_count = self.instance.area.places_count
        # - Вдруг уменьшат параметры участка так, что номер могилы в захоронении
        #   окажется больше числа могил в участке для нового места
        # - Вдруг вообще не укажут кладбище или участок, но в записи захоронения
        #   уже не 1-е место. Нельзя его заменять на 1-е.
        places_count = max(places_count, self.instance.grave_number or 1)
        grave_choices = [(i,i) for i in range(1, places_count+1)]
        self.fields['grave_number'].widget = forms.Select(choices=grave_choices)

        if self.request.user.profile.is_loru():
            max_grave_number = self.fields['cemetery'].queryset.aggregate(m=Max('area__places_count'))['m']
            max_grave_choices = [(i,i) for i in range(1, max_grave_number+1)]
            self.fields['desired_graves_count'].widget = forms.Select(choices=max_grave_choices)
        else:
            del self.fields['desired_graves_count']
        
        loru_list = Org.objects.all()
        self.fields['applicant_organization'].queryset = loru_list
        self.fields['applicant_organization'].inactive_queryset = loru_list.filter(Q(profile__user__is_active=False) | Q(profile=None))
        self.fields['agent'].queryset = Profile.objects.filter(org__in=loru_list, is_agent=True).select_related('user')
        self.fields['dover'].queryset = Dover.objects.filter(agent__org__in=loru_list)

        self.fields.keyOrder.insert(self.fields.keyOrder.index('applicant_organization'), self.fields.keyOrder.pop(-1))
        if self.instance.pk and self.instance.applicant:
            self.initial['opf'] = 'person'
        else:
            self.initial['opf'] = 'org'

        if self.request.user.profile.is_ugh() and self.request.REQUEST.get('archive'):
            del self.fields['plan_date']
            del self.fields['plan_time']
        elif self.instance.is_archive() or self.instance.is_transferred():
            del self.fields['plan_date']
            del self.fields['plan_time']
        elif not self.instance.is_finished():
            del self.fields['fact_date']
            del self.fields['account_number']

        if self.instance:
            self.initial['burial_container'] = self.instance.burial_container
            self.initial['burial_type'] = self.instance.burial_type
        else:
            self.initial['burial_container'] = Burial.CONTAINER_COFFIN
            self.initial['burial_type'] = self.instance.Burial.BURIAL_NEW

        if not self.instance or not self.instance.cemetery:
            if self.request.user.profile.cemetery:
                self.initial['cemetery'] = self.request.user.profile.cemetery
        if not self.instance or not self.instance.area:
            if self.request.user.profile.area:
                self.initial['area'] = self.request.user.profile.area

        if self.instance and self.instance.is_finished() and self.instance.place:
            self.initial.update(
                cemetery=self.instance.place.cemetery,
                area=self.instance.place.area,
                row=self.instance.place.row,
                place_number=self.instance.place.place,
            )

        self.fields['area'].queryset = self.fields['area'].queryset.select_related('purpose')

        self.forms = self.construct_forms()

    def construct_forms(self):
        data = self.data or None
        deadman = self.instance and self.instance.deadman
        self.old_place = self.instance and self.instance.get_place()
        self.deadman_form = DeadPersonForm(request=self.request, data=data, prefix='deadman', instance=deadman)
        deadman_addr = deadman and deadman.address
        self.deadman_address_form = LocationForm(data=data, prefix='deadman-address', instance=deadman_addr)
        self.bfiles_form = BurialFilesForm(data=self.request.POST or None, files=self.request.FILES or None)
        try:
            dc = self.instance and self.instance.deadman and self.instance.deadman.deathcertificate
        except DeathCertificate.DoesNotExist:
            dc = None
        if not dc and deadman:
            dc = DeathCertificate(person=deadman)
        self.dc_form = DeathCertificateForm(self.request, data=data, prefix='deadman-dc', instance=dc)

        responsible = self.instance and self.instance.get_responsible()
        self.responsible_form = ResponsibleForm(data=data, prefix='responsible', instance=responsible)
        resp_addr = responsible and responsible.address
        self.responsible_address_form = LocationForm(data=data, prefix='responsible-address', instance=resp_addr)

        applicant = self.instance and self.instance.applicant
        applicant_form_initial = {}
        applicant_address_form_initial = {}
        applicant_id_form_initial = {}
        if not self.instance.pk and self.order and self.order.applicant:
            self.initial['opf'] = 'person'
            for f in AlivePersonForm.base_fields.keys():
                applicant_form_initial[f] = getattr(self.order.applicant, f)
            cust_address = self.order.applicant.address
            if cust_address:
                if cust_address.country:
                    applicant_address_form_initial['country_name'] = cust_address.country.name
                if cust_address.country:
                    applicant_address_form_initial['region_name'] = cust_address.region.name
                if cust_address.country:
                    applicant_address_form_initial['city_name'] = cust_address.city.name
                if cust_address.street:
                    applicant_address_form_initial['street_name'] = cust_address.street.name
                for f in ('post_index', 'house', 'block', 'building', 'flat', 'info', ):
                    applicant_address_form_initial[f] = getattr(cust_address, f)
            try:
                cust_personid = self.order.applicant.personid
            except PersonID.DoesNotExist:
                cust_personid = None
            if cust_personid:
                for f in PersonIDForm.base_fields.keys():
                    applicant_id_form_initial[f] = getattr(cust_personid, f)

        self.applicant_form = AlivePersonForm(data=data, prefix='applicant',
                                              instance=applicant,
                                              initial=applicant_form_initial,
                                             )
        applicant_addr = applicant and applicant.address
        self.applicant_address_form =  LocationForm(data=data, prefix='applicant-address',
                                                    instance=applicant_addr,
                                                    initial=applicant_address_form_initial,
                                                   )
        try:
            applicant_id = self.instance and self.instance.applicant and self.instance.applicant.personid
        except PersonID.DoesNotExist:
            applicant_id = None
        self.applicant_id_form = PersonIDForm(data=data, prefix='applicant-pid',
                                              instance=applicant_id,
                                              initial=applicant_id_form_initial
                                             )

        forms = [self.deadman_form, self.deadman_address_form, self.dc_form,
                self.responsible_form, self.responsible_address_form,
                self.applicant_form, self.applicant_address_form, self.applicant_id_form]
        
        # При ?action=.... метод is_valid() формы добавления файла, self.bfiles_form, возвращает
        # False.
        # Впрочем, форма добавления файла не требуется, если редактирование захоронения
        # вызывается не для правки его пользователем, а из просмотра захоронения,
        # с параметром ?action=.... "в строке браузера", чтоб сразу закрыть (complete)
        #
        if not self.request.REQUEST.get('action'):
            forms.append(self.bfiles_form)
        return forms

    def is_valid(self):
        return super(BurialForm, self).is_valid() and all([f.is_valid() for f in self.forms])

    def clean_plan_time(self):
        return self.cleaned_data['plan_time'] or None

    def clean(self):
        
        StrippedStringsMixin.clean(self)
        
        if self.cleaned_data.get('cemetery') and self.cleaned_data.get('area'):
            if self.cleaned_data['cemetery'] != self.cleaned_data['area'].cemetery:
                raise forms.ValidationError(_(u'Участок не от этого кладбища'))

        if self.request.user.profile.is_ugh():
            if self.cleaned_data.get('applicant_organization') and self.cleaned_data.get('agent'):
                if self.cleaned_data['applicant_organization'] != self.cleaned_data['agent'].org:
                    raise forms.ValidationError(_(u'Агент не от этого ЮЛ'))
            if self.cleaned_data.get('agent') and self.cleaned_data.get('dover'):
                if self.cleaned_data['agent'] != self.cleaned_data['dover'].agent:
                    raise forms.ValidationError(_(u'Доверенность не от этого Агента'))

            if not self.cleaned_data.get('applicant_organization') and self.cleaned_data.get('agent'):
                raise forms.ValidationError(_(u'Нельзя указать Агента без ЛОРУ'))
            if not self.cleaned_data.get('agent') and self.cleaned_data.get('dover'):
                raise forms.ValidationError(_(u'Нельзя указать Доверенность без Агента'))

            if self.cleaned_data.get('applicant_organization') and self.applicant_form.is_valid_data():
                raise forms.ValidationError(_(u"Нужно указать либо Заявителя-ЮЛ, либо Заявителя-ФЛ"))

            if self.cleaned_data.get('agent_director'):
                self.cleaned_data.update(agent=None, dover=None, )

        if self.responsible_form.is_valid():
            if self.responsible_form.cleaned_data.get('take_from') == ResponsibleForm.WHERE_FROM_APPLICANT:
                if self.cleaned_data.get('opf') != 'person':
                    raise forms.ValidationError(_(u"Невозможно указать Заявителя - Ответственного. Заявитель не ФЛ."))

        return self.cleaned_data

    def cemetery_placing_json(self):
        parents = {}
        if self.fields.get('cemetery'):
            for c in self.fields['cemetery'].queryset:
                parents[c.pk] = c.places_algo
        return mark_safe(json.dumps(parents))

    def get_prefix(self, form):
        prefix = u''
        if form is self.deadman_form:
            prefix = _(u"Усопший ")
        if form is self.deadman_address_form:
            prefix = _(u"Усопший, адрес ")
        if form is self.dc_form:
            prefix = _(u"Усопший, СоС, ")
        if form in [self.responsible_form, self.responsible_address_form]:
            prefix = _(u"Ответственный ")
        if form in [self.applicant_form, self.applicant_address_form, self.applicant_id_form]:
            prefix = _(u"Заявитель ")
        return prefix

    def save(self, commit=True, **kwargs):
        request = self.request
        self.collect_log_data()

        self.instance = super(BurialForm, self).save(commit=False)

        self.instance.changed = datetime.datetime.now()
        self.instance.changed_by = request.user

        if not self.instance.ugh:
            if request.user.profile.is_ugh():
                self.instance.ugh = request.user.profile.org
            elif self.instance.cemetery:
                self.instance.ugh = self.instance.cemetery.ugh

        if not self.instance.loru and request.user.profile.is_loru():
            self.instance.loru = request.user.profile.org

        if not self.instance.pk:
            if self.request.user.profile.is_loru():
                self.instance.source_type = Burial.SOURCE_FULL
            elif self.request.user.profile.is_ugh():
                if self.request.REQUEST.get('archive'):
                    self.instance.source_type = Burial.SOURCE_ARCHIVE
                else:
                    self.instance.source_type = Burial.SOURCE_UGH

        if self.deadman_form.is_valid() and self.instance.burial_container != Burial.CONTAINER_BIO:
            deadman = self.deadman_form.save(commit=False)
            if self.deadman_address_form.is_valid_data():
                # Хотя бы одно поле из адреса заполнено
                deadman.address = self.deadman_address_form.save()
            else:
                self.safe_delete('address', deadman)
            deadman.save()

            if self.dc_form.is_valid():
                dc = self.dc_form.save(commit=False)
                dc.person = deadman
                dc.save()
            self.instance.deadman = deadman
        else:
            self.safe_delete('deadman', self.instance)

        if self.cleaned_data.get('opf') == 'person' and self.applicant_form.is_valid_data():
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
            self.safe_delete('applicant', self.instance)

        remove_responsible = False
        if self.responsible_form.cleaned_data.get('take_from') == ResponsibleForm.WHERE_FROM_APPLICANT:
            self.instance.responsible = self.instance.applicant.deep_copy()
        elif self.responsible_form.is_valid():
            if self.responsible_form.cleaned_data.get('last_name').strip() or \
               self.responsible_form.cleaned_data.get('first_name').strip() or \
               self.responsible_form.cleaned_data.get('middle_name').strip():
                responsible = self.responsible_form.save(commit=False)
                if self.responsible_address_form.is_valid_data():
                    responsible.address = self.responsible_address_form.save()
                responsible.save()
                self.instance.responsible = responsible
            else:
                remove_responsible = True
        else:
            remove_responsible = True
        if remove_responsible:
            self.safe_delete('responsible', self.instance)

        if self.instance.is_closed() and \
            self.old_place and \
            (self.cleaned_data['cemetery'] != self.old_place.cemetery or \
             self.cleaned_data['area'] != self.old_place.area or \
             self.cleaned_data['row'] != self.old_place.row or \
             self.cleaned_data['place_number'] != self.old_place.place):
            place, created = Place.objects.get_or_create(cemetery=self.cleaned_data['cemetery'],
                                                         area=self.cleaned_data['area'],
                                                         row=self.cleaned_data['row'],
                                                         place=self.cleaned_data['place_number'],)
            self.instance.place=place
            if created:
                self.grave = place.create_graves(max(self.cleaned_data['area'].places_count or 1,
                                                     self.cleaned_data['grave_number'],
                                                    ),
                                                 self.cleaned_data['grave_number'],
                )
            # Пока не привязываем здесь могилу к захоронению, если место существует.
            # Это будет сделано ниже в self.instance.close(....)

        self.instance.save()
        if self.order:
            self.order.burial = self.instance
            self.order.save()

        if self.bfiles_form.is_valid() and self.request.FILES.get('bfile'):
            saved_file = self.bfiles_form.save(burial=self.instance, user=self.request.user)
            write_log(request, self.instance,
                     _(u'Добавлен файл'), "%s, %s" % (saved_file.comment, saved_file.original_name,)
            )

        if self.instance.is_closed():
            self.instance.close(old_place=self.old_place)

        self.put_log_data()

        order_parm = '?order=%s' % self.order.pk if self.order else ''
        url = 'view_burial' if request.user.profile.is_ugh() else 'edit_burial'
        msg = _(u"<a href='%s'>Захоронение %s</a> сохранено") % (
            reverse(url, args=[self.instance.pk]) + order_parm,
            self.instance.pk,
        )
        messages.success(self.request, msg)

        return self.instance

class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        exclude = ['responsible', ]

class BurialFilesForm(forms.ModelForm):
    class Meta:
        model = BurialFiles
        exclude = ['burial', 'date_of_creation', ]

    MAX_UPLOAD_SIZE_MB = 2

    def clean_comment(self):
        self.cleaned_data['comment'] = self.cleaned_data['comment'].strip()
        return self.cleaned_data['comment']

    def clean(self):
        cleaned_data = super(BurialFilesForm, self).clean()
        comment = cleaned_data['comment']
        bfile = cleaned_data['bfile']
        if comment and not bfile or not comment and bfile:
            raise forms.ValidationError(_(u'Надо задавать и файл, и описание; или ни файл, ни описание'))
        if bfile and bfile.size > self.MAX_UPLOAD_SIZE_MB * 2**20:
            raise forms.ValidationError(_(u'Превышен максимальный размер файла') + u", %s Мб." % self.MAX_UPLOAD_SIZE_MB)
        return cleaned_data

    def save(self, burial=None, user=None, commit=True, *args, **kwargs):
        burial_file_rec = super(BurialFilesForm, self).save(commit=False, *args, **kwargs)
        burial_file_rec.burial = burial
        burial_file_rec.creator = user
        if commit:
            burial_file_rec.save()
        return burial_file_rec

class BurialfileCommentEditForm(forms.ModelForm):
    class Meta:
        model = BurialFiles
        fields = ['comment', ]

    def clean_comment(self):
        self.cleaned_data['comment'] = self.cleaned_data['comment'].strip()
        if not self.cleaned_data['comment']:
            raise forms.ValidationError(_(u'Описание не может быть пустым'))
        return self.cleaned_data['comment']

class BurialCommitForm(BurialForm):
    def __init__(self, *args, **kwargs):
        super(BurialCommitForm, self).__init__(*args, **kwargs)

        self.mock_data()
        self.forms = self.construct_forms()

        self.setup_required()

    def form_to_data(self, form):
        data = {}
        for f in form.fields:
            k = form.prefix and '%s-%s' % (form.prefix, f) or f
            v = form.initial.get(f) or None
            if isinstance(v, models.Model):
                v = v.pk
            data.update({k:v})
        return data

    def setup_required(self):
        for f in self.fields:
            if f in ['cemetery', 'plan_date', 'plan_time',]:
                self.fields[f].required = True
        if self.request.user.profile.is_ugh():
            self.fields['area'].required = True

        if self.data.get('cemetery'):
            cemetery = self.data.get('cemetery')
            if not isinstance(cemetery, Cemetery):
                cemetery = Cemetery.objects.get(pk=cemetery)
        else:
            cemetery = self.instance.cemetery or None

        if self.instance.is_archive() and self.fields.get('fact_date'):
            self.fields['fact_date'].required = True

        if self.instance.is_finished():
            if cemetery and cemetery.places_algo == Cemetery.PLACE_MANUAL:
                self.fields['place_number'].required = True

        if self.instance.is_ugh() and self.instance.applicant_organization:
            if not self.instance.is_archive():
                for f in ['applicant_organization', 'agent', 'dover']:
                    self.fields[f].required = True

            if self.instance.agent_director or self.data.get('agent_director'):
                self.fields['dover'].required = False
                self.fields['agent'].required = False

        self.setup_required_deadman()
        self.setup_required_deadman_address()
        self.setup_required_deadman_dc()
        self.setup_required_responsible()
        self.setup_required_responsible_address()
        self.setup_required_applicant()
        self.setup_required_applicant_address()
        self.setup_required_applicant_id()

    def setup_required_deadman(self):
        pass

    def setup_required_deadman_address(self):
        pass

    def setup_required_deadman_dc(self):
        pass

    def setup_required_responsible(self):
        pass

    def setup_required_responsible_address(self):
        pass

    def setup_required_applicant(self):
        pass

    def setup_required_applicant_address(self):
        pass

    def setup_required_applicant_id(self):
        if self.data.get('applicant-last_name'):
            for f in self.applicant_id_form.fields:
                if f in ['id_type', 'series', 'number',]:
                    self.applicant_id_form.fields[f].required = True

    def clean(self):

        StrippedStringsMixin.clean(self)

        is_ugh = False
        if self.instance and self.instance.is_ugh():
            is_ugh = True
        if (not self.instance or not self.instance.pk) and self.request.user.profile.is_ugh():
            is_ugh = True
        if is_ugh:
            if not self.instance.is_archive() and not self.instance.is_transferred() and not self.request.REQUEST.get('archive'):
                if not self.cleaned_data.get('applicant_organization'):
                    if not self.applicant_form.is_valid_data():
                        raise forms.ValidationError(_(u"Нужно указать либо Заявителя-ЮЛ, либо Заявителя-ФЛ"))
                if self.cleaned_data.get('applicant_organization'):
                    if self.applicant_form.is_valid_data():
                        raise forms.ValidationError(_(u"Нужно указать либо Заявителя-ЮЛ, либо Заявителя-ФЛ"))

                if self.cleaned_data.get('opf') == 'person':
                    if not self.applicant_form.is_valid_data():
                        raise forms.ValidationError(_(u"Нужно указать Заявителя-ФЛ"))

                if self.cleaned_data.get('opf') == 'person':
                    if self.applicant_id_form.is_valid():
                        for field in ['series', 'number', ]:
                            if not self.applicant_id_form.cleaned_data.get(field):
                                raise forms.ValidationError(_(u"Не указаны серия и/или номер документа заявителя"))

                if self.cleaned_data.get('opf') == 'org':
                    if not self.cleaned_data.get('applicant_organization'):
                        raise forms.ValidationError(_(u"Нужно указать ЛОРУ"))
                    if not self.cleaned_data.get('agent_director'):
                        if not self.cleaned_data.get('agent') or not self.cleaned_data.get('dover'):
                            msg = _(u"Нужно указать Агента и Доверенность или указать, что Агент - Директор")
                            raise forms.ValidationError(msg)
                if  not self.instance.is_closed():
                    if self.cleaned_data.get('dover'):
                        dover_begin_date = self.cleaned_data.get('dover').begin
                        dover_end_date = self.cleaned_data.get('dover').end
                        today = datetime.datetime.today()
                        if dover_begin_date > today.date():
                            msg = _(u"Дата выдачи доверенности не может быть раньше текущей даты")
                            raise forms.ValidationError(msg)
                        if dover_end_date < today.date() :
                            msg = _(u"Срок действия доверенности не может быть меньше текущей даты")
                            raise forms.ValidationError(msg)

            if self.cleaned_data.get('opf') == 'person' and self.applicant_id_form.is_valid() and not self.instance.is_archive() and not self.instance.is_transferred():
                burial_date = self.cleaned_data.get('plan_date')
                document_date = self.applicant_id_form.cleaned_data.get('date')
                if burial_date and document_date:
                    check_date = datetime.datetime(burial_date.year - 75, burial_date.month, burial_date.day).date()
                    if document_date < check_date:
                        msg = _(u"Не верно указан номер документа")
                        raise forms.ValidationError(msg)

            if self.request.user.profile.org.numbers_algo in (Org.NUM_YEAR_UGH, Org.NUM_YEAR_CEMETERY) and \
               self.cleaned_data.get('account_number') and self.cleaned_data.get('fact_date'):
                acc_number = self.cleaned_data.get('account_number')
                fact_date  = self.cleaned_data.get('fact_date')
                msg = _(u"Номер в книге учета должен быть: ГГГГнн...н (год фактической даты, номер)")
                try:
                    if len(acc_number) < 4 or int(acc_number[:4]) != fact_date.year:
                        raise forms.ValidationError(msg)
                except ValueError:
                    raise forms.ValidationError(msg)

            if (self.instance.is_archive() or self.request.REQUEST.get('archive')) and \
               not self.cleaned_data.get('account_number').strip():
                msg = _(u"Нельзя закрывать архивное захоронение без указания его номера в книге учета")
                raise forms.ValidationError(msg)

        place_number = self.cleaned_data.get('place_number') or ''
        area = self.cleaned_data.get('area')
        row = self.cleaned_data.get('row')
        if not place_number.strip() and (self.instance.is_archive() or self.request.REQUEST.get('archive')):
            msg = _(u"Нельзя закрывать архивное захоронение без указания номера места")
            raise forms.ValidationError(msg)
        elif not place_number.strip() and area and area.availability == Area.AVAILABILITY_CLOSED:
            if is_ugh:
                msg = _(u"Не указано место для закрытого участка. Нельзя закрывать захоронение")
                raise forms.ValidationError(msg)
            elif self.request.REQUEST.get('ready'):
                msg = _(u"Не указано место для закрытого участка. Нельзя отправлять на согласование")
                raise forms.ValidationError(msg)
        elif (row.strip() or place_number.strip()) and not area:
            msg = _(u"Указан ряд и/или место, но не указан участок")
            raise forms.ValidationError(msg)

        cemetery = self.cleaned_data.get('cemetery')
        grave_number = self.cleaned_data.get('grave_number')
        place = None
        if cemetery and area and place_number:
            try:
                place = Place.objects.get(cemetery=cemetery, area=area, row=row, place=place_number)
            except Place.DoesNotExist:
                pass
        if place:
            if place.get_graves_count() < grave_number:
                msg = _(u"Номер могилы превышает максимальное количество в существующем месте")
                raise forms.ValidationError(msg)
        elif area and area.places_count  < grave_number:
            msg = _(u"Номер могилы превышает количество могил в месте для участка")
            raise forms.ValidationError(msg)

        if self.instance.is_closed() and not place_number.strip():
            raise forms.ValidationError(_(u"Не указан номер места закрытого захоронения"))

        cemetery = self.cleaned_data.get('cemetery')
        today = datetime.date.today()
        plan_date = self.cleaned_data.get('plan_date')
        if plan_date and today > plan_date and not self.instance.is_finished():
            if not self.instance.is_archive() and not self.request.REQUEST.get('archive'):
                msg = _(u"Плановая дата захоронения не может быть раньше текущей даты")
                raise forms.ValidationError(msg)

        if cemetery:
            if cemetery and cemetery.places_algo == Cemetery.PLACE_CEM_YEAR:
                place_number = self.cleaned_data.get('place_number')
                if place_number:
                    if not re.match(r'^\d{4}.+',place_number) or int(place_number[:4]) > today.year or not int(place_number[:4]):
                        raise forms.ValidationError(_(u"Номер места должен быть: ГГГГмм...м (год не больше текущего, место)"))

        deadman_birth_date = None
        deadman_death_date = None

        if self.deadman_form.is_valid_data():
            deadman_birth_date = self.deadman_form.cleaned_data.get("birth_date")
            if deadman_birth_date:
                deadman_birth_date = deadman_birth_date.d
            deadman_death_date = self.deadman_form.cleaned_data.get("death_date")
            if deadman_death_date:
                deadman_death_date = deadman_death_date.d
            if deadman_birth_date and deadman_death_date:
                if deadman_birth_date > deadman_death_date:
                    msg = _(u"Дата смерти не может быть раньше даты рождения")
                    raise forms.ValidationError(msg)
                from_death_150_years = datetime.datetime(deadman_birth_date.year - 150,  deadman_birth_date.month, deadman_birth_date.day).date()
                if deadman_birth_date < from_death_150_years :
                    msg = _(u"Не верно указаны даты жизни")
                    raise forms.ValidationError(msg)

            if deadman_death_date and deadman_death_date > today:
                msg = _(u"Дата смерти не может быть позже сегодняшней")
                raise forms.ValidationError(msg)
            if not self.instance.is_archive() and not self.instance.is_transferred():
                if plan_date and deadman_birth_date:
                    if deadman_birth_date > plan_date:
                        msg = _(u"Дата рождения не может быть позже даты захоронения")
                        raise forms.ValidationError(msg)
                if plan_date and deadman_death_date:
                    if deadman_death_date > plan_date:
                        msg = _(u"Дата смерти не может быть позже даты захоронения")
                        raise forms.ValidationError(msg)

        if self.dc_form.is_valid() and \
           not (self.instance.is_archive() or self.request.REQUEST.get('archive') or \
                self.instance.is_transferred() or \
                self.cleaned_data.get('burial_container') == Burial.CONTAINER_BIO \
               ):
            death_certificate_release_date = self.dc_form.cleaned_data.get('release_date')
            if not self.dc_form.cleaned_data.get("s_number").strip():
                raise forms.ValidationError(_(u"Не заполнен номер свидетельства о смерти"))
            if not death_certificate_release_date:
                raise forms.ValidationError(_(u"Не указана дата свидетельства о смерти"))
            if not self.dc_form.cleaned_data.get("zags"):
                raise forms.ValidationError(_(u"Не указан ЗАГС, выдавший свидетельство о смерти"))
            if deadman_birth_date:
                if deadman_birth_date > death_certificate_release_date:
                    msg = _(u"Дата выдачи свидетельства о смерти не может быть раньше даты рождения")
                    raise forms.ValidationError(msg)
            if deadman_death_date:
                if deadman_death_date> death_certificate_release_date:
                    msg = _(u"Дата выдачи свидетельства о смерти не может быть раньше даты смерти")
                    raise forms.ValidationError(msg)

        if self.responsible_form.is_valid():
            r_last_name = self.responsible_form.cleaned_data.get('last_name').strip()
            r_first_name = self.responsible_form.cleaned_data.get('first_name').strip()
            r_middle_name = self.responsible_form.cleaned_data.get('middle_name').strip()
            msg = ''
            if r_last_name:
                # Ф (+) И (-) О (-) : OK
                # Ф (+) И (-) О (+) : Bad :
                if not r_first_name and r_middle_name:
                    msg = _(u"Ответственный: не указано имя при указанном отчестве")
                # Ф (+) И (+) О (-) : OK
                # Ф (+) И (+) О (+) : OK
            else:
                # Ф (-) И (-) О (-) : OK
                # Ф (-) И (-) О (+) : Bad :
                if not r_first_name and r_middle_name:
                    msg = _(u"Ответственный: не указаны фамилия и имя при указанном отчестве")
                # Ф (-) И (+) О (-) : Bad
                elif r_first_name and not r_middle_name:
                    msg = _(u"Ответственный: не указана фамилия при указанном имени")
                # Ф (-) И (+) О (+) : Bad
                elif r_first_name and r_middle_name:
                    msg = _(u"Ответственный: не указана фамилия при указанных имени и отчестве")
            if msg:
                raise forms.ValidationError(msg)

            if self.request.REQUEST.get('ready') and self.dc_form.is_valid():
                death_date = self.deadman_form.cleaned_data.get('death_date')
                last_name = self.deadman_form.cleaned_data.get('last_name').strip()
                s_number = self.dc_form.cleaned_data.get('s_number').strip()
                if death_date and last_name and s_number:
                    first_name = self.deadman_form.cleaned_data.get('first_name').strip()
                    middle_name = self.deadman_form.cleaned_data.get('middle_name').strip()
                    query = Burial.objects.filter(
                                Q(ugh__loru_list__loru=self.request.user.profile.org) & \
                                Q(annulated=False) & \
                                Q(status__in = (Burial.STATUS_CLOSED, Burial.STATUS_APPROVED,))
                            )
                    query = query.filter(
                                deadman__last_name=last_name,
                                deadman__first_name=first_name,
                                deadman__middle_name=middle_name,
                                deadman__deathcertificate__s_number=s_number,
                                deadman__death_date__year=death_date.year,
                                deadman__death_date__month=death_date.month,
                                deadman__death_date__day=death_date.day,
                            )
                    if self.instance.pk:
                        query = query.exclude(pk=self.instance.pk)
                    if query:
                        raise forms.ValidationError(
                                _(u"Такой усопший уже есть (ФИО, дата смерти, свидетельство). Нельзя согласовывать")
                              )
                
        return self.cleaned_data

    def mock_data(self):
        if not self.data:
            self.data = {}
            self.data.update(self.form_to_data(self))
            for f in self.forms:
                self.data.update(self.form_to_data(f))

class BurialApproveCloseForm(ChildrenJSONMixin, LoggingFormMixin, forms.ModelForm):
    """
    Формируется при одобрении или закрытии электронного захоронения
    """
    class Meta:
        model = Burial
        fields = ['cemetery', 'area', 'row', 'place_number', 'fact_date', ]

    def __init__(self, request, *args, **kwargs):
        super(BurialApproveCloseForm, self).__init__(*args, **kwargs)
        self.forms = []
        self.request = request
        cemetery_qs = Q(ugh=request.user.profile.org)
        
        if self.data.get('cemetery'):
            cemetery = Cemetery.objects.get(pk=self.data.get('cemetery'))
        else:
            cemetery = self.instance.cemetery

        if self.instance.can_finish():
            # Закрытие
            if not self.instance.fact_date:
                self.initial['fact_date'] = self.instance.plan_date
            for f in self.fields:
                if f not in ['row', ]:
                    self.fields[f].required = True
            if cemetery and cemetery.places_algo != Cemetery.PLACE_MANUAL:
                self.fields['place_number'].required = False
            self.fields['cemetery'].queryset = Cemetery.objects.filter(cemetery_qs)

        elif self.instance.can_approve():
            # Одобрение
            for f in ['row', 'place_number', 'fact_date', ]:
                del self.fields[f]
            for f in ['cemetery', 'area', ]:
                self.fields[f].required = True
            cemetery_qs &= Q(area__availability=Area.AVAILABILITY_OPEN)
            self.fields['cemetery'].queryset = Cemetery.objects.filter(cemetery_qs).distinct()

    def clean_area(self):
        """
        Проверка одобрения захоронения только в открытый участок.
        """
        if self.instance.is_ready() and self.cleaned_data['area'].availability != Area.AVAILABILITY_OPEN:
            raise forms.ValidationError(_(u'Можно предлагать лишь открытый участок кладбища'))
        return self.cleaned_data['area']

    def is_valid(self):
        is_valid = super(BurialApproveCloseForm, self).is_valid()
        if not is_valid:
            messages.error(self.request, _(u'Обнаружены ошибки, их необходимо исправить'))
        return is_valid

    def save(self, **kwargs):
        self.collect_log_data()
        self.instance = super(BurialApproveCloseForm, self).save(**kwargs)
        self.put_log_data()
        return self.instance

class AddAgentForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['user_last_name','user_first_name', 'user_middle_name', ]

    def random_string(self):
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for x in range(10))

    def clean(self):
        cleaned_data = super(AddAgentForm, self).clean()
        if not cleaned_data['user_last_name'].strip():
            msg = _(u"Не заполнена фамилия")
            raise forms.ValidationError(msg)

        if cleaned_data['user_middle_name'].strip() and \
           not cleaned_data['user_first_name'].strip():
            msg = _(u"Не заполнено имя при имеющемся отчестве")
            raise forms.ValidationError(msg)
        return cleaned_data

    def save(self, commit=True, *args, **kwargs):
        loru = kwargs.pop('loru')
        profile = super(AddAgentForm, self).save(commit=False, *args, **kwargs)
        profile.org = loru
        profile.is_agent=True
        user = User()
        user.is_active = False
        user.email = loru.email or ''
        user.username = loru.email
        user.last_name = profile.user_last_name
        user.first_name = profile.user_first_name
        if profile.user_middle_name:
            user.first_name = user.first_name + ' ' + profile.user_middle_name
        while not user.username or User.objects.filter(username=user.username).exists():
            user.username = self.random_string()
        if commit:
            user.save() 
            profile.user = user 
            profile.save()
        return profile

class AddDoverForm(forms.ModelForm):
    class Meta:
        model = Dover
        exclude = ['agent', 'document', ]

    def clean(self):
        cleaned_data = super(AddDoverForm, self).clean()
        
        # Всплывающая форма. Если какое-то из обязательных полей не задано, то не будет,
        # как в "обычной" форме у поля сообщения "Обязательное поле". Просто не будет
        # никакой реакции. И имя незаполненного или неверно заполненного поля не будет в
        # cleaned_data.
        errors = []
        for field in ('begin', 'end', 'number', ):
            if field not in cleaned_data or \
               isinstance(self.cleaned_data[field], basestring) and not self.cleaned_data[field].strip():
                errors.append(u"%s : обязательное поле или неверно задано" % unicode(self.fields[field].label))
        if errors:
            raise forms.ValidationError("\n".join(errors))

        begin_date = cleaned_data['begin']
        end_date  = cleaned_data['end']
        number = cleaned_data['number']
        if begin_date > end_date:
            msg = _(u"Дата начала доверенности не может быть раньше даты окончания доверенности")
            raise forms.ValidationError(msg)

        today = datetime.date.today()
        if today > end_date:
            msg = _(u"Дата окончания доверенности не может быть раньше текущей даты")
            raise forms.ValidationError(msg)

        if not number.strip():
            msg = _(u"Пустое поле номера")
            raise forms.ValidationError(msg)
        
        return cleaned_data

class AddOrgForm(BaseOrgForm):
    class Meta:
        model = Org
        exclude = ['off_address', 'numbers_algo', ]
    
    def __init__(self, request, *args, **kwargs):
        super(AddOrgForm, self).__init__(request, *args, **kwargs)
        choices = []
        for profile_type in Org.PROFILE_TYPES:
            if request.user.profile.is_ugh():
                if profile_type[0] in (Org.PROFILE_LORU, Org.PROFILE_ZAGS, Org.PROFILE_COMPANY, ):
                    choices.append(profile_type)
            elif request.user.profile.is_loru():
                if profile_type[0] in (Org.PROFILE_ZAGS, Org.PROFILE_COMPANY, ):
                    choices.append(profile_type)
            else:
                if profile_type[0] in (Org.PROFILE_ZAGS, ):
                    choices.append(profile_type)
        label = self.fields['type'].label
        self.fields['type'] = forms.fields.TypedChoiceField(choices=choices)
        self.fields['type'].label = label
        for field in ('name', 'full_name', 'inn', 'director', ):
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super(AddOrgForm, self).clean()
        errors = []
        for field in ('name', 'full_name', 'inn', 'director', ):
            # Нюанс django: Если clean_FIELD raises an exception,
            # то FIELD не будет в cleaned_data, а здесь вызывается
            # clean_inn родительского класса (OrgForm)
            if field in cleaned_data and not cleaned_data[field].strip():
                errors.append(u"%s : обязательное поле" % unicode(self.fields[field].label))
        if errors:
            raise forms.ValidationError("\n".join(errors))
        return cleaned_data

    def save(self, commit=True):
        self.collect_log_data()
        org = super(AddOrgForm, self).save(commit=False)
        if commit:
            org.save()
            self.put_log_data(msg=_(u'Добавлена организация'))
        return org

class AddDocTypeForm(forms.ModelForm):
    class Meta:
        model = IDDocumentType

class ExhumationForm(ChildrenJSONMixin, SafeDeleteMixin, forms.ModelForm):
    opf = forms.ChoiceField(label=_(u'ОПФ'), choices=OPF_CHOICES, widget=forms.RadioSelect, initial='person')

    class Meta:
        model = ExhumationRequest
        exclude = ['plan_date', 'plan_time']

    def __init__(self, request, burial, *args, **kwargs):
        super(ExhumationForm, self).__init__(*args, **kwargs)
        self.request = request
        self.burial = burial

        self.fields.keyOrder.insert(0, self.fields.keyOrder.pop(-1))

        if self.instance.applicant:
            self.initial['opf'] = 'person'
        else:
            self.initial['opf'] = 'org'

        if burial.cemetery and burial.cemetery.time_slots and self.fields.get('plan_time'):
            choices = [('', '----------')] + burial.cemetery.get_time_choices(
                date=burial.plan_date,
                request=self.request,
            )
            self.fields['plan_time'].widget = forms.Select(choices=choices)
        if self.instance.plan_time:
            self.initial['plan_time'] = self.instance.plan_time.strftime('%H:%M')

        # Отсутствие выбора будет в выпадающем списке не "---", а ""
        self.fields['applicant_organization'].empty_label = ''

        self.forms = self.construct_forms()

    def is_valid(self):
        return super(ExhumationForm, self).is_valid() and all([f.is_valid() for f in self.forms])

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

    def clean(self):
        exhumation_date = self.cleaned_data.get('fact_date')
        burial_date = self.burial.fact_date
        if burial_date and exhumation_date:
            if burial_date.d > exhumation_date:
                raise forms.ValidationError(_(u"Дата эксгумации не может быть раньше даты захоронения"))
        if self.cleaned_data.get('opf') == 'org':
            if not (self.cleaned_data.get('agent_director') or \
                    self.cleaned_data.get('agent') and self.cleaned_data.get('dover')):
                raise forms.ValidationError(_(u'Нет данных об агенте и/или доверенности для заявителя-ЮЛ. Изменения не сохранены'))
        else:
            if not self.applicant_form.is_valid_data():
                raise forms.ValidationError(_(u"Нужно указать Заявителя-ФЛ"))
        return self.cleaned_data

    def save(self, commit=True, *args, **kwargs):
        self.instance = super(ExhumationForm, self).save(commit=False, *args, **kwargs)

        self.instance.burial = self.burial
        self.instance.place = self.burial.place

        if self.cleaned_data.get('opf') == 'person' and self.applicant_form.is_valid_data():
            applicant = self.applicant_form.save(commit=False)
            if self.applicant_address_form.is_valid_data():
                applicant.address = self.applicant_address_form.save()
            applicant.save()

            if self.applicant_id_form.is_valid_data():
                pid = self.applicant_id_form.save(commit=False)
                pid.person = applicant
                pid.save()
            self.instance.applicant = applicant
            self.instance.applicant_organization = None
        else:
            self.safe_delete('applicant', self.instance)

        self.instance.save()

        return self.instance

class AreaMergeForm(forms.Form):
    correct = forms.ModelChoiceField(queryset=Area.objects.none(), required=True, label=_(u"Правильный"))
    incorrect = forms.ModelChoiceField(queryset=Area.objects.none(), required=True, label=_(u"Неправильный"))

    def __init__(self, cemetery, *args, **kwargs):
        super(AreaMergeForm, self).__init__(*args, **kwargs)
        self.fields['correct'].queryset = Area.objects.filter(cemetery=cemetery)
        self.fields['incorrect'].queryset = Area.objects.filter(cemetery=cemetery)

    def save(self):
        if self.cleaned_data['incorrect'] != self.cleaned_data['correct']:
            Place.objects.filter(area=self.cleaned_data['incorrect']).update(area=self.cleaned_data['correct'])
            Burial.objects.filter(area=self.cleaned_data['incorrect']).update(area=self.cleaned_data['correct'])
            self.cleaned_data['incorrect'].delete()
