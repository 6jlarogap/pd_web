# coding=utf-8
from django import forms
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _

from users.models import Profile, ProfileLORU


class RegisterForm(forms.Form):
    username = forms.SlugField(label=_(u"Имя пользователя"))
    email = forms.EmailField()
    password1 = forms.CharField(label=_(u"Пароль"), widget=forms.PasswordInput())
    password2 = forms.CharField(label=_(u"Пароль (повторите)"), widget=forms.PasswordInput())
    name = forms.CharField(label=_(u"Организация"))
    type = forms.ChoiceField(label=_(u"Тип"), choices=Profile.PROFILE_TYPES)

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
        profile = Profile.objects.create(
            user = user,
            type = self.cleaned_data['type'],
            name = self.cleaned_data['name'],
        )
        return user

LoruFormset = inlineformset_factory(Profile, ProfileLORU, fk_name='ugh')