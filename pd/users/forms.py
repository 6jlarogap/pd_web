# coding=utf-8
from django import forms
from django.contrib.auth.models import User

from users.models import Profile


class RegisterForm(forms.Form):
    username = forms.SlugField(label=u"Имя пользователя")
    email = forms.EmailField()
    password1 = forms.CharField(label=u"Пароль", widget=forms.PasswordInput())
    password2 = forms.CharField(label=u"Пароль (повторите)", widget=forms.PasswordInput())
    name = forms.CharField(label=u"Организация")
    type = forms.ChoiceField(label=u"Тип", choices=Profile.PROFILE_TYPES)

    def clean_username(self):
        if User.objects.filter(username=self.cleaned_data['username']).exists():
            raise forms.ValidationError(u"Это имя уже используется")
        return self.cleaned_data['username']

    def clean(self):
        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError(u"Пароли не совпадают")
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

