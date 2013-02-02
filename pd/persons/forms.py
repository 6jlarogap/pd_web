import datetime

from django import forms

from persons.models import DeadPerson, PersonID, DeathCertificate


class DeadPersonForm(forms.ModelForm):
    class Meta:
        model = DeadPerson

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {}).update({
            'death_date': datetime.date.today() - datetime.timedelta(1),
        })
        super(DeadPersonForm, self).__init__(*args, **kwargs)

class PersonIDForm(forms.ModelForm):
    class Meta:
        model = PersonID

class DeathCertificateForm(forms.ModelForm):
    class Meta:
        model = DeathCertificate
        exclude = ['person', ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {}).update({
            'release_date': datetime.date.today() - datetime.timedelta(1),
        })
        super(DeathCertificateForm, self).__init__(*args, **kwargs)


