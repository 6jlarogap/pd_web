# coding=utf-8
import copy
import datetime
import json
import random
import string

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

from burials.models import Cemetery, Area, Burial, Place, ExhumationRequest
from geo.forms import LocationForm
from orders.models import Order
from pd.forms import PartialFormMixin, ChildrenJSONMixin, LoggingFormMixin
from persons.forms import DeadPersonForm, DeathCertificateForm, AlivePersonForm, PersonIDForm
from persons.models import DeathCertificate, PersonID, IDDocumentType
from users.forms import OrgForm
from users.models import Org, Profile, Dover


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
        self.address_form.fields['country_name'].required = True
        if self.instance and self.instance.pk:
            self.area_formset = AreaFormset(data=self.data or None, instance=self.instance, queryset=Area.objects.order_by('name'))
        else:
            self.area_formset = None

    def is_valid(self):
        return super(CemeteryForm, self).is_valid() and self.address_form.is_valid_data() and (not self.area_formset or self.area_formset.is_valid())

    def save(self, commit=True, *args, **kwargs):
        obj = super(CemeteryForm, self).save(commit=False, *args, **kwargs)
        if obj.pk and self.area_formset:
            self.area_formset.save()
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
                    msg = _(u'Участок %s с <a href="/burials/?area=%s" target="_blank">Захоронениями</a> удалить нельзя, обратитесь в <a href="#">службу поддержки</a>')
                    raise forms.ValidationError(mark_safe(msg % (df.instance.name, df.instance.name)))

AreaFormset = inlineformset_factory(Cemetery, Area, formset=BaseAreaFormset, can_delete=True)

class PlaceEditForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = ['places_count']

    def __init__(self, *args, **kwargs):
        super(PlaceEditForm, self).__init__(*args, **kwargs)
        if not self.instance.places_count:
            if self.instance.area:
                self.initial['places_count'] = self.instance.area.places_count
            else:
                self.initial['places_count'] = 1

    def clean_places_count(self):
        burials = self.instance.burial_set.exclude(status=Burial.STATUS_EXHUMATED)
        max_num = burials.aggregate(max=Max('grave_number')).get('max') or 1
        if self.cleaned_data['places_count'] < max_num:
            raise forms.ValidationError(_(u"Нельзя установить меньше %s, столько могил уже занято") % max_num)
        return self.cleaned_data['places_count']

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
    applicant_org = forms.CharField(required=False, max_length=30, label=_(u"Заявитель-ЮЛ"))
    applicant_person = forms.CharField(required=False, max_length=30, label=_(u"Заявитель-ФЛ"))
    responsible = forms.CharField(required=False, max_length=30, label=_(u"Ответственный"))
    operation = forms.ChoiceField(required=False, choices=EMPTY + Burial.BURIAL_TYPES, label=_(u"Услуга"))
    cemetery = forms.CharField(required=False, label=_(u"Кладбища"))
    area = forms.CharField(required=False, label=_(u"Участок"))
    row = forms.CharField(required=False, label=_(u"Ряд"))
    place = forms.CharField(required=False, label=_(u"Место"))
    no_responsible = forms.BooleanField(required=False, initial=False, label=_(u"Без отв."))
    source = forms.TypedChoiceField(required=False, label=_(u"Тип"), choices=EMPTY + Burial.SOURCE_TYPES)
    status = forms.TypedChoiceField(required=False, label=_(u"Статус"), choices=EMPTY + Burial.STATUS_CHOICES)
    per_page = forms.ChoiceField(label=_(u"На странице"), choices=PAGE_CHOICES, initial=25, required=False)
    burial_container = forms.TypedChoiceField(required=False, label=_(u"Тип захоронения"), choices=EMPTY + Burial.BURIAL_CONTAINERS)

