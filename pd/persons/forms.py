import datetime

from django import forms

from persons.models import DeadPerson, PersonID, DeathCertificate, AlivePerson


class DeadPersonForm(forms.ModelForm):
    class Meta:
        model = DeadPerson

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {})
        if not kwargs.get('instance'):
            kwargs['initial'].update({
                'death_date': datetime.date.today() - datetime.timedelta(1),
            })
        super(DeadPersonForm, self).__init__(*args, **kwargs)

class PersonIDForm(forms.ModelForm):
    class Meta:
        model = PersonID
        exclude = ['person', ]

class DeathCertificateForm(forms.ModelForm):
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

class AlivePersonForm(forms.ModelForm):
    class Meta:
        model = AlivePerson
