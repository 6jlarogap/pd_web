# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _

from django.views.generic.base import View
from users.forms import RegisterForm
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
        return super(LogoutView, self).dispatch(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
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

