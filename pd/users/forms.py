# coding=utf-8
from django import forms
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _

from users.models import Profile, ProfileLORU, Org


class RegisterForm(forms.Form):
    username = forms.SlugField(label=_(u"Имя пользователя"))
    email = forms.EmailField()
    password1 = forms.CharField(label=_(u"Пароль"), widget=forms.PasswordInput())
    password2 = forms.CharField(label=_(u"Пароль (повторите)"), widget=forms.PasswordInput())

    def clean_username(self):
        if User.objects.filter(username=self.cleaned_data['username']).exists():
            raise forms.ValidationError(_(u"Это имя уже используется"))
        return self.cleaned_data['username']

    def clean(self):
        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError(_(u"Пароли не совпадают"))
        return self.cleaned_data

    def save(self, *args, **kwargs):
        user = User.objects.create_user(
            self.cleaned_data['username'],
            self.cleaned_data['email'],
            self.cleaned_data['password1']
        )
        Profile.objects.create(user=user)
        return user

class BaseLoruFormset(BaseInlineFormSet):
    @property
    def changed_data(self):
        for f in self.forms:
            if f.is_valid() and any(f.cleaned_data.values()):
                yield f.cleaned_data

LoruFormset = inlineformset_factory(Org, ProfileLORU, fk_name='ugh', formset=BaseLoruFormset)

class ProfileForm(forms.ModelForm):
    org_type = forms.ChoiceField(label=_(u"Тип"), choices=Org.PROFILE_TYPES, required=False)
    org_name = forms.CharField(label=_(u"Краткое название организации"), required=False)
    org_full_name = forms.CharField(label=_(u"Полное название организации"), required=False)
    org_inn = forms.CharField(label=_(u"ИНН организации"), required=False)
    org_director = forms.CharField(label=_(u"Директор"), required=False)

    class Meta:
        model = Profile
        
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        if self.instance.org:
            self.fields['org'].widget = forms.HiddenInput()
            for f in self.fields:
                if f.startswith('org_'):
                    self.initial.update({f: getattr(self.instance.org, f[4:])})
        else:
            self.fields['org'].required = False

    def save(self, commit=True, *args, **kwargs):
        obj = super(ProfileForm, self).save(commit=False, *args, **kwargs)
        params = dict([(k[4:], v) for k,v in self.cleaned_data.items() if v and k.startswith('org_')])
        if not obj.org:
            obj.org, _created = Org.objects.get_or_create(**params)
        else:
            Org.objects.filter(pk=obj.org.pk).update(**params)
        if commit:
            obj.save()
        return obj

class UserDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',]

class ChangePasswordForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['id', ] # guaranteed to be invisible and non-editable

    password1 = forms.CharField(label=_(u"Пароль"), widget=forms.PasswordInput())
    password2 = forms.CharField(label=_(u"Пароль (повторите)"), widget=forms.PasswordInput())

    def clean(self):
        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError(_(u"Пароли не совпадают"))
        return self.cleaned_data

    def save(self, *args, **kwargs):
        self.instance.set_password(self.cleaned_data['password1'])
        return self.instance

