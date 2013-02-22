import datetime

from django import forms

from persons.models import DeadPerson, PersonID, DeathCertificate, AlivePerson

class ValidDataMixin:
    def is_valid_data(self):
        return self.is_valid() and any(self.cleaned_data.values())

class DeadPersonForm(ValidDataMixin, forms.ModelForm):
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

class PersonIDForm(ValidDataMixin, forms.ModelForm):
    class Meta:
        model = PersonID
        exclude = ['person', ]

class DeathCertificateForm(ValidDataMixin, forms.ModelForm):
    class Meta:
        model = DeathCertificate
        exclude = ['person', ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {})
        if not kwargs.get('instance'):
            kwargs['initial'].update({
                'release_date': datetime.date.today(),
            })
        super(DeathCertificateForm, self).__init__(*args, **kwargs)

class AlivePersonForm(ValidDataMixin, forms.ModelForm):
    class Meta:
        model = AlivePerson

    def is_valid_data(self):
        return self.is_valid() and self.cleaned_data.get('last_name') # last name should be present

