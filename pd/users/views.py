# -*- coding: utf-8 -*-
import json
import datetime
import random
import string
import decimal
import hashlib
import os
import csv

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail, EmailMessage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import transaction, connection
from django.db.models.query_utils import Q
from django.db.models.aggregates import Count
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import UpdateView, CreateView, FormView
from django.views.generic.detail import DetailView
    
from captcha.client import submit

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated

from burials.views import UGHRequiredMixin, LoginRequiredMixin, SupervisorRequiredMixin
from logs.models import Log, write_log, LoginLog
from users.forms import UserAddForm, RegisterForm, LoruFormset, ProfileForm, UserProfileForm, \
                        UserDataForm, ChangePasswordForm, BankAccountFormset, OrgForm, \
                        OrgLogForm, LoginLogForm, OrgBurialStatsForm, SupportForm, TestCaptchaForm
from users.models import Profile, Org, RegisterProfile, ProfileLORU, CustomerProfile, get_mail_footer, \
                         is_cabinet_user, is_loru_user
from pd.models import validate_phone_as_number
from persons.models import AlivePerson
from burials.models import Cemetery, Area, Burial, Place
from billing.models import Wallet, Rate
from orders.models import Product, ProductStatus, ProductHistory
from pd.views import PaginateListView, RequestToFormMixin, FormInvalidMixin, get_front_end_url, ServiceException

from sms_service.utils import send_sms

class CheckRecaptchaMixin(object):
    
    def check_recaptcha(self, request, challenge, response):
        forwarded_ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_ip:
            remote_ip = forwarded_ip
        else:
            remote_ip = request.META.get('REMOTE_ADDR', '')
        use_ssl = getattr(settings, 'RECAPTCHA_USE_SSL', False)
        private_key = settings.RECAPTCHA_PRIVATE_KEY
        return submit(
                smart_unicode(challenge),
                smart_unicode(response),
                private_key=private_key,
                remoteip=remote_ip,
                use_ssl=use_ssl
        ).is_valid
    
class AuthGetTokenView(APIView):
    """
    Проверка имени и пароля, (создать и) отдать token
    """
    def post(self, request):
        token = None
        username = request.DATA.get('username')
        password = request.DATA.get('password')
        confirm_tc = request.DATA.get('confirmTC')
        data = dict(status='error')
        status_code = 400
        if username and password:
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                token, created = Token.objects.get_or_create(user=user)
        if token:
            tc_confirmed = True
            role = None
            try:
                user.customerprofile
            except CustomerProfile.DoesNotExist:
                try:
                    user.profile
                except Profile.DoesNotExist:
                    pass
                else:
                    if user.profile.is_loru():
                        role = u'ROLE_LORU'
                    elif user.profile.is_ugh():
                        role = u'ROLE_OMS'
            else:
                role = 'ROLE_CLIENT'
                tc_confirmed = user.customerprofile.tc_confirmed or confirm_tc
            if not role:
                raise Exception(u'Unknown role')
            if tc_confirmed:
                login(request, user)

                profile = { 'email': user.email or None, 'photo': None }
                pr = user.customerprofile if role == 'ROLE_CLIENT' else user.profile
                profile['lastname'] = pr.user_last_name or user.last_name or None
                profile['firstname'] = pr.user_first_name or user.first_name or None
                profile['middlename'] = pr.user_middle_name or None
                if role == 'ROLE_CLIENT':
                    org = { 'id': None, 'name': None }
                    profile['mainPhone'] = username
                    if not user.customerprofile.tc_confirmed and confirm_tc:
                        user.customerprofile.tc_confirmed = datetime.datetime.now()
                        user.customerprofile.save()
                else:
                    org = { 'id': user.profile.org.pk, 'name': user.profile.org.name or None }
                    profile['mainPhone'] = None

                data.update({
                    'status': 'success',
                    'token': token.key,
                    'sessionId': request.session._get_or_create_session_key(),
                    'profile': profile,
                    'org': org,
                    'role': role,
                 })
                status_code = 200
                write_log(request, request.user, _(u'Вход в систему'))
                LoginLog.write(request)
            else:
                data['message'] = 'unconfirmed_tc'
        else:
            data['message'] = 'Wrong username or password'
        return Response(data=data, status=status_code)

auth_get_token = AuthGetTokenView.as_view()

class AuthApiLogout(APIView):
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        logout(request)
        return Response(data={}, status=200)

