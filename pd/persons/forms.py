from django import forms

from persons.models import DeadPerson, PersonID, DeathCertificate


class DeadPersonForm(forms.ModelForm):
    class Meta:
        model = DeadPerson

class PersonIDForm(forms.ModelForm):
    class Meta:
        model = PersonID

class DeathCertificateForm(forms.ModelForm):
    class Meta:
        model = DeathCertificate
        exclude = ['person', ]


