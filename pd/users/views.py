# -*- coding: utf-8 -*-
import json
import datetime
import random
import hashlib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.db.models.aggregates import Count
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import UpdateView, CreateView, FormView
from django.views.generic.detail import DetailView
from django.views.decorators.csrf import csrf_exempt
    
from rest_framework.parsers import YAMLParser
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.authtoken.models import Token

from burials.views import UGHRequiredMixin, LoginRequiredMixin, SupervisorRequiredMixin
from logs.models import Log, write_log, LoginLog
from users.forms import UserAddForm, RegisterForm, LoruFormset, ProfileForm, UserProfileForm, \
                        UserDataForm, ChangePasswordForm, BankAccountFormset, OrgForm, \
                        OrgLogForm, LoginLogForm, OrgBurialStatsForm, SupportForm
from users.models import Profile, Org, RegisterProfile, ProfileLORU
from burials.models import Burial
from pd.views import PaginateListView, RequestToFormMixin, FormInvalidMixin

class AuthGetTokenView(APIView):
    """
    Проверка имени и пароля, (создать и) отдать token
    
    Проверка работы представления:
    curl -X POST http://host/api/signin -d 'username=USERNAME' -d 'password=PASSWORD'
    """
    parser_classes = (YAMLParser,)

    def post(self, request, format=None):
        token = None
        username = request.DATA.get('username')
        password = request.DATA.get('password')
        if username and password:
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                token, created = Token.objects.get_or_create(user=user)
        mimetype = 'application/json'
        if token:
            data = { 'token': token.key }
            status = 200
        else:
            data = { 'status': 'error', 'message': 'Wrong username or password' }
            status = 400
        return Response(data=data, status=status)

auth_get_token = AuthGetTokenView.as_view()

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
            write_log(request, request.user, _(u'Вход в систему'))
            LoginLog.write(request)
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
        write_log(request, request.user, _(u'Выход из системы'))
        logout(request)
        next_url = request.GET.get("next", "/")
        return redirect(next_url)

ulogout = LogoutView.as_view()

class RegistrationOldView(SupervisorRequiredMixin, View):
    """
    Регистрация
    """
    def post(self, request, *args, **kwargs):
        form = UserAddForm(data=request.POST)
        if form.is_valid():
            form.save()
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            login(request, user)
            write_log(request, request.user, _(u'Вход в систему'))
            LoginLog.write(request)
            messages.success(self.request, _(u"Все хорошо, регистрация успешна"))
            return redirect('dashboard')
        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = UserAddForm()
        request.session.set_test_cookie()
        return render(request, 'registration_old.html', {'form':form})

registration_old = RegistrationOldView.as_view()

class LoruRegistryView(UGHRequiredMixin, View):
    """
    Редактирование реестра ЛОРУ у этого УГХ
    """

    template_name = 'loru_registry.html'

    def get_success_url(self):
        return reverse('loru_registry')

    def get_formset(self):
        self.my_ugh = self.request.user.profile.org
        return LoruFormset(data=self.request.POST or None, instance=self.my_ugh,
                queryset=ProfileLORU.objects.filter(ugh=self.my_ugh).order_by('loru__name'))

    def get_context_data(self, **kwargs):
        return {
            'formset': self.get_formset(),
            'user': self.request.user,
        }

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()
        if formset.is_valid():
            old_lorus = []
            for registry_entry in ProfileLORU.objects.filter(ugh=self.my_ugh):
                old_lorus.append(registry_entry.loru)
            formset.save()
            new_lorus = []
            for registry_entry in ProfileLORU.objects.filter(ugh=self.my_ugh):
                new_lorus.append(registry_entry.loru)
            removed_lorus = []
            for loru in old_lorus:
                if loru not in new_lorus:
                    removed_lorus.append(loru)
            for profile in Profile.objects.filter(org__in=removed_lorus):
                if profile.cemetery and profile.cemetery.ugh == self.my_ugh:
                    profile.area = None
                    profile.cemetery = None
                    profile.save()

            messages.success(self.request, _(u"Данные сохранены"))
            write_log(self.request, self.request.user.profile.org, _(u'Изменены данные реестра ЛОРУ'))
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

