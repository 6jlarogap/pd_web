# coding=utf-8
import datetime
from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from burials.models import Cemetery, Area, Burial, Place
from django.db.models.query_utils import Q
from geo.forms import LocationForm
from logs.models import write_log
from persons.forms import DeadPersonForm, DeathCertificateForm, AlivePersonForm, PersonIDForm
from persons.models import DeathCertificate, PersonID
from users.models import Org, Profile


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

class CemeteryAdminForm(BaseCemeteryForm):
    class Meta:
        model = Cemetery

AreaFormset = inlineformset_factory(Cemetery, Area, can_delete=False)

class BurialSearchForm(forms.Form):
    """
    Форма поиска на главной странице.
    """
    fio = forms.CharField(required=False, max_length=100, label=_(u"ФИО"))
    no_last_name = forms.BooleanField(required=False, initial=False, label=_(u"Неизв."))
    birth_date_from = forms.DateField(required=False, label=_(u"Дата рожд. с"))
    birth_date_to = forms.DateField(required=False, label=_(u"по"))
    death_date_from = forms.DateField(required=False, label=_(u"Дата смерти с"))
    death_date_to = forms.DateField(required=False, label=_(u"по"))
    burial_date_from = forms.DateField(required=False, label=_(u"Дата захор. с"))
    burial_date_to = forms.DateField(required=False, label=_(u"по"))
    responsible = forms.CharField(required=False, max_length=30, label=_(u"Ответственный"))
    operation = forms.ChoiceField(required=False, choices=Burial.BURIAL_TYPES, label=_(u"Услуга"))
    cemetery = forms.CharField(required=False, label=_(u"Кладбища"))
    area = forms.CharField(required=False, label=_(u"Участок"))
    row = forms.CharField(required=False, label=_(u"Ряд"))
    place = forms.CharField(required=False, label=_(u"Место"))
    no_responsible = forms.BooleanField(required=False, initial=False, label=_(u"Без отв."))