auth_api_logout = AuthApiLogout.as_view()

class ApiAuthSettings(APIView):
    permission_classes = (IsAuthenticated,)
    
    @transaction.commit_on_success
    def put(self, request):
        """
        Поменять пароль и фотку пользователя
        
        Input data
        {
           # avatar, пока не применяем
           "loginPhone": "375297542270",
            "oldPassword": "1234567",
            "newPassword": "7654321"
         }
        """
        try:
            user = request.user
            old_username = user.username
            old_password = request.DATA.get('oldPassword')
            if old_password:
                user = authenticate(username=old_username, password=old_password)
                if not user:
                    raise ServiceException(_(u'Неверно указан действующий пароль'))

            login_phone = request.DATA.get('loginPhone')
            if login_phone:
                try:
                    validate_phone_as_number(decimal.Decimal(login_phone))
                except (TypeError, decimal.InvalidOperation, ValidationError, ):
                    raise ServiceException(_(u'Неверный формат телефона'))
                user.username = login_phone

            new_password = request.DATA.get('newPassword')
            if new_password:
                user.set_password(new_password)

            email = request.DATA.get('email')
            if email:
                try:
                    validate_email(email)
                except ValidationError:
                    raise ServiceException(_(u'Неверный формат адреса электронной почты'))
                user.email = email

            if new_password or login_phone or email:
                user.save()
            try:
                # это только для клиента кабинета!
                user.customerprofile
                if login_phone and login_phone != old_username:
                    AlivePerson.objects.filter(login_phone=old_username).update(login_phone=login_phone)
            except CustomerProfile.DoesNotExist:
                pass
        except ServiceException as excpt:
            data = { 'status': 'error',
                     'message': excpt.message,
                   }
            status_code = 400
        else:
            data = {}
            status_code = 200
        return Response(data=data, status=status_code)

api_auth_settings = ApiAuthSettings.as_view()

class ApiAuthUser(APIView):
    permission_classes = (IsAuthenticated,)
    
    def delete(self, request):
        request.user.is_active = False
        try:
            request.user.customerprofile
        except CustomerProfile.DoesNotExist:
            pass
        else:
            # Пользователь кабинета
            request.user.customerprofile.user_last_name = ''
            request.user.customerprofile.user_first_name = ''
            request.user.customerprofile.user_middle_name = ''
            request.user.customerprofile.save()
            request.user.email = ''
            chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
            while True:
                new_username  = 'deleted-' + ''.join(random.choice(chars) for x in range(10))
                if not User.objects.filter(username=new_username).count():
                    request.user.username = new_username
                    break
        request.user.save()
        return Response(data={}, status=200)

api_auth_user = ApiAuthUser.as_view()

class AuthGetPasswordBySMSView(CheckRecaptchaMixin, APIView):
    """
    Замена существующему пользователю-кабинетчику пароля, отправка пароля по СМС
    
    Input example:
    {
        "phoneNumber": "375291234567",
        "recaptchaData": {
            "response": "foo bar",
            "challenge": "03AHJ_VuvQ5p0AdejIw4W6"
        }
    }
    Output examples:
    {
        "status: "success",
        "message": "Пароль установлен"
    }
    {
        "status: "error",
        "message": "Ваш номер телефона не указан в списке для входа. Обратитесь в администрацию кладбища."
        # or       "Введена не верная captcha"
    }
    """
    def post(self, request):
        status = 'error'
        status_code = 400
        message = ''
        phone_number = request.DATA['phoneNumber']
        recaptcha_data = request.DATA['recaptchaData']
        if not self.check_recaptcha(self.request, recaptcha_data['challenge'], recaptcha_data['response']):
            message = _(u'Введена неверная captcha')
        else:
            if not CustomerProfile.objects.filter(user__username=phone_number).count():
                message = _(u'Вы не зарегистрированы в системе. Обратитесь в администрацию кладбища')
            else:
                password = CustomerProfile.generate_password()
                user = User.objects.get(username=phone_number)
                user.set_password(password)
                user.save()
                if not settings.DEBUG:
                    sent, message = send_sms(
                        phone_number=phone_number,
                        text=_(u'Vash parol na PohoronnoeDelo: %s') % password,
                        email_error_text = _(u"Пользователь %s не смог получить или заменить пароль" % (phone_number,)),
                    )
        if not message:
            status = 'success'
            status_code = 200
            if settings.DEBUG:
                message = _(u'Ваш пароль: %s') % password
            else:
                message = _(u'Пароль установлен, СМС с паролем отправлено')
        data = { 'status': status, 'message': message }
        return Response(data=data, status=status_code)

