# coding=utf-8
import datetime

from django import forms
from django.utils.translation import ugettext as _

from persons.models import DeadPerson, PersonID, DeathCertificate, AlivePerson, DocumentSource
from pd.models import UnclearDate
from pd.forms import BaseModelFormMixin

class StrippedStringsMixin(object):
    
   def clean(self):
       for field in self.cleaned_data:
           if isinstance(self.cleaned_data[field], basestring):
               self.cleaned_data[field] = self.cleaned_data[field].strip()
       return self.cleaned_data

class ValidDataMixin:
    def is_valid_data(self):
        return self.is_valid() and any(self.cleaned_data.values())

class DeadPersonForm(ValidDataMixin, StrippedStringsMixin, forms.ModelForm):
    class Meta:
        model = DeadPerson

    def __init__(self, request, *args, **kwargs):
        kwargs.setdefault('initial', {})
        if request.user.profile.is_loru():
            death_date = datetime.date.today()
        else:
            death_date = datetime.date.today() - datetime.timedelta(1)
        if not kwargs.get('instance'):
            kwargs['initial'].update({
                'death_date': death_date,
            })
        super(DeadPersonForm, self).__init__(*args, **kwargs)

    def is_valid_data(self):
        return self.is_valid() and len([k for k,v in self.cleaned_data.items() if v]) > 1 # more than just death date
    
    def do_clean_date(self, unclear_date_form_field):
        d = self.cleaned_data[unclear_date_form_field]
        if isinstance(d, basestring):
            try:
                datetime.datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                y, m, d_ = d.split('-')
                raise forms.ValidationError(_(u'Была введена неверная дата (д-м-г): %s-%s-%s') % (d_, m, y))
        elif isinstance(d, UnclearDate) and not d.no_day and d.no_month:
            raise forms.ValidationError(_(u'Нет месяца в дате'))
        return d

    def clean_birth_date(self):
        return self.do_clean_date('birth_date')

    def clean_death_date(self):
        return self.do_clean_date('death_date')

class PersonIDForm(ValidDataMixin, StrippedStringsMixin, forms.ModelForm):
    no_id_required = forms.BooleanField(label=_(u'Документ не обязателен'), required=False)
    source = forms.CharField(label=_(u'Кем выдан'), required=False)

    class Meta:
        model = PersonID
        exclude = ['person', ]

    def clean_source(self):
        src, _created = DocumentSource.objects.get_or_create(name=self.cleaned_data['source'])
        return src

    def __init__(self, *args, **kwargs):
        super(PersonIDForm, self).__init__(*args, **kwargs)
        if self.initial and self.initial.get('source') and isinstance(self.initial.get('source'), DocumentSource):
            self.initial['source'] = self.initial.get('source').name
        if self.instance and self.instance.source and isinstance(self.instance.source, DocumentSource):
            self.initial.update({'source': self.instance.source.name})

    def clean_date(self):
        today = datetime.date.today()
        release_date = self.cleaned_data.get('date')
        if release_date and release_date > today:
            msg = _(u'Неверная дата выдачи')
            raise forms.ValidationError(msg)
        return release_date

class DeathCertificateForm(ValidDataMixin, StrippedStringsMixin, BaseModelFormMixin, forms.ModelForm):
    class Meta:
        model = DeathCertificate
        exclude = ['person', ]

    def __init__(self, request, *args, **kwargs):
        self.request = request
        kwargs.setdefault('initial', {})
        instance = kwargs.get('instance')
        if (not instance or not instance.person) and not request.REQUEST.get('archive'):
            kwargs['initial'].update({
                'release_date': datetime.date.today(),
            })
        super(DeathCertificateForm, self).__init__(*args, **kwargs)

    def clean_release_date(self):
        today = datetime.date.today()
        release_date = self.cleaned_data.get('release_date')
        if release_date and release_date > today:
            msg = _(u'Неверная дата выдачи')
            raise forms.ValidationError(msg)
        return release_date

    def save(self, *args, **kwargs):
        return self.basemodelform_save(*args, **kwargs)

class AlivePersonForm(ValidDataMixin, StrippedStringsMixin, forms.ModelForm):
    class Meta:
        model = AlivePerson

    def __init__(self, *args, **kwargs):
        super(AlivePersonForm, self).__init__(*args, **kwargs)
        self.fields['phones'].widget = forms.TextInput()

    def is_valid_data(self):
        return self.is_valid() and self.cleaned_data.get('last_name') # last name should be present
