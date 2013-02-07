# coding=utf-8
import datetime
from django import forms
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from burials.models import BurialRequest, Cemetery, Area, Burial, Place
from django.db.models.query_utils import Q


class BurialRequestCreateForm(forms.ModelForm):
    class Meta:
        model = BurialRequest
        exclude = ['loru', 'responsible']

    def __init__(self, request, *args, **kwargs):
        super(BurialRequestCreateForm, self).__init__(*args, **kwargs)
        self.fields['cemetery'].queryset = Cemetery.objects.filter(
            Q(ugh__isnull=True) | Q(ugh__loru_list__loru=request.user.profile.org)
        ).distinct()
        if self.instance and self.instance.cemetery and self.instance.cemetery.time_slots:
            choices = [('', '')] + self.instance.cemetery.get_time_choices()
            # self.fields['plan_time'] = forms.ChoiceField(label=_(u'План. время'), choices=choices, required=False)
            self.fields['plan_time'].widget = forms.Select(choices=choices)
        if self.instance and self.instance.plan_time:
            self.initial['plan_time'] = self.instance.plan_time.strftime('%H:%M')
        self.fields['plan_date'].initial = datetime.date.today() + datetime.timedelta(1)

    def clean_plan_time(self):
        return self.cleaned_data['plan_time'] or None

    def clean(self):
        if self.cleaned_data.get('cemetery') and self.cleaned_data.get('area'):
            if self.cleaned_data['cemetery'] != self.cleaned_data['area'].cemetery:
                raise forms.ValidationError(_(u'Участок не от этого кладбища'))
        return self.cleaned_data

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
    operation = forms.ChoiceField(required=False, choices=BurialRequest.BURIAL_TYPES, label=_(u"Услуга"))
    cemetery = forms.CharField(required=False, label=_(u"Кладбища"))
    area = forms.CharField(required=False, label=_(u"Участок"))
    row = forms.CharField(required=False, label=_(u"Ряд"))
    place = forms.CharField(required=False, label=_(u"Место"))
    no_responsible = forms.BooleanField(required=False, initial=False, label=_(u"Без отв."))

class BurialForm(forms.ModelForm):
    class Meta:
        model = Burial
        exclude = ['place', 'deadman', ]


class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        exclude = ['responsible', ]