auth_get_password_by_sms = AuthGetPasswordBySMSView.as_view()

class ApiFeedBack(CheckRecaptchaMixin, APIView):
    """
    Вопрос в поддержку от front-end api. Отправка письма.
    
    Пример входных данных:
    {
        "subject": "Тема",
        "text": "Текст вопроса",
        "email": "email@email.ru",
        "recaptchaData": {
            "response": "foo bar",
            "challenge": "03AHJ_VuvQ5p0AdejIw4W6"
        }
    }
    recaptchaData передается, если пользователь незарегистрирован
    
    Status codes:
        200 - если все нормально
        400 - если произошла ошибка валидации входных данных

    Если отправляет аутентифицированный пользователь и у него нет
    в свойствах почтового адреса, то он устанавливается в email
    из входных данных
    """
    def post(self, request):
        status_code = 400
        recaptcha_data = request.DATA.get('recaptchaData')
        try:
            if not request.user.is_authenticated():
                if not recaptcha_data:
                    raise ServiceException(_(u'Не задана captcha'))
                if not self.check_recaptcha(self.request, recaptcha_data['challenge'], recaptcha_data['response']):
                    raise ServiceException(_(u'Ошибка проверки captcha'))

            email_from = (request.DATA.get('email') or '').strip()
            callback = request.DATA.get('requestBackCall')
            phone = (request.DATA.get('phoneNumber') or '').strip()
            email_text = (request.DATA.get('text') or '').strip()

            if callback:
                try:
                    validate_phone_as_number(phone.lstrip('+'))
                except ValidationError:
                    raise ServiceException(_(u"Не указан или неверен телефон для обратного звонка"))
            else:
                try:
                    validate_email(email_from)
                except ValidationError:
                    raise ServiceException(_(u"Неверный адрес электронной почты"))
                if not email_text:
                    raise ServiceException(_(u"Если не требуется обратный звонок, то задайте вопрос"))
                
            user_last_name = (request.DATA.get('lastName') or '').strip()
            if not user_last_name:
                raise ServiceException(_(u"Не задана фамилия"))
            user_first_name = (request.DATA.get('firstName') or '').strip()
            user_middle_name = (request.DATA.get('middleName') or '').strip()
            if not user_first_name and user_middle_name:
                raise ServiceException(_(u"Не указано имя при указанном отчестве"))

            email_subject = (request.DATA.get('subject') or '').strip()
            if not email_subject:
                email_subject = _(u'Вопрос в поддержку')
            
            if request.user.is_authenticated():
                if not request.user.email and email_from:
                    request.user.email = email_from
                    request.user.save()

                if is_cabinet_user(request.user):
                    profile = request.user.customerprofile
                else:
                    profile = request.user.profile
                    if callback and not request.user.profile.org.phones:
                        request.user.profile.org.phones = phone
                        request.user.profile.org.save()

                if profile.user_last_name != user_last_name or \
                   profile.user_first_name != user_first_name or \
                   profile.user_middle_name != user_middle_name:
                    profile.user_last_name = user_last_name
                    profile.user_first_name = user_first_name
                    profile.user_middle_name = user_middle_name
                    profile.save()

            email_text += u"\n----------\n\n%s: %s %s %s" % (
                            _(u'Запрос от'),
                            user_last_name,
                            user_first_name,
                            user_middle_name,
                        )
            if callback:
                email_text += u"\n\n%s\n%s %s" % (
                    _(u'ЗАКАЗАН ОБРАТНЫЙ ЗВОНОК'),
                    _(u'телефон'),
                    phone,
                )
            email_text += get_mail_footer(request.user)

            email_to = (settings.DEFAULT_FROM_EMAIL, )
            headers = {}
            if email_from:
                headers['Reply-To'] = email_from
            EmailMessage(email_subject, email_text, email_from, email_to, headers=headers, ).send()
            data = { 'status': 'success',
                     'message': '',
                   }
            status_code = 200
        except ServiceException as excpt:
            data = { 'status': 'error',
                     'message': excpt.message,
                   }
            status_code = 400
        return Response(data=data, status=status_code)

api_feedback = ApiFeedBack.as_view()