class ResponsibleForm(AlivePersonForm):
    WHERE_FROM_PLACE = u'place'
    WHERE_FROM_ORDER = u'order'
    WHERE_FROM_APPLICANT = u'applicant'
    WHERE_NEW = u'new'
    WHERE_CHOICES = (
        (WHERE_FROM_PLACE, _(u'Существующий (из места)')),
        (WHERE_FROM_ORDER, _(u'Заказчик (из Счет-Заказа)')),
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

    def set_loru_from(self):
        if 'take_from' in self.fields:
            all_choices = self.WHERE_CHOICES
            new_choices = [c for c in all_choices if c[0] != self.WHERE_FROM_APPLICANT]

            if self.initial.get('order'):
                order = self.initial.get('order')
                if not isinstance(order, Order):
                    try:
                        order = Order.objects.get(pk=self.initial['order'])
                    except Order.DoesNotExist:
                        order = None

                if order and not order.applicant:
                    new_choices = [c for c in new_choices if c[0] != self.WHERE_FROM_ORDER]

            self.fields['take_from'].choices = new_choices
            self.fields['take_from'].widget.choices = new_choices

    def set_ugh_from(self):
        if 'take_from' in self.fields:
            all_choices = self.WHERE_CHOICES
            new_choices = [c for c in all_choices if c[0] != self.WHERE_FROM_ORDER]
            self.fields['take_from'].choices = new_choices
            self.fields['take_from'].widget.choices = new_choices

    def clean(self):
        if self.cleaned_data.get('take_from') == self.WHERE_FROM_ORDER:
            if not self.cleaned_data.get('order'):
                raise forms.ValidationError(_(u'Нет Заказа'))
            if not self.cleaned_data.get('order').applicant:
                raise forms.ValidationError(_(u'Нет Закачика-ФЛ'))
        if self.cleaned_data.get('take_from') == self.WHERE_FROM_PLACE:
            if not self.cleaned_data.get('place'):
                raise forms.ValidationError(_(u'Нет Места'))
            if not self.cleaned_data.get('place').responsible:
                raise forms.ValidationError(_(u'Нет Ответственного у Места'))
        return self.cleaned_data

    def save(self, *args, **kwargs):
        if self.instance.pk:
            return super(ResponsibleForm, self).save(*args, **kwargs)
        elif self.cleaned_data.get('take_from') == self.WHERE_FROM_ORDER:
            a = copy.deepcopy(self.cleaned_data['order'].applicant)
            a.id = None
            a.baseperson_ptr_id = None
            a.save(force_insert=True)
            return a
        elif self.cleaned_data.get('take_from') == self.WHERE_FROM_PLACE:
            a = copy.deepcopy(self.cleaned_data['place'].responsible)
            a.id = None
            a.baseperson_ptr_id = None
            a.save(force_insert=True)
            return a
        else:
            return super(ResponsibleForm, self).save(*args, **kwargs)

    def is_valid_data(self):
        if self.is_valid():
            return self.cleaned_data.get('last_name') or self.cleaned_data.get('take_from') != self.WHERE_NEW
        else:
            return False

class BurialForm(PartialFormMixin, ChildrenJSONMixin, LoggingFormMixin, forms.ModelForm):
    COFFIN = 'coffin'
    URN = 'urn'

    burial_container = forms.ChoiceField(label=_(u"Тип захоронения"), choices=Burial.BURIAL_CONTAINERS, widget=forms.RadioSelect,  required=False)
    opf = forms.ChoiceField(label=_(u'ОПФ'), choices=OPF_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = Burial
        exclude = ['place', 'deadman', 'responsible', 'applicant', 'burial_type', ]

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

        places_count = 1
        if self.instance.place_number and self.instance.get_place() and self.instance.grave_number:
            places_count = self.instance.get_place().get_places_count()
        grave_choices = [(i,i) for i in range(1, places_count+1)]
        self.fields['grave_number'].widget = forms.Select(choices=grave_choices)

        if self.request.user.profile.is_loru():
            del self.fields['applicant_organization']
            del self.fields['agent']
            del self.fields['agent_director']
            del self.fields['dover']
            del self.fields['opf']

        if self.request.user.profile.is_ugh() or self.instance.is_ugh_only():
            ugh = self.request.user.profile.org
            loru_list = Org.objects.all()
            self.fields['applicant_organization'].queryset = loru_list
            self.fields['agent'].queryset = Profile.objects.filter(org__in=loru_list, is_agent=True).select_related('user')
            self.fields['dover'].queryset = Dover.objects.filter(agent__org__in=loru_list)

            self.fields.keyOrder.insert(self.fields.keyOrder.index('applicant_organization'), self.fields.keyOrder.pop(-1))
            if self.instance.pk and self.instance.applicant and self.instance.is_ugh():
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
        else:
            self.initial['burial_container'] = Burial.CONTAINER_COFFIN

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
        try:
            dc = self.instance and self.instance.deadman and self.instance.deadman.deathcertificate
        except DeathCertificate.DoesNotExist:
            dc = None
        if not dc and deadman:
            dc = DeathCertificate(person=deadman)
        self.dc_form = DeathCertificateForm(self.request, data=data, prefix='deadman-dc', instance=dc)

        responsible = self.instance and self.instance.get_responsible()
        resp_initial = {'order': self.instance.order or self.request.REQUEST.get('order')}
        self.responsible_form = ResponsibleForm(data=data, prefix='responsible', instance=responsible,
                                                initial=resp_initial)
        resp_addr = responsible and responsible.address
        self.responsible_address_form = LocationForm(data=data, prefix='responsible-address', instance=resp_addr)

        if self.request.user.profile.is_ugh():
            self.responsible_form.set_ugh_from()
        elif self.request.user.profile.is_loru():
            self.responsible_form.set_loru_from()

        applicant = self.instance and self.instance.applicant
        self.applicant_form = AlivePersonForm(data=data, prefix='applicant', instance=applicant)
        applicant_addr = applicant and applicant.address
        self.applicant_address_form =  LocationForm(data=data, prefix='applicant-address', instance=applicant_addr)
        try:
            applicant_id = self.instance and self.instance.applicant and self.instance.applicant.personid
        except PersonID.DoesNotExist:
            applicant_id = None
        self.applicant_id_form = PersonIDForm(data=data, prefix='applicant-pid', instance=applicant_id)

        if self.request.user.profile.is_loru():
            return [self.deadman_form, self.deadman_address_form, self.dc_form,
                    self.responsible_form, self.responsible_address_form]
        else:
            return [self.deadman_form, self.deadman_address_form, self.dc_form,
                    self.responsible_form, self.responsible_address_form,
                    self.applicant_form, self.applicant_address_form, self.applicant_id_form]

    def is_valid(self):
        return super(BurialForm, self).is_valid() and all([f.is_valid() for f in self.forms])

    def clean_plan_time(self):
        return self.cleaned_data['plan_time'] or None

    def clean(self):
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
                raise forms.ValidationError(_(u"Нужно указать только либо Заявителя-ЮЛ, либо Заявителя-ФЛ"))

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
        if form in [self.deadman_form, self.deadman_address_form, self.dc_form]:
            prefix = _(u"Усопший ")
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

        if not self.instance.pk:
            if self.request.user.profile.is_loru():
                self.instance.applicant_organization = self.request.user.profile.org
                self.instance.source_type = Burial.SOURCE_FULL
            elif self.request.user.profile.is_ugh():
                if self.request.REQUEST.get('archive'):
                    self.instance.source_type = Burial.SOURCE_ARCHIVE
                else:
                    self.instance.source_type = Burial.SOURCE_UGH

        if self.deadman_form.is_valid():
            deadman = self.deadman_form.save(commit=False)
            if self.deadman_address_form.is_valid_data():
                deadman.address = self.deadman_address_form.save()
            deadman.save()

            if self.dc_form.is_valid_data():
                dc = self.dc_form.save(commit=False)
                dc.person = deadman
                dc.save()
            self.instance.deadman = deadman
        else:
            try:
                self.instance.deadman.delete()
            except (AttributeError, ProtectedError):
                pass
            self.instance.deadman = None

        if self.request.user.profile.is_ugh():
            if self.cleaned_data.get('opf') == 'person':
                if self.applicant_form.is_valid_data():
                    applicant = self.applicant_form.save(commit=False)
                    if self.applicant_address_form.is_valid():
                        applicant.address = self.applicant_address_form.save()
                    applicant.save()

                    if self.applicant_id_form.is_valid():
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

        if self.request.user.profile.is_ugh() and self.responsible_form.cleaned_data.get('take_from') == ResponsibleForm.WHERE_FROM_APPLICANT:
            resp = copy.deepcopy(self.instance.applicant)
            resp.id = None
            resp.baseperson_ptr_id = None
            resp.save(force_insert=True)
            self.instance.responsible = resp
        elif self.responsible_form.is_valid():
            responsible = self.responsible_form.save(commit=False)
            if self.responsible_address_form.is_valid():
                responsible.address = self.responsible_address_form.save()
            responsible.save()
            self.instance.responsible = responsible
        else:
            try:
                self.instance.responsible.delete()
            except (AttributeError, ProtectedError):
                pass
            self.instance.responsible = None

        if self.cleaned_data['burial_container'] == Burial.CONTAINER_URN:
            self.instance.burial_type = Burial.BURIAL_URN
        elif self.instance.place_number:
            self.instance.burial_type = Burial.BURIAL_ADD
        else:
            self.instance.burial_type = Burial.BURIAL_NEW

        self.instance.save()

        if self.instance.is_closed():
            self.instance.close(old_place=self.old_place)

        self.put_log_data()

        msg = _(u"<a href='%s'>Захоронение %s</a> сохранено") % (
            reverse('view_burial', args=[self.instance.pk]),
            self.instance.pk,
        )
        messages.success(self.request, msg)

        return self.instance

class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        exclude = ['responsible', ]

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
            if f in ['cemetery', 'area', 'plan_date', 'plan_time']:
                self.fields[f].required = True

        if self.data.get('cemetery'):
            cemetery = self.data.get('cemetery')
            if not isinstance(cemetery, Cemetery):
                cemetery = Cemetery.objects.get(pk=cemetery)
        else:
            cemetery = self.instance and self.instance.cemetery or None

        if self.instance.is_archive() and self.fields.get('fact_date'):
            self.fields['fact_date'].required = True

        if self.instance.is_finished():
            if cemetery and cemetery.places_algo == Cemetery.PLACE_MANUAL:
                self.fields['place_number'].required = True

        if self.instance and self.instance.is_ugh() and self.instance.applicant_organization:
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
        #
        # Установка обязательности полей свидетельства о смерти (СоС)
        # при закрытии захоронения.
        # - если захоронение архивное или перенесенное, то проверка обязательности
        #   не производится, т.е. можно заполнить или все поля СоС, или некоторые,
        #   или не заполнять СоС вообще;
        # - для остальных захоронений обязательность полей СоС имеет смысл
        #   только если усопший известен, т.е. если заполнено поле фамилии в форме;
        #   * в этом случае проверяется, заполнено ли хотя бы одно из полей СоС.
        #     Если заполнено, то обязательны все поля СоС, кроме серии.
        #
        if self.instance.is_archive() or self.request.REQUEST.get('archive') or self.instance.is_transferred():
            return
        if self.data.get('deadman-last_name'):
            if any([True for k,v in self.data.items() if v and k.startswith(self.dc_form.prefix)]):
                for f in self.dc_form.fields:
                    if f != 'series':
                        self.dc_form.fields[f].required = True

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
        is_ugh = False
        if self.instance and self.instance.is_ugh():
            is_ugh = True
        if (not self.instance or not self.instance.pk) and self.request.user.profile.is_ugh():
            is_ugh = True
        if is_ugh:
            if not self.instance.is_archive() and not self.instance.is_transferred():
                if not self.cleaned_data.get('applicant_organization'):
                    if not self.applicant_form.is_valid_data():
                        raise forms.ValidationError(_(u"Нужно указать либо Заявителя-ЮЛ, либо Заявителя-ФЛ"))
                if self.cleaned_data.get('applicant_organization'):
                    if self.applicant_form.is_valid_data():
                        raise forms.ValidationError(_(u"Нужно указать либо Заявителя-ЮЛ, либо Заявителя-ФЛ"))

                if self.cleaned_data.get('opf') == 'person':
                    if not self.applicant_form.is_valid_data():
                        raise forms.ValidationError(_(u"Нужно указать Заявителя-ФЛ"))

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

            if self.cleaned_data.get('account_number') and self.cleaned_data.get('fact_date'):
                acc_number = self.cleaned_data.get('account_number')
                fact_date  = self.cleaned_data.get('fact_date')
                if len(acc_number) < 4 or int(acc_number[:4]) != fact_date.year:
                    msg = _(u"Не верный номер в книге учета")
                    raise forms.ValidationError(msg)

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
                    if len(place_number) < 4 or int(place_number[:4]) > today.year:
                        raise forms.ValidationError(_(u"Неверно указан номер места"))

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

        if not self.instance.is_archive() and not self.instance.is_transferred():
            if self.dc_form.is_valid():
                death_certificate_release_date = self.dc_form.cleaned_data.get('release_date')
                if deadman_birth_date and death_certificate_release_date:
                    if deadman_birth_date > death_certificate_release_date:
                        msg = _(u"Дата выдачи свидетельства о смерти не может быть раньше даты рождения")
                        raise forms.ValidationError(msg)
                if deadman_death_date and death_certificate_release_date:
                    if deadman_death_date> death_certificate_release_date:
                        msg = _(u"Дата выдачи свидетельства о смерти не может быть раньше даты смерти")
                        raise forms.ValidationError(msg)

        return self.cleaned_data

    def mock_data(self):
        if not self.data:
            self.data = {}
            self.data.update(self.form_to_data(self))
            for f in self.forms:
                self.data.update(self.form_to_data(f))

class BurialCloseForm(ChildrenJSONMixin, LoggingFormMixin, forms.ModelForm):
    class Meta:
        model = Burial
        fields = ['cemetery', 'area', 'row', 'place_number', 'fact_date', ]

    def __init__(self, request, *args, **kwargs):
        super(BurialCloseForm, self).__init__(*args, **kwargs)
        if not self.instance.fact_date:
            self.initial['fact_date'] = self.instance.plan_date
        for f in self.fields:
            if f not in ['row', ]:
                self.fields[f].required = True

        if self.data.get('cemetery'):
            cemetery = Cemetery.objects.get(pk=self.data.get('cemetery'))
        else:
            cemetery = self.instance.cemetery

        if cemetery and cemetery.places_algo != Cemetery.PLACE_MANUAL:
            self.fields['place_number'].required = False

        self.fields['cemetery'].queryset = Cemetery.objects.filter(ugh=request.user.profile.org)
        self.forms = []
        self.request = request

    def save(self, **kwargs):
        self.collect_log_data()
        self.instance = super(BurialCloseForm, self).save(**kwargs)
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

class AddOrgForm(OrgForm):
    class Meta:
        model = Org
        exclude = ['type', 'off_address', ]

class AddDocTypeForm(forms.ModelForm):
    class Meta:
        model = IDDocumentType

class ExhumationForm(ChildrenJSONMixin, forms.ModelForm):
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
        if self.cleaned_data.get('applicant_organization') and self.cleaned_data.get('applicant'):
            raise forms.ValidationError(_(u'Необходимо указать только одного заявителя'))
        if not self.cleaned_data.get('applicant_organization') and not self.cleaned_data.get('applicant'):
            raise forms.ValidationError(_(u'Необходимо указать заявителя'))
        exhumation_date = self.cleaned_data.get('fact_date')
        burial_date = self.burial.fact_date
        if burial_date and exhumation_date:
            if burial_date.d > exhumation_date:
                raise forms.ValidationError(_(u"Дата эксгумации не может быть раньше даты захоронения"))
        if self.cleaned_data.get('opf') == 'org' and \
                not self.cleaned_data.get('agent_director') and \
                not (self.cleaned_data.get('agent') and self.cleaned_data.get('dover')):
            raise forms.ValidationError(_(u'Нет данных об агенте и/или доверенности для заявителя-ЮЛ'))
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
            try:
                self.instance.applicant.delete()
            except (AttributeError, ProtectedError):
                pass
            self.instance.applicant = None

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
