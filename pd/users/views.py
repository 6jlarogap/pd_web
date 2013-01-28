# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _

from django.views.generic.base import View
from django.views.generic.edit import UpdateView
from users.forms import RegisterForm, LoruFormset
from users.models import Profile


class LoginView(View):
    """
    Страница логина.
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('/')
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get("next", "/")
            if next_url == '/logout/':
                next_url = '/'
            return redirect(next_url)
        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = AuthenticationForm()
        request.session.set_test_cookie()
        return render(request, 'login.html', {'form':form})

ulogin = LoginView.as_view()

class LogoutView(View):
    """
    Выход пользователя из системы.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/')

        logout(request)
        next_url = request.GET.get("next", "/")
        return redirect(next_url)

ulogout = LogoutView.as_view()

class RegisterView(View):
    """
    Регистрация
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('/')
        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = RegisterForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(self.request, _(u"Все хорошо, теперь можете зайти на сервис"))
            return redirect('ulogin')
        return super(RegisterView, self).get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = RegisterForm()
        request.session.set_test_cookie()
        return render(request, 'register.html', {'form':form})


uregister = RegisterView.as_view()

class ProfileView(UpdateView):
    """
    Редактирование профиля
    """

    template_name = 'profile.html'
    model = Profile

    def get_success_url(self):
        return reverse('profile')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/')
        if request.user.profile.is_ugh():
            self.formset = LoruFormset(data=request.POST or None, instance=request.user.profile)
        else:
            self.formset = LoruFormset()
        return super(ProfileView, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        data = super(ProfileView, self).get_context_data(**kwargs)
        data['formset'] = self.formset
        return data

    def form_valid(self, form):
        self.formset.save()
        form.save()
        messages.success(self.request, _(u"Данные сохранены"))
        return redirect(self.get_success_url())

profile = ProfileView.as_view()