class ApiLoruPlaces(APIView):
    """
    Поиск всех ОМС, подключенных к этому лору

    При этом ОМС, отмеченный в settings.ORG_AD_PAY_RECIPIENT,
    ставится первым в списке
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if not is_loru_user(request.user):
            return Response(data={ "detail": "User denied access: not LORU" }, status=403)
        data = []
        idx_public_catalog = None
        for i, ugh in enumerate(Org.objects.filter(loru_list__loru=request.user.profile.org)):
            d = {
                    'id': ugh.pk,
                    'name': ugh.name,
                    'currency': {
                        'name': ugh.currency.name,
                        'shortName': ugh.currency.short_name,
                        'code': ugh.currency.code,
                    }
            }
            if ugh.inn == settings.ORG_AD_PAY_RECIPIENT['inn']:
                idx_public_catalog = i
            for action, costFor in (
                                        (Rate.RATE_ACTION_PUBLISH, 'costForEnable'),
                                        (Rate.RATE_ACTION_UPDATE, 'costForUp'),
                                   ):
                d[costFor] = decimal.Decimal('0.00')
                for rate in Rate.objects.filter(wallet__org=ugh,
                                                wallet__currency=ugh.currency,
                                                action=action,
                                                ).order_by('-date_from')[:1]:
                        d['costFor'] = rate.rate
            data.append(d)
        if idx_public_catalog:
            data.insert(0, data.pop(idx_public_catalog))
        return Response(data=data, status=200)

api_loru_places = ApiLoruPlaces.as_view()

class ApiBalance(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data = []
        for wallet in Wallet.objects.filter(org=request.user.profile.org):
            d = {
                    'amount': wallet.amount,
                    'currency': {
                        'name': wallet.currency.name,
                        'shortName': wallet.currency.short_name,
                        'code': wallet.currency.code,
                    }
            }
            data.append(d)
            data = {
                'currentBalance': data,
            }
        return Response(data=data, status=200)

api_balance = ApiBalance.as_view()

class LoginView(View):
    """
    Страница логина. Перенаправление на страницу логина front-end,
    если задан параметр settings.REDIRECT_LOGIN_TO_FRONT_END
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('/')
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if settings.REDIRECT_LOGIN_TO_FRONT_END:
            if request.GET.get("redirectUrl"):
                next_url = "?redirectUrl=%s" % request.GET.get("redirectUrl")
            else:
                next_url = ''
            response = redirect('%s#/signout%s' % (get_front_end_url(request), next_url))
            response.delete_cookie('pdsession')
            return response
        else:
            form = AuthenticationForm()
            request.session.set_test_cookie()
            return render(request, 'login.html', {'form':form})

    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            write_log(request, request.user, _(u'Вход в систему'))
            LoginLog.write(request)
            # Пользователь-ответственный в любом случае отправляется на
            # front-end api, настроено front-end api на сервере или нет.
            # В коде Django для этого пользователя ничего нет
            next_url_default = get_front_end_url(request) if is_cabinet_user(user) else '/'
            next_url = request.GET.get("redirectUrl", next_url_default)
            if next_url == '/logout/':
                next_url = next_url_default
            return redirect(next_url)
        return self.get(request, *args, **kwargs)

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
        if request.GET.get("redirectUrl"):
            response = redirect(request.GET.get("redirectUrl"))
        elif settings.REDIRECT_LOGIN_TO_FRONT_END:
            response = redirect(get_front_end_url(request) + '#/signout')
            response.delete_cookie('pdsession')
        else:
            response = redirect('/')
        return response

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
            for p_status in ProductStatus.objects.filter(ugh=request.user.profile.org,
                                                         product__loru__in=removed_lorus):
                ProductHistory.objects.create(
                    product=p_status.product,
                    ugh=p_status.ugh,
                    operation=ProductHistory.PRODUCT_OPERATION_DELETE,
                    dt=datetime.datetime.now(),
                    publish_cost='0.0',
                    currency=p_status.ugh.currency,
                )

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

        return HttpResponse(json.dumps([{'value': c.pk if exact else c.name} for c in orgs[:20]]), mimetype='text/javascript')

autocomplete_org = AutocompleteOrg.as_view()