class BurialForm(forms.ModelForm):
    class Meta:
        model = Burial
        exclude = ['place', 'deadman', 'responsible', 'applicant', ]

    def __init__(self, request, *args, **kwargs):
        super(BurialForm, self).__init__(*args, **kwargs)
        self.request = request
        self.fields['cemetery'].queryset = Cemetery.objects.filter(
            Q(ugh__isnull=True) |
            Q(ugh__loru_list__loru=self.request.user.profile.org) |
            Q(ugh=self.request.user.profile.org)
        ).distinct()
        if self.instance and self.instance.cemetery and self.instance.cemetery.time_slots:
            choices = [('', '')] + self.instance.cemetery.get_time_choices(date=self.instance.plan_date)
            self.fields['plan_time'].widget = forms.Select(choices=choices)
        if self.instance and self.instance.plan_time:
            self.initial['plan_time'] = self.instance.plan_time.strftime('%H:%M')
        else:
            self.fields['plan_date'].initial = datetime.date.today() + datetime.timedelta(1)

        if self.request.user.profile.is_loru():
            del self.fields['loru']
            del self.fields['agent']

        if self.request.user.profile.is_ugh():
            ugh = self.request.user.profile.org
            loru_list = Org.objects.filter(type=Org.PROFILE_LORU, ugh_list__ugh=ugh)
            self.fields['loru'].queryset = loru_list
            self.fields['agent'].queryset = Profile.objects.filter(org__in=loru_list, is_agent=True)

        if not self.request.user.profile.is_ugh() or not self.request.REQUEST.get('archive'):
            del self.fields['fact_date']
        else:
            del self.fields['plan_date']
            del self.fields['plan_time']

        self.forms = self.construct_forms()

    def construct_forms(self):
        data = self.data or None
        deadman = self.instance and self.instance.deadman
        self.deadman_form = DeadPersonForm(data=data, prefix='deadman', instance=deadman)
        deadman_addr = self.instance and self.instance.deadman and self.instance.deadman.address
        self.deadman_address_form = LocationForm(data=data, prefix='deadman-address', instance=deadman_addr)
        try:
            dc = self.instance and self.instance.deadman and self.instance.deadman.deathcertificate
        except DeathCertificate.DoesNotExist:
            dc = None
        self.dc_form = DeathCertificateForm(data=data, prefix='deadman-dc', instance=dc)

        responsible = self.instance and self.instance.responsible
        self.responsible_form = AlivePersonForm(data=data, prefix='responsible', instance=responsible)
        resp_addr = self.instance and self.instance.responsible and self.instance.responsible.address
        self.responsible_address_form =  LocationForm(data=data, prefix='responsible-address', instance=resp_addr)

        applicant = self.instance and self.instance.applicant
        self.applicant_form = AlivePersonForm(data=data, prefix='applicant', instance=applicant)
        applicant_addr = self.instance and self.instance.applicant and self.instance.applicant.address
        self.applicant_address_form =  LocationForm(data=data, prefix='applicant-address', instance=applicant_addr)
        try:
            applicant_id = self.instance and self.instance.applicant and self.instance.applicant.personid
        except PersonID.DoesNotExist:
            applicant_id = None
        self.applicant_id_form = PersonIDForm(data=data, prefix='applicant-pid', instance=applicant_id)

        is_archive = self.request.REQUEST.get('archive') or self.instance and self.instance.is_archive()
        if self.request.user.profile.is_loru() or is_archive:
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
        if self.cleaned_data.get('loru') and self.cleaned_data.get('agent'):
            if self.cleaned_data['loru'] != self.cleaned_data['agent'].org:
                raise forms.ValidationError(_(u'Агент не от этого ЛОРУ'))
        return self.cleaned_data

    def save(self, commit=True, **kwargs):
        request = self.request
        changed_data = []
        obj = self.instance
        if obj and obj.pk:
            obj = Burial.objects.get(pk=obj.pk)
            for form in [self] + self.forms:
                prefix = u''
                if form in [self.deadman_form, self.deadman_address_form, self.dc_form]:
                    prefix = _(u"Усопший ")
                if form in [self.responsible_form, self.responsible_address_form]:
                    prefix = _(u"Ответственный ")
                if form in [self.applicant_form, self.applicant_address_form, self.applicant_id_form]:
                    prefix = _(u"Заявитель ")
                for f in form.changed_data:
                    old_value = obj and getattr(obj, f, None) or form.initial.get(f) or ''
                    new_value = form.cleaned_data.get(f) or ''

                    if isinstance(old_value, datetime.date):
                        old_value = old_value.strftime('%d.%m.%Y')
                    if isinstance(new_value, datetime.date):
                        new_value = new_value.strftime('%d.%m.%Y')
                    if isinstance(old_value, datetime.time):
                        old_value = old_value.strftime('%H:%M')
                    if isinstance(new_value, datetime.time):
                        new_value = new_value.strftime('%H:%M')

                    if old_value != new_value:
                        changed_data.append((u'%s%s' % (prefix, form.fields[f].label), old_value, new_value))

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
                self.instance.loru = self.request.user.profile.org
                self.instance.source_type = Burial.SOURCE_FULL
            elif self.request.user.profile.is_ugh():
                if self.request.REQUEST.get('archive'):
                    self.instance.source_type = Burial.SOURCE_ARCHIVE
                else:
                    self.instance.source_type = Burial.SOURCE_UGH

        if self.deadman_form.is_valid_data():
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
            self.instance.deadman = None

        if self.responsible_form.is_valid_data():
            responsible = self.responsible_form.save(commit=False)
            if self.responsible_address_form.is_valid_data():
                responsible.address = self.responsible_address_form.save()
            responsible.save()
            self.instance.responsible = responsible
        else:
            self.instance.responsible = None

        if self.applicant_form.is_valid_data():
            applicant = self.applicant_form.save(commit=False)
            if self.applicant_address_form.is_valid_data():
                applicant.address = self.applicant_address_form.save()
            applicant.save()

            if self.request.user.profile.is_ugh() and self.applicant_id_form.is_valid_data():
                pid = self.applicant_id_form.save(commit=False)
                pid.person = applicant
                pid.save()
            self.instance.applicant = applicant
        else:
            self.instance.applicant = None

        self.instance.save()

        if changed_data or not self.instance or not self.instance.pk:
            changed_data_str = u'\n'.join([u'%s: %s -> %s' % cd for cd in changed_data])
            write_log(self.request, self.instance, _(u'Заявка сохранена') + u'\n' + changed_data_str)
        else:
            write_log(self.request, self.instance, _(u'Заявка сохранена'))

        msg = _(u"<a href='%s'>Заявка %s</a> сохранена") % (
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
            data.update({k:v})
        return data

    def setup_required(self):
        for f in self.fields:
            if f in ['burial_type', 'cemetery', 'area', 'plan_date', 'plan_time']:
                self.fields[f].required = True

        bt = self.data['burial_type'] or (self.instance and self.instance.burial_type) or None
        if bt not in Burial.NEW_BURIAL_TYPES:
            self.fields['place_number'].required = True

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
        if self.data.get('deadman-last_name'):
            if any([True for k,v in self.data.items() if v and k.startswith(self.dc_form.prefix)]):
                for f in self.dc_form.fields:
                    self.dc_form.fields[f].required = True

    def setup_required_responsible(self):
        pass

    def setup_required_responsible_address(self):
        if self.data.get('responsible-last_name'):
            for f in self.responsible_address_form.fields:
                if f in ['country_name', 'region_name', 'city_name', 'street_name', 'house']:
                    self.responsible_address_form.fields[f].required = True

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
        if self.cleaned_data.get('burial_type') not in Burial.NEW_BURIAL_TYPES:
            for f in [self.responsible_form, self.responsible_address_form]:
                if f.is_valid() and any(f.cleaned_data.values()):
                    raise forms.ValidationError(_(u"Для подзахоронений Ответственного быть не должно"))
        is_ugh = False
        if self.instance and self.instance.is_ugh_only():
            is_ugh = True
        if (not self.instance or not self.instance.pk) and self.request.user.profile.is_ugh():
            is_ugh = True
        if is_ugh:
            if not self.cleaned_data.get('loru') or not self.cleaned_data.get('agent'):
                if not self.applicant_form.is_valid_data():
                    raise forms.ValidationError(_(u"Нужно указать ЛОРУ или ФЛ-Заявителя"))
            if self.cleaned_data.get('loru') or self.cleaned_data.get('agent'):
                if self.applicant_form.is_valid_data():
                    raise forms.ValidationError(_(u"Нужно указать либо ЛОРУ, либо ФЛ-Заявителя"))

        return self.cleaned_data


    def mock_data(self):
        if not self.data:
            self.data = {}
            self.data.update(self.form_to_data(self))
            for f in self.forms:
                self.data.update(self.form_to_data(f))
