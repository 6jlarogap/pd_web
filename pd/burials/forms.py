# coding=utf-8
import datetime
import json

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.deletion import ProtectedError
from django.forms.models import inlineformset_factory
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.db.models.query_utils import Q

from burials.models import Cemetery, Area, Burial, Place
from geo.forms import LocationForm
from logs.models import write_log
from persons.forms import DeadPersonForm, DeathCertificateForm, AlivePersonForm, PersonIDForm
from persons.models import DeathCertificate, PersonID
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

class CemeteryAdminForm(BaseCemeteryForm):
    class Meta:
        model = Cemetery

AreaFormset = inlineformset_factory(Cemetery, Area, can_delete=False)

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

class ChildrenJSONMixin:
    def universal_children_json(self, parent, children_rel, filter_kw=None):
        parents = {}
        filter_kw = filter_kw or {}
        if self.fields.get(parent):
            for c in self.fields[parent].queryset:
                parents[c.pk] = [[a.pk, u'%s' % a] for a in getattr(c, children_rel).filter(**filter_kw)]
        return mark_safe(json.dumps(parents))

    def cemetery_areas_json(self):
        return self.universal_children_json('cemetery', 'area_set')

    def cemetery_times_json(self):
        parents = {}
        if self.fields.get('cemetery'):
            for c in self.fields['cemetery'].queryset:
                parents[c.pk] = c.get_time_choices(
                    date=self.instance.plan_date or self.initial.get('plan_date'),
                    request=self.request
                )
        return mark_safe(json.dumps(parents))

    def agent_dover_json(self):
        return self.universal_children_json('agent', 'dover_set')

    def loru_agents_json(self):
        return self.universal_children_json('loru', 'profile_set', filter_kw={'is_agent': True})

class LoggingFormMixin:
    def get_prefix(self, form):
        return u''

    def collect_log_data(self):
        self.changed_list = []
        obj = self.instance
        if obj and obj.pk:
            obj = Burial.objects.get(pk=obj.pk)
            for form in [self] + self.forms:
                prefix = self.get_prefix(form)
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

                    if getattr(form.fields[f], 'choices', None):
                        old_value = dict(form.fields[f].choices).get(old_value, old_value)
                        new_value = dict(form.fields[f].choices).get(new_value, new_value)

                    if old_value != new_value:
                        self.changed_list.append((u'%s%s' % (prefix, form.fields[f].label), old_value, new_value))

    def put_log_data(self, msg=_(u'Захоронение сохранено')):
        if self.changed_list or not self.instance or not self.instance.pk:
            changed_data_str = u'\n'.join([u'%s: %s -> %s' % cd for cd in self.changed_list])
            write_log(self.request, self.instance, msg + u'\n' + changed_data_str)
        else:
            write_log(self.request, self.instance, msg)


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