class AutocompleteLoruInBurials(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('query')
        if query and request.user.profile.is_ugh():
            lorus = Burial.objects.filter(ugh=request.user.profile.org, loru__name__icontains=query).\
                                  order_by('loru__name').values('loru__name').distinct()
        else:
            lorus = Org.objects.none()

        return HttpResponse(
            json.dumps([{'value': loru['loru__name']} for loru in lorus[:20]]),
            mimetype='text/javascript',
        )

autocomplete_loru_in_burials = AutocompleteLoruInBurials.as_view()

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
        # Поля адреса вплоть до города обязательны, но
        # вдруг мы от этой обязательности откажемся, посему if...:
        if form.address_form.cleaned_data.get('country_name'):
            obj.org_address = form.address_form.save()
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
        if registrant.status == RegisterProfile.STATUS_APPROVED:
            messages.error(request, _(u'Заявка уже одобрена'))
        elif registrant.status != RegisterProfile.STATUS_CONFIRMED:
            messages.error(request, _(u'Статус заявки (%s) не соответствует ее одобрению') % \
                registrant.get_status_display()
            )
        else:
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
            org.create_wallet_rate()
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

class OrgCurrentStatsView(SupervisorRequiredMixin, TemplateView):
    template_name = 'org_current_stats.html'

    def get_context_data(self, **kwargs):
        sort = self.request.GET.get('sort', 'org')
        SORT_FIELDS = {
            'org': 'name',
            '-org': '-name',
            'city': 'off_address__city',
            '-city': '-off_address__city',
       }
        s = SORT_FIELDS[sort]
        if not isinstance(s, list):
            s = [s]

        orgs = []
        total={}
        for source_type in Burial.SOURCE_TYPES:
            total[source_type[0]] = 0
        total['oms_count'] = total['cemeteries_count'] = \
        total['areas_count'] = total['places_count'] = \
        total['burials_count'] = total['places_cabinet_count'] = 0
        q_published = Q(
            productstatus__status__in=\
            (ProductHistory.PRODUCT_OPERATION_PUBLISH, ProductHistory.PRODUCT_OPERATION_UPDATE, )
        )
        for o in Org.objects.filter(type=Org.PROFILE_UGH).order_by(*s):
            total['oms_count'] += 1
            org = {'name': o.name}
            org['city'] = o.off_address and o.off_address.city or ''

            org['num_cemeteries'] = Cemetery.objects.filter(ugh=o).count()
            total['cemeteries_count'] += org['num_cemeteries']

            org['num_areas'] = Area.objects.filter(cemetery__ugh=o).count()
            total['areas_count'] += org['num_areas']

            org['num_places'] = Place.objects.filter(cemetery__ugh=o).count()
            total['places_count'] += org['num_places']

            org['num_burials'] = Burial.objects.filter(
                ugh=o,
                status=Burial.STATUS_CLOSED
            ).count()
            total['burials_count'] += org['num_burials']

            cabinets = Place.objects.filter(
                cemetery__ugh=o,
                responsible__login_phone__isnull=False,
            )
            org['num_places_cabinet'] = cabinets.count()
            total['places_cabinet_count'] += org['num_places_cabinet']

            # вместо:
            # User.objects.filter(username__in=\
            #    cabinets.distinct('responsible__login_phone').
            #    order_by('responsible__login_phone').
            #    values_list('responsible__login_phone')
            # )
            # применяем этот сырой запрос из-за cast(string to decimal)
            #
            query = r"""SELECT COUNT(*) FROM "auth_user"
                        WHERE "auth_user"."username" ~ E'^\\d+$'
                        and cast("auth_user"."username" as decimal) IN 
                        (SELECT DISTINCT ON (U1."login_phone") U1."login_phone" FROM 
                        "burials_place" U0 LEFT OUTER JOIN "persons_aliveperson" U1 
                        ON (U0."responsible_id" = U1."baseperson_ptr_id") 
                        INNER JOIN "burials_cemetery" U2 ON (U0."cemetery_id" = U2."id")
                        WHERE (U1."login_phone" IS NOT NULL AND U2."ugh_id" = %s ))
                     """ % o.pk
            cursor = connection.cursor()
            cursor.execute(query)
            org['num_cabinets'] = cursor.fetchone()[0]

            org['num_lorus'] = ProfileLORU.objects.filter(ugh=o).count()
            
            products = Product.objects.filter(loru__ugh_list__ugh=o)
            org['num_products'] = products.distinct().count()
            org['num_published_products'] = products.filter(q_published).distinct().count()

            orgs.append(org)

        lorus = Org.objects.filter(type=Org.PROFILE_LORU)
        total['lorus_count'] = lorus.count()
        total['active_lorus_count'] = lorus.filter(profile__user__is_active=True).count()
        
        total['cabinets_count'] = CustomerProfile.objects.all().count()
        total['products_count'] = Product.objects.all().count()
        total['published_products_count'] = Product.objects.filter(q_published).distinct().count()

        return {
            'orgs':orgs,
            'total': total,
            'sort': sort,
        }

org_current_stats = OrgCurrentStatsView.as_view()

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

class TestCaptchaView(FormView):
    """
    Форма тестирования captcha
    
    Без этой простой страницы трудно, если не невозможно
    увидеть и challenge-код капчи и правильный ответ пользователя.
    Правильный ответ -- в графике! И еще: повтор правильных
    challenge и ответа приведет к неверному срабатыванию капчи.
    """
    form_class = TestCaptchaForm
    template_name = 'testcaptcha.html'

    def get_success_url(self):
        return reverse('testcaptcha')

testcaptcha = TestCaptchaView.as_view()

class ApiEducation(APIView):
    """
    Передать json- массив пунктов видеокурса

    Примерный вид получаемого массива:    
    [
        {
            “type”: "category",
            “title”: "Вступление”,
            “order”: 1,
            “items”: [
                {
                    “type”: “item”,
                    “title”: “Начало работы”,
                    “text”: “Речь диктора...”,
                    “url”:
                        [
                            “http://example.com/video.mp4”,
                            “http://example.com/video.webm”,
                            “http://example.com/video.ogg”
                        ],
                    “order”: 1
                },
                ... # следующий пункт
         },
         ... # следующая категория (заголовок)
     ]
     
    Структура двухуровневая:
        заголовок (category)
            пункт (item)
            пункт (item)
            ...
        заголовок (category)
            пункт (item)
            ...
    Теоретически может начинаться с пунктов:
        пункт
        пункт
        заголовок
            пункт
    """
    
    permission_classes = (IsAuthenticated,)
    
    FOLDER_EDU = 'support'

    @classmethod
    def get_description(cls, request):
        """
        получить массив заголовков и пунктов
        
        Читаем csv файл со следующими полями:
            0   тип пользователя, для которого курс, loru или oms (вычисляется из request)
            1   заголовок или краткое описание пункта
            2   текст диктора, если это пункт (не учитывается, если заголовок:)
            3   имя_файла.mp4 с видеороликом (если пусто, значит это заголовок, иначе пункт)
            
        Параметр host: http(s)://hostname.org
        """
        data = []
        try:
            request.user.profile
            type_ = 'oms' if request.user.profile.is_ugh() else 'loru'
            host = u"%s://%s" % ('https' if request.is_secure() else 'http', request.get_host(), )
            try:
                f_description = open(os.path.join(settings.MEDIA_ROOT, cls.FOLDER_EDU, 'description.csv'), "rb")
                csv_reader = csv.reader(f_description)
                # 
                order_titles = 0
                order_items = 0
                cur_title = None
                for row in csv_reader:
                    if row[0] == type_:
                        if not row[3]:
                            data.append({
                                'type': 'category', 
                                'title': row[1],
                                'order': order_titles + 1,
                                'items': []
                            })
                            cur_title = data[order_titles]
                            order_titles += 1
                            order_items = 0
                        else:
                            append_to = cur_title['items'] if cur_title else data
                            url =  u"%s/media/%s/video/%s/%s" % (host, cls.FOLDER_EDU, type_, row[3], ), 
                            append_to.append({
                                'type': 'item', 
                                'title': row[1],
                                'text': row[2],
                                'urls':  [
                                    { 'url': u"%s.mp4" % url, 'type': 'mp4' },
                                    { 'url': u"%s.webm" % url, 'type': 'webm' },
                                    { 'url': u"%s.ogg" % url, 'type': 'ogg' },
                                 ],
                                'order': order_items + 1 if cur_title else order_titles + 1
                            })
                            if cur_title:
                                order_items += 1
                            else:
                                order_titles += 1
                f_description.close()
            except IOError:
                pass
        except (AttributeError, Profile.DoesNotExist, ):
            pass
        return data

    def get(self, request):
        return Response(data=ApiEducation.get_description(request), status=200)
    
api_education = ApiEducation.as_view()

class Tutorial(TemplateView):
    template_name = 'tutorial.html'

    def get(self, request, *args, **kwargs):
        data = ApiEducation.get_description(request)
        return self.render_to_response({'data': data})

tutorial = Tutorial.as_view()