class UserAddView(CreateView):
    template_name = 'add_user.html'
    model = User
    form_class = UserAddForm

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
        return super(UserAddView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        data = super(UserAddView, self).get_form_kwargs(**kwargs)
        del data['instance']
        return data

add_user = UserAddView.as_view()

class UserEditView(LoginRequiredMixin, UpdateView):
    template_name = 'edit_user.html'
    model = User
    form_class = UserDataForm

    def get_success_url(self):
        msg = _(u"<a href='%s'>Пользователь %s</a> изменен") % (
            reverse('edit_user', args=[self.object.pk]),
            self.object.username,
        )
        messages.success(self.request, msg)
        return reverse('edit_org', args=[self.object.profile.org.pk])

    def form_valid(self, form):
        form.save()
        if 'is_active' in form.changed_data:
            msg = _(u'%s (%s) изменил(а) статус %s (%s) на %s') % \
                    (self.request.user.profile.last_name_initials(),
                     self.request.user.username,
                     self.object.profile.last_name_initials(),
                     self.object.username,
                     _(u'активный') if self.object.is_active else _(u'неактивный'),
                   )
            write_log(self.request, self.object.profile.org, msg)
            write_log(self.request, self.object, msg)
        return redirect(self.get_success_url())
        
edit_user = UserEditView.as_view()

class OrgEditView(LoginRequiredMixin, RequestToFormMixin, FormInvalidMixin, UpdateView):
    template_name = 'edit_org.html'
    model = Org
    form_class = OrgForm

    def get_queryset(self):
        #return Org.objects.annotate(profiles=Count('profile')).filter(profiles=0)
        return Org.objects.filter(Q(pk=self.request.user.profile.org.pk) |
                                  Q(profile=None) |
                                 ~Q(profile__user__is_active=True)
                                 ).distinct()

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
        msg = _(u'%s (%s) изменил(а) пароль %s (%s)') % (self.request.user.profile.last_name_initials(),
                                                         self.request.user.username,
                                                         self.object.profile.last_name_initials(),
                                                         self.object.username,
                                                        )
        write_log(self.request, self.object, msg)
        write_log(self.request, self.object.profile.org, msg)
        return reverse('edit_org', args=[self.object.profile.org.pk])

change_password = ChangePasswordView.as_view()


class AutocompleteOrg(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('query')
        type_ = request.GET.get('type')
        exact = request.GET.get('exact')
        if request.user.profile.is_loru() or \
           request.user.profile.is_ugh():
            q = Q(name=query) if exact else Q(name__icontains=query)
            if type_:
                q &= Q(type=type_)
            orgs = Org.objects.filter(q).order_by('name')
        else:
            orgs = Org.objects.none()

        return HttpResponse(json.dumps([{'value': c.name} for c in orgs[:20]]), mimetype='text/javascript')

autocomplete_org = AutocompleteOrg.as_view()

class OrgLogView(LoginRequiredMixin, PaginateListView):
    template_name = 'org_log.html'
    context_object_name = 'logs'

    def get_queryset(self):
        if not self.request.GET:
            return Log.objects.none()

        org=self.request.user.profile.org
        users = []
        for profile in Profile.objects.filter(org=org):
            if profile.user:
                users.append(profile.user)
        # Такой поиск будет гораздо быстрее, чем по user__profile__org=org
        logs = Log.objects.filter(user__in=users)
        form = self.get_form()

        if form.data and form.is_valid():
            if form.cleaned_data['date_from']:
                logs = logs.filter(dt__gte=form.cleaned_data['date_from'])
            if form.cleaned_data['date_to']:
                logs = logs.filter(dt__lte=form.cleaned_data['date_to']+datetime.timedelta(days=1))

        sort = self.request.GET.get('sort', self.SORT_DEFAULT)
        SORT_FIELDS = {
            'dt': 'pk',
            '-dt': '-pk',
            'user': 'user__username',
            '-user': '-user__username',
        }
        s = SORT_FIELDS[sort]
        if not isinstance(s, list):
            s = [s]

        logs = logs.select_related(
            'user__profile',
        ).order_by(*s)
        return logs

    def get_form(self):
        return OrgLogForm(data=self.request.GET or None)

org_log = OrgLogView.as_view()

class LoginLogView(SupervisorRequiredMixin, PaginateListView):
    template_name = 'login_log.html'
    context_object_name = 'logs'

    def get_queryset(self):
        if not self.request.GET:
            return Log.objects.none()

        logs = LoginLog.objects.all()
        form = self.get_form()

        if form.data and form.is_valid():
            if form.cleaned_data['date_from']:
                logs = logs.filter(dt__gte=form.cleaned_data['date_from'])
            if form.cleaned_data['date_to']:
                logs = logs.filter(dt__lte=form.cleaned_data['date_to']+datetime.timedelta(days=1))

        sort = self.request.GET.get('sort', self.SORT_DEFAULT)
        SORT_FIELDS = {
            'dt': 'pk',
            '-dt': '-pk',
            'user': 'user__username',
            '-user': '-user__username',
            'org': 'org__name',
            '-org': '-org__name',
            'ip': 'ip',
            '-ip': '-ip',
       }
        s = SORT_FIELDS[sort]
        if not isinstance(s, list):
            s = [s]

        logs = logs.select_related(
            'user__profile',
        ).order_by(*s)
        return logs

    def get_form(self):
        return LoginLogForm(data=self.request.GET or None)

login_log = LoginLogView.as_view()

class RegisterView(CreateView):
    """
    Регистрация новых пользователей и организаций
    
    Пользователь набирает форму, отправляет заявку
    """
    template_name = 'register.html'
    form_class = RegisterForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user_password = make_password(form.cleaned_data['password1'])
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        obj.user_activation_key = hashlib.sha1(salt+obj.user_name).hexdigest()
        obj.status = RegisterProfile.STATUS_TO_CONFIRM
        obj.save()
        write_log(None, obj, _(u'%s : получена. Ожидание подтверждения') % obj)
        email_subject = "%s %s" % (unicode(_(u"Подтверждение заявки на регистрацию на")),
                                   unicode(_(u"Похоронное Дело")),
                                  )
        email_text = render_to_string(
                        'register_activation_email.txt',
                        {
                         'host': '%s://%s' % (self.request.is_secure() and 'https' or 'http',
                                              self.request.get_host(),
                                             ),
                         'activation_key': obj.user_activation_key,
                        }
                     )
        email_from = settings.DEFAULT_FROM_EMAIL
        email_to = (obj.user_email, )
        send_mail(email_subject, email_text, email_from, email_to)
        return redirect(reverse('register_activation', args=[obj.user_activation_key]))
        
register = RegisterView.as_view()

class RegisterActivation(DetailView):
    """
    Регистрация новых пользователей. Различные варианты.
    
    1. пользователь заполнил форму регистрации, подал заявку,
       получает ответ: жди письмо, в нем ссылка;
    2. пользователь получил письмо, надавил на ссылку,
       которая отличается от 1-й ссылки только: ?confirm=1
       получает ответ: заявка принята на рассмотрение.
       Администратору посылается об этом уведомление
    3. Пользователь подтвердил заявку на регистрацию,
       но тупо давит на присланные ему ссылку. Получит
       ответ, что его заявка уже рассматривается
    4. Пользователю отказано в регистрации.
    5. Пользователь уже внесен в систему.
    """
    template_name = 'simple_message.html'
    model = RegisterProfile

    def get_object(self):
        return get_object_or_404(RegisterProfile, user_activation_key=self.kwargs['key'])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        message = _(u'Регистрация успешна, но еще не завершена!')
        if self.object.status == RegisterProfile.STATUS_TO_CONFIRM:
            if 'confirm' in request.GET:
                self.object.status = RegisterProfile.STATUS_CONFIRMED
                self.object.save()
                write_log(None, self.object, _(u'%s : получено подтверждение') % self.object)
                for r in RegisterProfile.objects.filter(
                        status__in=(RegisterProfile.STATUS_DECLINED, RegisterProfile.STATUS_APPROVED, ),
                        dt_modified__lt=datetime.datetime.now() - \
                                        datetime.timedelta(days=RegisterProfile.CLEAR_PROCESSED),):
                    r.delete()
                    write_log(None, self.object,
                              _(u'%s : автоматическое удаление по истечении %s дней') % \
                                (self.object, RegisterProfile.CLEAR_PROCESSED, ))
                explain = _(
                            u'Спасибо за подтверждение заявки на регистрацию!\n'
                            u'Ваша заявка принята на <b>рассмотрение администратора системы</b>\n'
                )
                email_subject = "%s %s" % (unicode(_(u"Заявка на регистрацию на")),
                                           unicode(_(u"ПохоронноеДело")),
                                          )
                email_text = render_to_string(
                                'register_notify_supervisor_email.txt',
                                { 
                                    'obj': self.object,
                                    'host': '%s://%s' % (request.is_secure() and 'https' or 'http',
                                                         self.request.get_host(),
                                                        ),
                                }
                )
                email_from = settings.DEFAULT_FROM_EMAIL
                email_to = (Org.get_supervisor_email(), )
                send_mail(email_subject, email_text, email_from, email_to )
            else:
                explain = _(
                            u'Вам отправлено письмо, в котором имеется ссылка,\n'
                            u'переход по которой направит вашу заявку на рассмотрение\n'
                            u'администратора системы\n'
                        )
        elif self.object.status == RegisterProfile.STATUS_CONFIRMED:
            explain = _(
                        u'Ваша заявка на регистрацию уже <b>рассматривается администратором системы</b>\n'
                       )
        elif self.object.status == RegisterProfile.STATUS_DECLINED:
            message = _(u'В регистрации отказано!')
            explain = _(
                        u'Ваша заявка на регистрацию была <b>отклонена</b>.\n'
                        u'Обратитесь в <a href="%s">поддержку</a>\n' % reverse('support')
                       )
        elif self.object.status == RegisterProfile.STATUS_APPROVED:
            message = _(u'Регистрация успешна!')
            explain = _(
                        u"Вы можете работать в <a href='%s'>системе</a>\n"
                       ) % reverse('dashboard')
        else:
            raise Http404
        context = {}
        context['message'] = message
        context['html_message'] = u'<br /><big>%s</big>' % explain.replace('\n','<br />')
        return self.render_to_response(context)

register_activation = RegisterActivation.as_view()

class RegistrantsView(SupervisorRequiredMixin, TemplateView):
    template_name = 'registrants.html'

    def get_context_data(self, **kwargs):
        sort = self.request.GET.get('sort', '-pk')
        SORT_FIELDS = {
            'pk': 'pk',
            '-pk': '-pk',
            'org_type': 'org_type',
            '-org_type': '-org_org_type',
            'org': 'org_name',
            '-org': '-org_name',
            'fio': ['user_last_name', 'user_first_name', 'user_middle_name'],
            '-fio': ['-user_last_name', '-user_first_name', '-user_middle_name'],
            'director': 'org_director',
            '-director': '-org_director',
            'status': 'status',
            '-status': '-status',
        }
        s = SORT_FIELDS[sort] if sort in SORT_FIELDS else '-pk'
        if not isinstance(s, list):
            s = [s]

        registrants = RegisterProfile.objects.all().order_by(*s)
        return {
            'registrants': registrants,
            'sort': sort,
            'RegisterProfile' : RegisterProfile,
        }

registrants = RegistrantsView.as_view()

class RegistrantDelete(SupervisorRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        registrant = get_object_or_404(RegisterProfile, pk=self.kwargs['pk'])
        write_log(request, registrant, _(u'%s : удалена') % registrant)
        registrant.delete()
        return redirect('registrants')

registrant_delete = RegistrantDelete.as_view()

class RegistrantApprove(SupervisorRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        registrant = get_object_or_404(RegisterProfile, pk=self.kwargs['pk'])
        registrant.status = RegisterProfile.STATUS_APPROVED
        registrant.save()
        write_log(request, registrant, _(u'%s : одобрена') % registrant)
        user = User.objects.create(
                    username=registrant.user_name,
                    password=registrant.user_password,
                    email=registrant.user_email,
        )
        org=Org.objects.create(
                    type=registrant.org_type,
                    name=registrant.org_name,
                    full_name=registrant.org_full_name,
                    inn = registrant.org_inn,
                    director = registrant.org_director,
                    email = registrant.user_email,
                    phones = registrant.org_phones,
        )
        profile=Profile.objects.create(
                    user_last_name=registrant.user_last_name,
                    user_first_name=registrant.user_first_name,
                    user_middle_name=registrant.user_middle_name,
                    is_agent=True,
                    user=user,
                    org=org,
        )
        email_subject = unicode(_(u"Заявка на регистрацию одобрена"))
        email_text = render_to_string(
                        'register_approved_email.txt',
                        { 'host': '%s://%s' % (self.request.is_secure() and 'https' or 'http',
                                               self.request.get_host(),
                                              ),
                          'obj': registrant,
                        }
                    )
        email_from = settings.DEFAULT_FROM_EMAIL
        email_to = (registrant.user_email, )
        send_mail(email_subject, email_text, email_from, email_to )
        return redirect('registrants')

registrant_approve = RegistrantApprove.as_view()

class RegistrantDecline(SupervisorRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        registrant = get_object_or_404(RegisterProfile, pk=self.kwargs['pk'])
        registrant.status = RegisterProfile.STATUS_DECLINED
        registrant.save()
        write_log(request, registrant, _(u'%s : отказано') % registrant)
        return redirect('registrants')

registrant_decline = RegistrantDecline.as_view()

class OrgBurialStatsView(SupervisorRequiredMixin, TemplateView):
    template_name = 'org_burial_stats.html'

    def get_context_data(self, **kwargs):
        form = self.get_form()
        q = Q()
        if form.data and form.is_valid():
            if form.cleaned_data['date_from']:
                q &= Q(dt_modified__gte=form.cleaned_data['date_from'])
            if form.cleaned_data['date_to']:
                q &= Q(dt_modified__lte=form.cleaned_data['date_to'])
            if form.cleaned_data['status']:
                q &= Q(status=form.cleaned_data['status'])
            else:
                q &= Q(status__in=(Burial.STATUS_CLOSED, Burial.STATUS_EXHUMATED, ))

        sort = self.request.GET.get('sort', 'org')
        SORT_FIELDS = {
            'org': 'name',
            '-org': '-name',
       }
        s = SORT_FIELDS[sort]
        if not isinstance(s, list):
            s = [s]

        orgs = []
        total={}
        for source_type in Burial.SOURCE_TYPES:
            total[source_type[0]] = 0
        total['all'] = 0
        for o in Org.objects.filter(type=Org.PROFILE_UGH).order_by(*s):
            org = {'name': o.name, 'all': 0}
            for source_type in Burial.SOURCE_TYPES:
                org[source_type[0]] = Burial.objects.filter(
                    q &
                    Q(
                      ugh=o,
                      source_type=source_type[0],
                      annulated=False,
                     )
                ).count()
                total[source_type[0]] += org[source_type[0]]
                org['all'] += org[source_type[0]]
                total['all'] += org[source_type[0]]
            orgs.append(org)

        return {
            'form': form,
            'orgs':orgs,
            'total': total,
            'sort': sort,
        }

    def get_form(self):
        return OrgBurialStatsForm(data=self.request.GET or None)

org_burial_stats = OrgBurialStatsView.as_view()

class SupportView(RequestToFormMixin, FormView):
    form_class = SupportForm
    template_name = 'support.html'

    def form_valid(self, form):
        form.save()
        return super(SupportView, self).form_valid(form)
        
    def get_success_url(self):
        return reverse('support_thanks')

support = SupportView.as_view()

class SupportThanks(TemplateView):
    template_name = 'simple_message.html'

    def get(self, request, *args, **kwargs):
        message = _(u'Спасибо за сообщение!')
        html_message = u'<br /><big>%s.</big>' % \
                       _(u'Сообщение будет рассмотрено в службе поддержки')
        return self.render_to_response({'message': message,
                                        'html_message': html_message})

support_thanks = SupportThanks.as_view()
