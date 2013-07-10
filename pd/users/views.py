# -*- coding: utf-8 -*-
import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Count
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View
from django.views.generic.edit import UpdateView, CreateView

from burials.views import UGHRequiredMixin, LoginRequiredMixin
from logs.models import write_log
from users.forms import RegisterForm, LoruFormset, ProfileForm, UserProfileForm, UserDataForm, ChangePasswordForm, BankAccountFormset, OrgForm
from users.models import Profile, Org


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
        if request.user.is_authenticated() and \
           request.user.profile and \
           hasattr(settings, 'SUPERVISOR_ORG_INN') and \
           request.user.profile.org.inn == settings.SUPERVISOR_ORG_INN:
            return super(RegisterView, self).dispatch(request, *args, **kwargs)
        raise Http404

    def post(self, request, *args, **kwargs):
        form = RegisterForm(data=request.POST)
        if form.is_valid():
            form.save()
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            login(request, user)
            messages.success(self.request, _(u"Все хорошо, регистрация успешна"))
            return redirect('dashboard')
        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = RegisterForm()
        request.session.set_test_cookie()
        return render(request, 'register.html', {'form':form})


uregister = RegisterView.as_view()

class LoruRegistryView(UGHRequiredMixin, View):
    """
    Редактирование реестра ЛОРУ у этого УГХ
    """

    template_name = 'loru_registry.html'

    def get_success_url(self):
        return reverse('loru_registry')

    def get_formset(self):
        return LoruFormset(data=self.request.POST or None, instance=self.request.user.profile.org)

    def get_context_data(self, **kwargs):
        return {
            'formset': self.get_formset(),
            'user': self.request.user,
        }

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()
        if formset.is_valid():
            formset.save()
            messages.success(self.request, _(u"Данные сохранены"))
            write_log(self.request, self.request.user.profile, _(u'Изменены данные реестра ЛОРУ'))
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, _(u"Обнаружены ошибки"))
            return self.get(request, *args, **kwargs)
            
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

loru_registry = LoruRegistryView.as_view()

class ProfileView(LoginRequiredMixin, UpdateView):
    """
    Редактирование профиля, заодно организации,
    применяется только при вводе начальной организации
    """

    template_name = 'profile.html'
    model = Profile
    form_class = ProfileForm

    def get_success_url(self):
        return reverse('profile')

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        form.save()
        write_log(self.request, form.instance, _(u'Изменены данные организации и пользователя'))
        messages.success(self.request, _(u"Данные сохранены"))
        return redirect(self.get_success_url())

profile = ProfileView.as_view()

class UserProfileView(LoginRequiredMixin, UpdateView):
    """
    Редактирование профиля
    """

    template_name = 'userprofile.html'
    model = Profile
    form_class = UserProfileForm

    def get_success_url(self):
        return reverse('user_profile')

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        form.save()
        write_log(self.request, form.instance, _(u'Изменены данные пользователя'))
        messages.success(self.request, _(u"Данные сохранены"))
        return redirect(self.get_success_url())

user_profile = UserProfileView.as_view()

class UserAddForm(CreateView):
    template_name = 'add_user.html'
    model = User
    form_class = RegisterForm

    def form_valid(self, form):
        self.object = form.save()
        self.object.profile.org = self.request.user.profile.org
        self.object.profile.save()

        msg = _(u"<a href='%s'>Пользователь %s</a> создан") % (
            reverse('edit_user', args=[self.object.pk]),
            self.object.username,
        )
        messages.success(self.request, msg)
        write_log(self.request, self.object, _(u'Создан пользователь'))
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('edit_org', args=[self.object.profile.org.pk])

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/')
        return super(UserAddForm, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        data = super(UserAddForm, self).get_form_kwargs(**kwargs)
        del data['instance']
        return data

add_user = UserAddForm.as_view()

class UserEditForm(UpdateView):
    template_name = 'edit_user.html'
    model = User
    form_class = UserDataForm

    def get_success_url(self):
        msg = _(u"<a href='%s'>Пользователь %s</a> изменен") % (
            reverse('edit_user', args=[self.object.pk]),
            self.object.username,
        )
        messages.success(self.request, msg)
        write_log(self.request, self.object, _(u'Изменены данные пользователя'))
        return reverse('edit_org', args=[self.object.profile.org.pk])

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('/')
        return super(UserEditForm, self).dispatch(request, *args, **kwargs)

edit_user = UserEditForm.as_view()

class OrgEditView(LoginRequiredMixin, UpdateView):
    template_name = 'edit_org.html'
    model = Org
    form_class = OrgForm

    def get_form_kwargs(self):
        data = super(OrgEditView, self).get_form_kwargs()
        data['request'] = self.request
        return data

    #def get_queryset(self):
        #return Org.objects.annotate(profiles=Count('profile')).filter(profiles=0)

    def get_context_data(self, **kwargs):
        data = super(OrgEditView, self).get_context_data(**kwargs)
        data['is_my_org'] = self.request.user.profile.org.pk == self.object.pk
        return data

    def get_success_url(self):
        msg = _(u"<a href='%s'>Организация %s</a> изменена") % (
            reverse('edit_org', args=[self.object.pk]),
            self.object,
        )
        messages.success(self.request, msg)
        return reverse('edit_org', args=[self.object.pk])
        
    def form_invalid(self, form, *args, **kwargs):
        messages.error(self.request, _(u'Обнаружены ошибки, их необходимо исправить'))
        return super(OrgEditView, self).form_invalid(form, *args, **kwargs)

edit_org = OrgEditView.as_view()

class ChangePasswordView(LoginRequiredMixin, UpdateView):
    template_name = 'change_password.html'
    model = User
    form_class = ChangePasswordForm

    def get_success_url(self):
        msg = _(u"Пароль <a href='%s'>пользователя %s</a> изменен") % (
            reverse('edit_user', args=[self.object.pk]),
            self.object.username,
        )
        messages.success(self.request, msg)
        msg = _(u'%s (%s) изменил(а) пароль %s (%s)') % (self.request.user.username,
                                                         self.request.user.profile.last_name_initials(),
                                                         self.object.username,
                                                         self.object.profile.last_name_initials(),
                                                        )
        write_log(self.request, self.object, msg)
        write_log(self.request, self.object.profile.org, msg)
        return reverse('edit_org', args=[self.object.profile.org.pk])

change_password = ChangePasswordView.as_view()


class AutocompleteOrg(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']
        if request.user.profile.is_loru() or \
           request.user.profile.is_ugh():
            orgs = Org.objects.filter(name__icontains=query)
        else:
            orgs = Org.objects.none()

        return HttpResponse(json.dumps([{'value': c.name} for c in orgs[:20]]), mimetype='text/javascript')

autocomplete_org = AutocompleteOrg.as_view()