class BurialForm(ChildrenJSONMixin, LoggingFormMixin, forms.ModelForm):
    opf = forms.ChoiceField(label=_(u'ОПФ'), choices=OPF_CHOICES, widget=forms.RadioSelect)

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
            choices = [('', '----------')] + self.instance.cemetery.get_time_choices(
                date=self.instance.plan_date,
                request=self.request,
            )
            self.fields['plan_time'].widget = forms.Select(choices=choices)
        if self.instance and self.instance.plan_time:
            self.initial['plan_time'] = self.instance.plan_time.strftime('%H:%M')
        else:
            self.fields['plan_date'].initial = datetime.date.today() + datetime.timedelta(1)

        if self.request.user.profile.is_loru():
            del self.fields['loru']
            del self.fields['agent']
            del self.fields['agent_director']
            del self.fields['dover']
            del self.fields['opf']

        if self.request.user.profile.is_ugh() or self.instance.is_ugh_only():
            ugh = self.request.user.profile.org
            loru_list = Org.objects.filter(type=Org.PROFILE_LORU, ugh_list__ugh=ugh)
            self.fields['loru'].queryset = loru_list
            self.fields['agent'].queryset = Profile.objects.filter(org__in=loru_list, is_agent=True)
            self.fields['dover'].queryset = Dover.objects.filter(agent__org__in=loru_list)

            self.fields.keyOrder.insert(self.fields.keyOrder.index('loru'), self.fields.keyOrder.pop(-1))
            if self.instance.pk and self.instance.applicant and self.instance.is_ugh():
                self.initial['opf'] = 'person'
            else:
                self.initial['opf'] = 'org'


        if self.request.user.profile.is_ugh() and self.request.REQUEST.get('archive'):
            del self.fields['plan_date']
            del self.fields['plan_time']
        elif self.instance.is_archive():
            del self.fields['plan_date']
            del self.fields['plan_time']
        else:
            if not self.instance.is_finished():
                del self.fields['fact_date']
            del self.fields['account_number']

        self.forms = self.construct_forms()

    def construct_forms(self):
        data = self.data or None
        deadman = self.instance and self.instance.deadman
        self.old_place = self.instance and self.instance.get_place()
        self.deadman_form = DeadPersonForm(data=data, prefix='deadman', instance=deadman)
        deadman_addr = self.instance and self.instance.deadman and self.instance.deadman.address
        self.deadman_address_form = LocationForm(data=data, prefix='deadman-address', instance=deadman_addr)
        try:
            dc = self.instance and self.instance.deadman and self.instance.deadman.deathcertificate
        except DeathCertificate.DoesNotExist:
            dc = None
        self.dc_form = DeathCertificateForm(data=data, prefix='deadman-dc', instance=dc)

        responsible = self.instance and self.instance.get_responsible()
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
            if self.cleaned_data.get('loru') and self.cleaned_data.get('agent'):
                if self.cleaned_data['loru'] != self.cleaned_data['agent'].org:
                    raise forms.ValidationError(_(u'Агент не от этого ЛОРУ'))
            if self.cleaned_data.get('agent') and self.cleaned_data.get('dover'):
                if self.cleaned_data['agent'] != self.cleaned_data['dover'].agent:
                    raise forms.ValidationError(_(u'Доверенность не от этого Агента'))

            if not self.cleaned_data.get('loru') and self.cleaned_data.get('agent'):
                raise forms.ValidationError(_(u'Нельзя указать Агента без ЛОРУ'))
            if not self.cleaned_data.get('agent') and self.cleaned_data.get('dover'):
                raise forms.ValidationError(_(u'Нельзя указать Доверенность без Агента'))

            if self.cleaned_data.get('loru') and self.applicant_form.is_valid_data():
                raise forms.ValidationError(_(u"Нужно указать только либо ЛОРУ, либо ФЛ-Заявителя"))

            if self.cleaned_data.get('agent_director'):
                self.cleaned_data.update(agent=None, dover=None, )

        return self.cleaned_data

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
            try:
                self.instance.deadman.delete()
            except (AttributeError, ProtectedError):
                pass
            self.instance.deadman = None

        if self.responsible_form.is_valid_data():
            responsible = self.responsible_form.save(commit=False)
            if self.responsible_address_form.is_valid_data():
                responsible.address = self.responsible_address_form.save()
            responsible.save()
            self.instance.responsible = responsible
        else:
            try:
                self.instance.responsible.delete()
            except (AttributeError, ProtectedError):
                pass
            self.instance.responsible = None

        if self.request.user.profile.is_ugh():
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
                self.instance.loru = None
            else:
                try:
                    self.instance.applicant.delete()
                except (AttributeError, ProtectedError):
                    pass
                self.instance.applicant = None

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
            data.update({k:v})
        return data

    def setup_required(self):
        for f in self.fields:
            if f in ['burial_type', 'cemetery', 'area', 'plan_date', 'plan_time']:
                self.fields[f].required = True

        bt = self.data['burial_type'] or (self.instance and self.instance.burial_type) or None
        if bt not in Burial.NEW_BURIAL_TYPES:
            self.fields['place_number'].required = True

        if self.instance.is_archive() and self.fields.get('fact_date'):
            self.fields['fact_date'].required = True

        if self.instance.is_finished():
            self.fields['place_number'].required = True

        if self.instance and self.instance.is_ugh() and self.instance.loru:
            for f in ['loru', 'agent', 'dover']:
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
        if self.instance and self.instance.is_ugh():
            is_ugh = True
        if (not self.instance or not self.instance.pk) and self.request.user.profile.is_ugh():
            is_ugh = True
        if is_ugh:
            if not self.cleaned_data.get('loru'):
                if not self.applicant_form.is_valid_data():
                    raise forms.ValidationError(_(u"Нужно указать ЛОРУ или ФЛ-Заявителя"))
            if self.cleaned_data.get('loru'):
                if self.applicant_form.is_valid_data():
                    raise forms.ValidationError(_(u"Нужно указать либо ЛОРУ, либо ФЛ-Заявителя"))

            if self.cleaned_data.get('opf') == 'person':
                if not self.applicant_form.is_valid_data():
                    raise forms.ValidationError(_(u"Нужно указать ФЛ-Заявителя"))

            if self.cleaned_data.get('opf') == 'org':
                if not self.cleaned_data.get('loru'):
                    raise forms.ValidationError(_(u"Нужно указать ЛОРУ"))
                if not self.cleaned_data.get('agent_director'):
                    if not self.cleaned_data.get('agent') or not self.cleaned_data.get('dover'):
                        msg = _(u"Нужно указать Агента и Доверенность или указать, что Агент - Директор")
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
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', ]

class AddDoverForm(forms.ModelForm):
    class Meta:
        model = Dover
        exclude = ['agent', 'document', ]

