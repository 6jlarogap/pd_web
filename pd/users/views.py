# -*- coding: utf-8 -*-
import json
import datetime
import random
import string
import decimal
import hashlib
import os
import csv
import copy
import re
from urllib import quote_plus, unquote_plus, urlencode
import urllib2
from qsstats import QuerySetStats

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.sessions.models import Session
from django.core.validators import validate_email
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction, connection, IntegrityError
from django.db.models import Sum
from django.db.models.query_utils import Q
from django.db.models.aggregates import Count
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode
from django.utils.formats import number_format
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import UpdateView, CreateView, FormView
from django.views.generic.detail import DetailView
from django.views.decorators.cache import cache_page

from wkhtmltopdf.views import PDFTemplateResponse

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser

from logs.models import LogOperation, Log, write_log, LoginLog
from users.forms import RegisterForm, LoruFormset, BankAccountFormset, OrgForm, \
                        OrgLogForm, LoginLogForm, OrgBurialStatsForm, SupportForm, \
                        TestCaptchaForm, TestCaptcha2Form, \
                        LoruOrdersStatsForm, ProfileDataForm, OmsOperStats, \
                        VideoSearchForm, ThanksForm
from users.models import Profile, Org, RegisterProfile, ProfileLORU, CustomerProfile, Store, \
                         get_mail_footer, is_cabinet_user, is_loru_user, is_ugh_user, \
                         PermitIfTrade, PermitIfTradeOrSupervisor, PermitIfLoruOrUgh, \
                         PermitIfCabinet, PermitIfTradeOrCabinet, Oauth, OrgAbility, \
                         BankAccount, BankAccountRegister, OrgCertificate, OrgContract, \
                         RegisterProfileContract, RegisterProfileScan, FavoriteSupplier, \
                         UserPhoto, OrgGallery, OrgReview, Role, ThankUser, Thank, \
                         is_supervisor, get_default_currency, get_profile, \
                         YoutubeVideo, YoutubeVote, YoutubeCaption, YoutubeCaptionVote, \
                         PermitIfSupervisor
from pd.models import validate_phone_as_number, validate_username
from pd.utils import host_country_code, phones_from_text, EmailMessage, get_image, SeriesTable, \
                     utcstr2local, utcisoformat, dictfetchall
from persons.models import AlivePerson, Phone, CustomPlace, CustomPerson
from burials.models import Cemetery, Area, Burial, Place, Grave
from billing.models import Wallet, Rate, Currency
from orders.models import Product, Order, Service, ProductCategory
from pd.views import PaginateListView, RequestToFormMixin, FormInvalidMixin, \
                     get_front_end_host, get_front_end_url, ServiceException
from pd.youtube import Youtube
from geo.models import Location, Country

from users.serializers import StoreSerializer, Store2Serializer, \
                              OrgSerializer, OrgShort2Serializer, \
                              OrgShort3Serializer, OrgOptSupplierSerializer, OrgShort5Serializer, \
                              UserSettingsSerializer, ShopSerializer, OrgGallerySerializer, \
                              ShopDetailSerializer, OrgReviewSerializer, \
                              OrgClientSiteSerializer, ProfileClientSiteSerializer, \
                              UserSettings2Serializer, OauthSerializer, \
                              YoutubeVoteSerializer, YoutubeVideoSerializer, \
                              YoutubeCaptionSerializer, YoutubeCaptionVoteSerializer, \
                              SocialUserSerializer

from sms_service.utils import send_sms

User._meta.get_field_by_name('email')[0]._unique = True
User._meta.get_field_by_name('email')[0].null=True

class SupervisorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if is_supervisor(request.user):
            return View.dispatch(self, request, *args, **kwargs)
        raise Http404

class SupervisorProductionRequiredMixin:
    """
    Быть и супервизором на основном (производственном) сайте
    """
    def dispatch(self, request, *args, **kwargs):
        if is_supervisor(request.user) and settings.PRODUCTION_SITE:
            return View.dispatch(self, request, *args, **kwargs)
        raise Http404

class UGHRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not is_ugh_user(request.user):
            return redirect('/')
        return View.dispatch(self, request, *args, **kwargs)

class UghOrLoruRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if is_ugh_user(request.user) or is_loru_user(request.user):
            return View.dispatch(self, request, *args, **kwargs)
        return redirect('/')

class CheckRecaptchaMixin(object):

    def check_recaptcha(self, request, challenge, response):
        forwarded_ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_ip:
            remote_ip = forwarded_ip
        else:
            remote_ip = request.META.get('REMOTE_ADDR', '')
        use_ssl = getattr(settings, 'RECAPTCHA_USE_SSL', False)
        private_key = settings.RECAPTCHA_PRIVATE_KEY
        from captcha.client import submit
        return submit(
                smart_unicode(challenge),
                smart_unicode(response),
                private_key=private_key,
                remoteip=remote_ip,
                use_ssl=use_ssl
        ).is_valid

class CheckRecaptcha2Mixin(object):

    def check_recaptcha(self, request, g_nocaptcha_response_value):
        forwarded_ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_ip:
            remote_ip = forwarded_ip
        else:
            remote_ip = request.META.get('REMOTE_ADDR', '')
        secret_key = settings.RECAPTCHA_PRIVATE_KEY
        from nocaptcha_recaptcha.client import submit
        return submit(
                g_nocaptcha_response_value=smart_unicode(g_nocaptcha_response_value),
                secret_key=secret_key,
                remoteip=remote_ip,
        ).is_valid

class SessionDataMixin(object):

    def session_data(self, user):
        if is_cabinet_user(user):
            pr = user.customerprofile
            role = 'ROLE_CLIENT'
        elif is_ugh_user(user):
            role = u'ROLE_OMS'
            pr = user.profile
        elif is_loru_user(user):
            role = u'ROLE_LORU'
            pr = user.profile
        else:
            raise Exception(u'Unknown role')

        profile = dict(
            id=user.pk,
            email=user.email or None,
        )
        profile['lastname'] = pr.user_last_name or user.last_name or None
        profile['firstname'] = pr.user_first_name or user.first_name or None
        profile['middlename'] = pr.user_middle_name or None
        org_abilities = []
        try:
            profile['photo'] = self.request.build_absolute_uri(UserPhoto.objects.get(user=user).bfile.url)
        except UserPhoto.DoesNotExist:
            profile['photo'] = None
        profile['username'] = pr.user.username
        if role == 'ROLE_CLIENT':
            org = { 'id': None, 'name': None, 'location': None }
            profile['mainPhone'] = pr.login_phone
        else:
            org = { 'id': user.profile.org.pk, 'name': user.profile.org.name or None }
            org_abilities = [ f.name for f in pr.org.ability.all() ]
            if user.profile.org.off_address:
                org['location'] = {
                    'address': unicode(user.profile.org.off_address),
                    'coords': {
                        'longitude': user.profile.org.off_address.gps_x,
                        'latitude': user.profile.org.off_address.gps_y,
                    },
                }
            else:
                org['location'] = None
            profile['mainPhone'] = None

        token, created = Token.objects.get_or_create(user=user)
        return {
            'token': token.key,
            'sessionId': self.request.session._get_or_create_session_key(),
            'sessionName': settings.SESSION_COOKIE_NAME,
            'profile': profile,
            'org': org,
            'role': role,
            'orgAbilities': org_abilities,
            'isSupervisor': is_supervisor(user),
            }

class ApiAuthSigninView(SessionDataMixin, APIView):

    def do_post(self, request, user=None):
        """
        Выполнить 'обычную' авторизацию, если не задан объект user как параметр,
        иначе только создать при необходимости token и вернуть данные
        """
        valid = False
        data = dict(status='error')
        status_code = 400
        message = ''
         # Так надо для login() без предварительного authenticate()
        user_backend = 'django.contrib.auth.backends.ModelBackend'
        confirm_tc = True # пока нет во front-end пользовательского соглашения: request.DATA.get('confirmTC')
        oauth = request.DATA.get('oauth')
        password = None
        if user:
            user.backend = user_backend
        else:
            username = request.DATA.get('username')
            password = request.DATA.get('password')
            if username and password:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    data['message'] = _(u"Пользователь %s отсутствует в системе") % username
                    data['errorCode'] = 'wrong_username'
            elif oauth:
                user, oauth_rec, message = Oauth.check_token(
                    oauth,
                )
            if oauth and user:
                user.backend = user_backend
        if user:
            if user.is_active:
                if password:
                    user = authenticate(username=username, password=password)
                    if not user:
                        data['message'] = _(u"Неверный пароль")
                        data['errorCode'] = 'wrong_password'
                valid = bool(user)
            else:
                data['message'] = _(u'Пользователь не активен')
                data['errorCode'] = 'user_not_active'
        if valid:
            tc_confirmed = True
            if is_cabinet_user(user):
                if user.customerprofile.tc_confirmed:
                    pass
                elif confirm_tc:
                    user.customerprofile.tc_confirmed = datetime.datetime.now()
                    user.customerprofile.save()
                else:
                    tc_confirmed = False
            if tc_confirmed:
                login(request, user)
                data.update(self.session_data(user))
                data['status'] = 'success'
                status_code = 200
                write_log(request, user, _(u'Вход в систему'))
                LoginLog.write(request)
            else:
                data['message'] = data['errorCode'] = 'unconfirmed_tc'
        elif oauth and not user:
            data['message'] = message
        elif not data.get('message'):
            data['message'] = 'Unknown Error'
            data['errorCode'] = 'unknown_error'
        if not data.get('message'):
            data['utctime'] = utcisoformat(datetime.datetime.now(), remove_mcsec=False)
        return Response(data=data, status=status_code)

    def post(self, request):
        return self.do_post(request)

api_auth_signin = ApiAuthSigninView.as_view()

class ApiAuthSessionsView(SessionDataMixin, APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        data = self.session_data(request.user)
        data['status'] = 'success'
        return Response(data=data, status=200)

api_auth_sessions = ApiAuthSessionsView.as_view()

class ApiAuthSignoutView(APIView):

    def post(self, request):
        user=request.user
        if request.user.is_authenticated():
            # print u'DEBUG: %s:%s /API/AUTH/SIGNOUT' % (request.get_host(), request.user.username, )
            logout(request)
            Token.objects.filter(user=user).delete()
        return Response(data={}, status=200)

api_auth_signout = ApiAuthSignoutView.as_view()

class ApiThankMixin(object):

    def get_thanked(self, request, must_thank=True):
        thank_got = request.DATA.get('thank') or \
                    request.GET.get('thank') or \
                    request.DATA.get('thankToken') or \
                    request.GET.get('thankToken')
        if not thank_got:
            if must_thank:
                raise ServiceException(_(u"Не задана персона, которой выражается благодарность"))
            else:
                return None
        try:
            thanked = CustomPerson.objects.get(token=thank_got)
        except CustomPerson.DoesNotExist:
            raise ServiceException(_(u"Не найдена персона, которой выражается благодарность"))
        return thanked

    def get_from_qs(self, request):
        """
        Получить queryset для поиска в таблице Thank

        Пагинация:
        -   Если передается и from и limit одновременно,
            то отдавать пользоватей от этой даты к более ранним пользователям
        -   Если передается только limit - то отдавать последних {limit} пользователей
        -   Если предается только from - то отдавать пользователей от даты {from}
            по текущий момент всех пользователей
        """
        from_ = request.GET.get('from')
        limit = request.GET.get('limit')
        qs = Q()
        if from_:
            from_dt = utcstr2local(from_)
            if not from_dt:
                raise ServiceException(_(u"Неверное время from"))
            if limit:
                # from_ & limit: отдавать пользоватей от этой даты к более ранним пользователям
                qs =Q(dt_created__lt=from_dt)
            else:
                # from_ & !limit: от from по текущий момент всех пользователей
                qs =Q(dt_created__gt=from_dt)
        return qs

class ApiCabinetGetcodeView(ApiThankMixin, APIView):

    @transaction.commit_on_success
    def post(self, request):
        status_code = 200
        data = {}
        try:
            login_phone = request.DATA.get('phone', '').strip().lstrip('+')
            thanked = self.get_thanked(request, must_thank=False)
            site = thanked.thank_site if thanked and thanked.thank_site else 'GoraTsvetov'
            # отправитель в смс, до 11 символов. Если больше обрежетсся при отправке
            # http://gorastalina.ru -> gorastalina
            sender_name = re.sub(r'^https?\://', '', site, flags=re.I)
            sender_name = re.sub(r'\.\S+$', '', sender_name)
            data['site'] = site
            try:
                validate_phone_as_number(login_phone)
            except (TypeError, decimal.InvalidOperation, ValidationError, ):
                raise ServiceException(_(u'Неверный формат телефона'))
            data['phone'] = login_phone
            chars = string.digits
            code = ''.join(random.choice(chars) for x in range(6))

            sms_text=u"%s code: %s" % (site, code,)
            if settings.DEBUG:
                data['code'] = code
                data['sms_sender_name'] = sender_name
                data['sms_text'] = sms_text
            else:
                sent, message = send_sms(
                    phone_number=login_phone,
                    text=sms_text,
                    email_error_text=site,
                    sender_name=sender_name,
                    # Возможно много регистраций, из разных стран,
                    # но не все у нас подключены к смс сервису.
                    # Тогда будет много сообщений об ошибках.
                    # Посему не отправлять письма об ошибках
                    # ссмс сервиса на администраторов
                    error_email=False,
                )
                if message:
                    raise ServiceException(message)
            password = make_password(code)
            thankuser, created_ = ThankUser.objects.get_or_create(
                login_phone=login_phone,
                defaults=dict(
                    password=password
            ))
            if not created_:
                thankuser.password = password
                thankuser.save()
        except ServiceException as excpt:
            transaction.rollback()
            data = dict(message=excpt.message)
            status_code = 400
        return Response(data=data, status=status_code)

api_cabinet_getcode = ApiCabinetGetcodeView.as_view()

class ApiCabinetTokensView(ApiThankMixin, APIView):

    @transaction.commit_on_success
    def post(self, request):
        """
        Авторизация пользователя с кодом, полученным на телефон

        -   Если пользователь авторизован, успех.
            * если при этом о передал oauth параметры, то прикрепляем
              его oauth данные
        -   Если переданы oauth данные, то авторизуем его по oauth или,
            если такого нет в системе, создаем пользователя
        -   Если переданы phone & token:
            *   Ищем phone, code в таблице ThankUser, 
                строка в которой могла появиться из /api/cabinet/getcode.
            *   Если есть телефон в той таблице, то сверяем код. Код неверный: отказ.
            *   Если есть телефон и верный код, то пускаем в систему,
                создаем нового кабинетчика, если нет такого кабинетчика в базе,
                с паролем == коду. Если такой кабинетчик есть, то пароль его не меняем.
            *   Если телефона нет в той таблице, то телефон и код есть login_phone и пароль.
        """
        try:
            if request.user.is_authenticated():
                user = request.user
                if request.DATA.get('oauth'):
                    user_rec, oauth_rec, message = Oauth.check_token(
                        oauth_dict=request.DATA['oauth'],
                        bind_dict=dict(
                            user=user,
                    ))
            elif request.DATA.get('oauth'):
                user, oauth_rec, message = Oauth.check_token(
                    oauth_dict=request.DATA['oauth'],
                    signup_dict=dict(
                        signup_if_absent=True,
                ))
                if message:
                    raise ServiceException(message)
            else:
                login_phone = request.DATA.get('phone', '').strip().lstrip('+')
                password = request.DATA.get('code')
                if not login_phone or not password:
                    raise ServiceException(_(u'Не заданы phone и code'))
                try:
                    validate_phone_as_number(login_phone)
                except (TypeError, decimal.InvalidOperation, ValidationError, ):
                    raise ServiceException(_(u'Неверный формат телефона'))
                try:
                    thankuser = ThankUser.objects.get(login_phone=login_phone)
                    if check_password(password, thankuser.password):
                        try:
                            customerprofile = CustomerProfile.objects.get(
                                login_phone=login_phone
                            )
                            user = customerprofile.user
                        except CustomerProfile.DoesNotExist:
                            try:
                                user = User.objects.create(
                                    username=login_phone,
                                    password=thankuser.password,
                                )
                                CustomerProfile.objects.create(
                                    user=user,
                                    login_phone=login_phone,
                                    tc_confirmed=datetime.datetime.now(), 
                                )
                            except IntegrityError:
                                # Такое возможно, но маловероятно.
                                # Если был username = login_phone1,
                                # сменил телефон на login_phone2, имя пользователя
                                # осталось прежним, а сейчас идет с login_phone1
                                raise ServiceException(
                                    'Пользователь с таким телефоном как именем входа уже имеется'
                                )
                    else:
                        raise ServiceException(_(u"Неверный код"))
                except ThankUser.DoesNotExist:
                    try:
                        customerprofile = CustomerProfile.objects.get(
                            login_phone=login_phone
                        )
                        user = authenticate(
                            username=customerprofile.user.username,
                            password=password,
                        )
                        if not user:
                            raise ServiceException(_(u"Неверный код (пароль)"))
                    except CustomerProfile.DoesNotExist:
                        raise ServiceException(_(u"Не найден телефон среди пользователей"))

            if not user.is_active:
                raise ServiceException(dict(
                    message=_(u"Пользователю закрыт вход в систему"),
                    errorCode=u'user_not_active'
                ))

            if not request.user.is_authenticated():
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                write_log(request, user, _(u'Вход в систему'))
                LoginLog.write(request)

            # Успешная авторизация, благодарим, если пришел thankToken!
            thanked = self.get_thanked(request, must_thank=False)
            is_already_counted = False
            if thanked:
                thank, created_  = Thank.objects.get_or_create(
                    user=user,
                    customperson=thanked,
                )
                if not created_:
                    # update thank.dt_modifiled
                    is_already_counted = True
                    thank.save()

            data=dict(
                userId=user.pk,
                authToken=Token.objects.get_or_create(user=user)[0].key,
                isCounted=is_already_counted,
            )
            status_code = 200
        except ServiceException as excpt:
            transaction.rollback()
            data = excpt.message
            if isinstance(data, basestring):
                data = dict(message=data)
            status_code = 400
        return Response(data=data, status=status_code)

api_cabinet_tokens = ApiCabinetTokensView.as_view()

class ApiAuthCookiesView(APIView):
    permission_classes = (IsAuthenticated,)

    def do_it(self, request, token=None):
        user_token, created = Token.objects.get_or_create(user=request.user)
        if token is not None and (created or token != user_token.key):
            return Response(
                status=400,
                data=dict(
                    status='error',
                    message=_(u"Несовпадение переданного токена и токена пользователя")
            ))
        # Пользователь может быть is_authenticated, но если зашел через Token,
        # то его сессия не будет аутентифицированной
        session_key = request.session._get_or_create_session_key()
        try:
            session = Session.objects.get(session_key=session_key)
        except Session.DoesNotExist:
            session = None
        if not session or not session.get_decoded().get('_auth_user_id'):
            request.user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, request.user)
        response = Response(data={}, status=200)
        response.set_cookie(
            'client_auth_token',
            user_token.key,
            secure=settings.SESSION_COOKIE_SECURE or None,
            max_age = settings.SESSION_COOKIE_AGE,
            domain=u".%s" % re.sub(r'\:\d+$','', get_front_end_host(request)),
        )
        # Такую куку отдает back-end ?
        #response.set_cookie(
            #settings.SESSION_COOKIE_NAME,
            #session_key,
            #secure=settings.SESSION_COOKIE_SECURE or None,
            #max_age=settings.SESSION_COOKIE_AGE,
            #domain=re.sub(r'\:\d+$','', request.get_host()),
        #)
        return response

    def post(self, request):
        return self.do_it(request)

    def get(self, request):
        token=request.GET.get('token') or ''
        return self.do_it(request, token=token)

api_auth_cookies = ApiAuthCookiesView.as_view()

class ApiAuthSignupView(CheckRecaptcha2Mixin, ApiAuthSigninView):
    """
    Регистрация пользователя-кабинетчика (физического лица)
    """
    def post(self, request):
        data = dict(status='error')
        status_code = 400
        username = request.DATA.get('username')
        password = request.DATA.get('password')
        profile = request.DATA.get('profile')
        try:
            if profile and profile.get('email'):
                try:
                    validate_email(profile['email'])
                except ValidationError:
                    raise ServiceException(_(u'Неверный формат адреса электронной почты'))
            oauth = request.DATA.get('oauth')
            recaptcha_data = request.DATA.get('captchaData')
            if oauth:
                user, oauth_rec, message = Oauth.check_token(
                    oauth,
                    signup_dict=dict(
                        username=username,
                        password=password,
                        profile=profile,
                    ),
                )
                if message:
                    raise ServiceException(message)
                return super(ApiAuthSignupView, self).do_post(request, user)
            elif recaptcha_data and isinstance(recaptcha_data, basestring):
                if not self.check_recaptcha(request, recaptcha_data):
                    raise ServiceException(_(u'Введена неверная captcha'))
                try:
                    email = profile and profile.get('email') or ''
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults = {
                            'email': email,
                        }
                    )
                except IntegrityError:
                    raise ServiceException(_(u'Есть уже пользователь с таким email: %s') % email)
                if not created:
                    raise ServiceException(_(u'Такой пользователь, %s, уже имеется') % username)
                if password:
                    user.set_password(password)
                    user.save()
                kwargs = {}
                if profile:
                    kwargs.update({
                        'user_last_name': profile.get('lastname', ''),
                        'user_first_name': profile.get('firstname', ''),
                        'user_middle_name': profile.get('middlename', ''),
                    })
                CustomerProfile.objects.create(
                    user=user,
                    tc_confirmed = datetime.datetime.now(),
                    **kwargs
                )
                return super(ApiAuthSignupView, self).do_post(request)
            else:
                raise ServiceException(_(u'Регистрация пользователя без captcha или стороннего провайдера не предусмотрена'))
        except ServiceException as excpt:
            data['message'] = excpt.message
        return Response(data=data, status=status_code)

api_auth_signup = ApiAuthSignupView.as_view()
    
class ApiProfileView(APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request):
        profile = request.user.customerprofile
        data = {
            'id': request.user.pk,
        }
        try:
            data['photo'] = request.build_absolute_uri(UserPhoto.objects.get(user=request.user).bfile.url)
        except UserPhoto.DoesNotExist:
            data['photo'] = None
        data['lastName'] = profile.user_last_name
        data['firstName'] = profile.user_first_name
        data['middleName'] = profile.user_middle_name
        data['loginPhone'] = request.user.customerprofile.login_phone
        data['username'] = request.user.username

        return Response(status=200, data=data)

api_profile = ApiProfileView.as_view()

class ApiSettingsOauthProvidersView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = dict(status='error')
        status_code = 400
        user, oauth_rec, message = Oauth.check_token(
            request.DATA,
            bind_dict=dict(
                user=request.user,
            ),
        )
        if message:
            data.update(message)
        else:
            status_code = 200
            data['status'] = 'success'
            data['username'] = oauth_rec.get_display_name()
        return Response(data=data, status=status_code)
        
api_settings_oauth_providers = ApiSettingsOauthProvidersView.as_view()

class ApiSettingsOauthProvidersDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, provider):
        providers = Oauth.objects.filter(user=request.user, provider=provider)
        if providers:
            providers.delete()
            return Response(data={'status': 'success'}, status=200)
        else:
            return Response(
                data={'status': 'error', 'message': _(u'Нет такого провайдера')},
                status=400,
            )

api_settings_oauth_providers_delete = ApiSettingsOauthProvidersDeleteView.as_view()

class ApiCabinetUsersMixin(object):

    def get_user(self, pk):
        user = get_object_or_404(User, pk=pk)
        if user != self.request.user:
            raise PermissionDenied
        return user

class ApiCabinetOauth(ApiCabinetUsersMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        user = self.get_user(pk)
        return Response(OauthSerializer(
            Oauth.objects.filter(user=user).order_by('provider'),
            many=True).data
        )

    def post(self, request, pk):
        user = self.get_user(pk)
        data = dict()
        user, oauth_rec, message = Oauth.check_token(
            request.DATA,
            bind_dict=dict(
                user=user,
            ),
        )
        if message:
            data = message
            status_code = 400
        else:
            status_code = 200
            data = OauthSerializer(oauth_rec).data
        return Response(data=data, status=status_code)

api_cabinet_oauth = ApiCabinetOauth.as_view()

class ApiCabinetOauthDetail(ApiCabinetUsersMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, user_id, oauth_id):
        user = self.get_user(user_id)
        oauth_rec = get_object_or_404(Oauth, pk=oauth_id, user=user)
        oauth_rec.delete()
        return Response({})

api_cabinet_oauth_detail = ApiCabinetOauthDetail.as_view()

class ApiSettings(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, JSONParser, )
    
    def get(self, request):
        data = dict(oauthProviders=[])
        for provider in Oauth.objects.filter(user=request.user):
            info = {
                'id': provider.provider,
                'username': provider.get_display_name(),
            }
            data['oauthProviders'].append(info)
        return Response(data=data, status=200)
        
    @transaction.commit_on_success
    def put(self, request):
        """
        Поменять данные пользователя
        
        Input data
        {
           "avatar",
                - None в json-input, тогда удаляем картинку
                - request.FILES['avatar'], в multipart-input,
                  тогда устанавляваем фото
           "username": "somebody",
           "loginPhone": "375297542270",
           "oldPassword": "1234567",
           "newPassword": "7654321",
           "lastName": "Моя-новая-фамилия",
           "firstName": "Мое-новое-имя",
           "middleName": "Мое-новое-отчество"
         }
        """
        try:
            user = request.user
            profile = get_profile(user)
            change_profile = False
            old_username = user.username
            old_password = request.DATA.get('oldPassword')
            if old_password:
                user = authenticate(username=old_username, password=old_password)
                if not user:
                    raise ServiceException(_(u'Неверно указан действующий пароль'))

            login_phone = request.DATA.get('loginPhone')
            if login_phone and is_cabinet_user(user):
                try:
                    new_login_phone = decimal.Decimal(login_phone)
                    validate_phone_as_number(new_login_phone)
                except (TypeError, decimal.InvalidOperation, ValidationError, ):
                    raise ServiceException(_(u'Неверный формат телефона'))
                old_login_phone = profile.login_phone
                if new_login_phone != old_login_phone:
                    try:
                        profile.login_phone = new_login_phone
                        change_profile = True
                        AlivePerson.objects.filter(user=user).update(login_phone=new_login_phone)
                        Place.log_login_phone_change(request, old_login_phone)
                    except IntegrityError:
                        raise ServiceException(_(u'Такой номер телефона ответственного уже имеется'))

            new_username = request.DATA.get('username')
            if new_username:
                user.username = new_username

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

            if new_password or new_username or email:
                try:
                    user.save()
                except IntegrityError:
                    raise ServiceException(_(u'Пользователь с таким именем для входа в систему уже имеется'))

            user_last_name = request.DATA.get('lastName')
            if user_last_name is not None:
                change_profile = True
                profile.user_last_name = user_last_name
            user_first_name = request.DATA.get('firstName')
            if user_first_name is not None:
                change_profile = True
                profile.user_first_name = user_first_name
            user_middle_name = request.DATA.get('middleName')
            if user_middle_name is not None:
                change_profile = True
                profile.user_middle_name = user_middle_name
            avatar = request.FILES.get('avatar')
            if avatar:
                if avatar.size > UserPhoto.MAX_SIZE * 1024 * 1024:
                    raise ServiceException(_(u"Размер изображения не должен превышать %sМб") % UserPhoto.MAX_SIZE)
                image = get_image(avatar)
                if not image:
                    raise ServiceException(_(u"Прикрепленный файл не является изображением"))
                if image.size[0] <= UserPhoto.MIN_SIZE_X:
                    raise ServiceException(_(u"Ширина картинки должна быть больше %s px") % UserPhoto.MIN_SIZE_X)
                userphoto, created_ = UserPhoto.objects.get_or_create(
                    user=user,
                    defaults=dict(
                        creator=user,
                        bfile=avatar,
                ))
                if not created_:
                    userphoto.delete_from_media()
                    userphoto.bfile.save(avatar.name, avatar)
                change_profile = True
            elif 'avatar' in request.DATA and request.DATA['avatar'] is None:
                for photo in UserPhoto.objects.filter(user=user):
                    photo.delete()
                    change_profile = True

            if change_profile:
                profile.save()
        except ServiceException as excpt:
            transaction.rollback()
            data = { 'status': 'error',
                     'message': excpt.message,
                   }
            status_code = 400
        else:
            data = UserSettingsSerializer(user,context=dict(request=request)).data
            status_code = 200
        return Response(data=data, status=status_code)

api_settings = ApiSettings.as_view()

class ApiCabinetUsersView(ApiThankMixin, APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, JSONParser, )
    
    def get(self, request, pk):
        user = request.user
        if unicode(user.pk) != unicode(pk):
            raise PermissionDenied
        data = UserSettings2Serializer(user,context=dict(request=request)).data
        status_code = 200
        return Response(data=data, status=status_code)

    @transaction.commit_on_success
    def put(self, request, pk):
        """
        Поменять данные пользователя и поблагодарить
        
        Input data
        {
           "photo",
                - None в json-input, тогда удаляем картинку
                - request.FILES['photo'], в multipart-input,
                  тогда устанавляваем фото
           "lastName": "Моя-новая-фамилия",
           "firstName": "Мое-новое-имя",
           "middleName": "Мое-новое-отчество"
           "thank": токен благодаримого
         }
        """
        try:
            user = request.user
            if unicode(user.pk) != unicode(pk):
                raise PermissionDenied
            profile = get_profile(user)
            profile_fields = dict()
            profile_map = dict(
                lastName='user_last_name',
                firstName='user_first_name',
                middleName='user_middle_name',
            )
            for f in profile_map:
                if f in request.DATA:
                    profile_fields[profile_map[f]] = request.DATA[f] or ''
            photo_changed = True
            photo = request.FILES.get('photo')
            if photo:
                if photo.size > UserPhoto.MAX_SIZE * 1024 * 1024:
                    raise ServiceException(_(u"Размер изображения не должен превышать %sМб") % UserPhoto.MAX_SIZE)
                image = get_image(photo)
                if not image:
                    raise ServiceException(_(u"Прикрепленный файл не является изображением"))
                userphoto, created_ = UserPhoto.objects.get_or_create(
                    user=user,
                    defaults=dict(
                        creator=user,
                        bfile=photo,
                ))
                if not created_:
                    userphoto.delete_from_media()
                    userphoto.bfile.save(photo.name, photo)
            elif 'photo' in request.DATA and request.DATA['photo'] is None:
                UserPhoto.objects.filter(user=user).delete()
            else:
                photo_changed = False

            if profile_fields:
                profile = get_profile(user)
                for f in profile_fields:
                    setattr(profile, f, profile_fields[f])
            if profile_fields or photo_changed:
                # При изменении фото пусть меняется тоже профиль, установится profile.dt_modified
                profile.save()

            thanked = self.get_thanked(request, must_thank=False)
            if thanked:
                thank, created_  = Thank.objects.get_or_create(
                    user=user,
                    customperson=thanked,
                )
                if not created_:
                    # update thank.dt_modifiled
                    thank.save()

            data = UserSettings2Serializer(user,context=dict(request=request)).data
            status_code = 200
        except ServiceException as excpt:
            transaction.rollback()
            data = dict(message=excpt.message)
            status_code = 400
        return Response(data=data, status=status_code)

api_cabinet_users = ApiCabinetUsersView.as_view()

class ApiThankUsersCount(ApiThankMixin, APIView):

    def get(self, request):
        """
        Число пользователей, выразивших благодарность
        """
        data = {}
        from_ = request.GET.get('from')
        try:
            thanked = self.get_thanked(request)
            from_qs = self.get_from_qs(request)
            qs = from_qs & Q(customperson=thanked, user__is_active=True)
            data = {
                'count': Thank.objects.filter(qs).distinct().count(),
                'from': request.GET.get('from'),
            }
            status_code = 200
        except ServiceException as excpt:
            data = dict(message=excpt.message)
            status_code = 400
        return Response(data=data, status=status_code)

api_thank_users_count = ApiThankUsersCount.as_view()

class ApiThankUsers(ApiThankMixin, APIView):

    def get(self, request):
        """
        Пользователи, выразившие благодарность

        По умолчанию сортировать по дате создания от последней к первой
        """
        data = []
        from_ = request.GET.get('from')
        try:
            thanked = self.get_thanked(request)
            limit = int(request.GET.get('limit', '0'))
            from_qs = self.get_from_qs(request)
            qs = from_qs & Q(customperson=thanked, user__is_active=True)
            thanks = Thank.objects.filter(qs).order_by('-dt_created').distinct()
            if limit > 0:
                thanks = thanks[:limit]
            for thank in thanks:
                item = UserSettings2Serializer(thank.user,context=dict(request=request)).data
                item.update(dict(
                    createdAt=utcisoformat(thank.dt_created, remove_mcsec=False)
                ))
                data.append(item)
            status_code = 200
        except ServiceException as excpt:
            data = dict(message=excpt.message)
            status_code = 400
        return Response(data=data, status=status_code)

api_thank_users = ApiThankUsers.as_view()

class ApiAuthUser(APIView):
    permission_classes = (PermitIfCabinet,)
    
    def delete(self, request):
        request.user.is_active = False
        old_username = request.user.username
        old_fullname = request.user.customerprofile.full_name()
        request.user.customerprofile.user_last_name = ''
        request.user.customerprofile.user_first_name = ''
        request.user.customerprofile.user_middle_name = ''
        request.user.customerprofile.save()
        request.user.email = None
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        username_max_length = User._meta.get_field('username').max_length
        while True:
            new_username  = u"%s-%s-%s" % (
                'deleted',
                request.user.username,
                ''.join(random.choice(chars) for x in range(10)),
            )
            new_username = new_username[:username_max_length]
            if not User.objects.filter(username=new_username).count():
                request.user.username = new_username
                break
        request.user.save()
        write_log(
            request,
            request.user,
            _(
                u"Пользователь кабинета, \n"
                u"логин: %(username)s\n"
                u"ФИО: %(full_name)s\n"
                u'"удален" из системы, т.е. переименован в %(new_username)s\n'
                u"с потерей права входа в систему"
            ) % dict(
                username=old_username,
                full_name=old_fullname,
                new_username=new_username,
        ))
        return Response(data={}, status=200)

api_auth_user = ApiAuthUser.as_view()

class AuthGetPasswordBySMSView(CheckRecaptcha2Mixin, APIView):
    """
    Замена существующему пользователю-кабинетчику пароля, отправка пароля по СМС
    
    Input example:
    {
        "phoneNumber": "375291234567",
        "captchaData": "03AHJ_VuvQ5p0AdejIw4W6"
    }
    Output examples:
    {
        "status: "success",
        "message": "Пароль установлен"
    }
    {
        "status: "error",
        "message": "Ваш номер телефона не указан в списке для входа."
        # or       "Введена не верная captcha"
    }
    """
    def post(self, request):
        status = 'error'
        status_code = 400
        message = ''
        login_phone = request.DATA.get('phoneNumber')
        recaptcha_data = request.DATA.get('captchaData')
        if not recaptcha_data or not isinstance(recaptcha_data, basestring):
            message = _(u'Нет данных по captcha')
        elif not self.check_recaptcha(self.request, recaptcha_data):
            message = _(u'Введена неверная captcha')
        else:
            try:
                login_phone = decimal.Decimal(login_phone)
                validate_phone_as_number(login_phone)
            except (TypeError, decimal.InvalidOperation, ValidationError, ):
                message = _(u'Неверный формат телефона')
            else:
                try:
                    customerprofile = CustomerProfile.objects.get(login_phone=login_phone)
                except CustomerProfile.DoesNotExist:
                    message = _(u'Вы не зарегистрированы в системе')
                else:
                    password = CustomerProfile.generate_password()
                    user = customerprofile.user
                    user.set_password(password)
                    user.save()
                    if not settings.DEBUG:
                        sent, message = send_sms(
                            phone_number=login_phone,
                            text=_(u'Vash parol na PohoronnoeDelo: %s') % password,
                            email_error_text = _(u"Пользователь %(username)s (телефон %(login_phone)s) "
                                                 u"не смог получить или заменить пароль" % dict(
                                                    username=user.username, login_phone=login_phone)),
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

class ApiFeedBack(CheckRecaptcha2Mixin, APIView):
    """
    Вопрос в поддержку от front-end api. Отправка письма.
    
    Пример входных данных:
    {
        "subject": "Тема",
        "text": "Текст вопроса",
        "email": "email@email.ru",
        "captchaData": "03AHJ_VuvQ5p0AdejIw4W6"
    }
    captchaData передается, если пользователь незарегистрирован
    
    Status codes:
        200 - если все нормально
        400 - если произошла ошибка валидации входных данных

    Если отправляет аутентифицированный пользователь и у него нет
    в свойствах почтового адреса, то он устанавливается в email
    из входных данных
    """
    def post(self, request):
        status_code = 400
        recaptcha_data = request.DATA.get('captchaData')
        try:
            if not request.user.is_authenticated():
                if not recaptcha_data or not isinstance(recaptcha_data, basestring):
                    raise ServiceException(_(u'Нет данных по captcha'))
                if not self.check_recaptcha(self.request, recaptcha_data):
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
                user_email = request.user.email
                if not user_email and email_from:
                    try:
                        request.user.email = email_from
                        request.user.save()
                    except IntegrityError:
                        request.user.email = user_email

                if is_cabinet_user(request.user):
                    profile = request.user.customerprofile
                else:
                    profile = request.user.profile
                    if callback:
                        if not request.user.profile.org.phones:
                            request.user.profile.org.phones = phone
                            request.user.profile.org.save()
                        if not request.user.profile.phones:
                            request.user.profile.phones = phone
                            request.user.profile.save()

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

            email_to = settings.SUPPORT_EMAILS
            headers = {}
            if email_from:
                headers['Reply-To'] = email_from
            # Если в From: поставить задавшего вопрос, например, user@yandex.ru,
            # то письмо придет в email_to (адреса гугловской почты) с "замечаниями"
            # в заголовке, что письмо пришло не от yandex, так и в спам может попасть.
            # Посему реальный отправитель будет в Reply-To:
            #
            email_from = _(u"Вопрос в поддержку <%s>") % settings.DEFAULT_FROM_EMAIL
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
    permission_classes = (PermitIfTrade,)

    """
    Вернуть массив, в котором только "ОМС" публичного каталога
    """
    def get(self, request):
        data = []
        try:
            ugh = Org.objects.filter(pk=Org.get_catalog_org_pk())[0]
            d = {
                'id': ugh.pk,
                'name': _(u'Каталог'),
                'currency': {
                    'name': ugh.currency.name,
                    'shortName': ugh.currency.short_name,
                    'code': ugh.currency.code,
                }
            }
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
        except IndexError:
            pass
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
                next_url = "?redirectUrl=%s" % \
                        quote_plus(unquote_plus(request.GET.get("redirectUrl")).encode('utf8'))
            else:
                next_url = ''
            response = redirect('%ssignout%s' % (get_front_end_url(request), next_url))
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
        user = request.user
        write_log(request, request.user, _(u'Выход из системы'))
        # print u'DEBUG: %s:%s /LOGOUT' % (request.get_host(), request.user.username, )
        logout(request)
        Token.objects.filter(user=user).delete()
        if request.GET.get("redirectUrl"):
            response = redirect(request.GET.get("redirectUrl"))
        elif settings.REDIRECT_LOGIN_TO_FRONT_END:
            response = redirect(get_front_end_url(request) + 'signout')
            response.delete_cookie('pdsession')
        else:
            response = redirect('/')
        return response

ulogout = LogoutView.as_view()

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

class ProfileEditView(UghOrLoruRequiredMixin, RequestToFormMixin, FormInvalidMixin, UpdateView):
    template_name = 'edit_profile.html'
    model = Profile
    form_class = ProfileDataForm

    def get_form_kwargs(self):
        data = super(ProfileEditView, self).get_form_kwargs()
        data['my_profile'] = self.kwargs.get('my_profile')
        return data

    def get_object(self):
        self.new_ = False
        if 'pk' in self.kwargs:
            obj = Profile.objects.get(pk=self.kwargs['pk'])
        elif 'my_profile' in self.kwargs:
            obj = self.request.user.profile
        else:
            if self.request.user.profile.is_loru() or self.request.user.profile.is_admin():
                obj = Profile()
                self.new_ = True
            else:
                raise Http404
        return obj

    def get_success_url(self):
        if self.kwargs.get('my_profile'):
            return reverse('user_profile')
        else:
            return reverse('edit_org', args=[self.request.user.profile.org.pk])

    def form_valid(self, form):
        profile = form.save()
        if profile is None:
            # Ошибка при записи, даже после предварительной проверки на уникальность
            # username & password
            messages.error(self.request, _(u'Логин пользователя или email уже используются в системе'))
            return self.get(self.request, *self.args, **self.kwargs)
        msg = _(u"<a href='%(edit_profile)s'>Пользователь %(username)s</a>: %(created_modified)s") % dict(
            edit_profile=reverse('user_profile') if self.kwargs.get('my_profile') \
                         else reverse('edit_profile', args=[self.object.pk]),
            username=self.object.user.username,
            created_modified = _(u'создан') if self.new_ else _(u'изменения сохранены'),
        )
        messages.success(self.request, msg)
        return redirect(self.get_success_url())

edit_profile = ProfileEditView.as_view()

class OrgEditView(UghOrLoruRequiredMixin, RequestToFormMixin, FormInvalidMixin, UpdateView):
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
        data['is_readonly'] = True
        if data['is_my_org']:
            data['is_readonly'] = not (is_loru_user(self.request.user) or \
                                        self.request.user.profile.is_admin())
        else:
            data['is_readonly'] = Profile.objects.filter(
                org=self.object,
                user__is_active=True,
                ).exists()
        return data

    def get_success_url(self):
        msg = _(u"<a href='%(edit_org)s'>Организация %(org)s</a> изменена") % dict(
            edit_org=reverse('edit_org', args=[self.object.pk]),
            org=self.object,
        )
        messages.success(self.request, msg)
        return reverse('edit_org', args=[self.object.pk])
        
edit_org = OrgEditView.as_view()

class AutocompleteOrg(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('query')
        type_ = request.GET.get('type')
        exact = request.GET.get('exact')
        check_inn = request.GET.get('check_inn')
        if query and (request.user.profile.is_loru() or \
                      request.user.profile.is_ugh()
                     ):
            if exact:
                q = Q(name=query)
            else:
                q = Q(name__icontains=query)
                if check_inn:
                    m = re.search(r'^(\d{4,})$', query.strip())
                    if m:
                        country_code = host_country_code(request)
                        if country_code == 'by':
                            inn_label = _(u'УНП')
                        else:
                            inn_label = _(u'ИНН')
                        q = Q(inn__startswith=m.group(1))
                    else:
                        check_inn = None
            if type_:
                q &= Q(type=type_)
            orgs = Org.objects.filter(q).order_by('name')
        else:
            orgs = Org.objects.none()

        return HttpResponse(
            json.dumps([{'value': c.pk  if exact \
                                        else u"%s%s" % (c.name, u" (%s: %s)" % (inn_label, c.inn,)  if check_inn \
                                                                                                    else "")} \
                                            for c in orgs[:20]
            ]),
            mimetype='text/javascript'
        )

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

class ReportDatesMixin(object):

    def get_dates(self):
        """
        Получить начальные даты для отчета по умолчанию

        После 15-го числа: за текущий месяц
        До 15-го числа; начиная с предыдущего месяца
        """
        date_from = datetime.date.today()
        if date_from.day < 15:
            if date_from.month > 1:
                month = date_from.month - 1
                year = date_from.year
            else:
                month = 12
                year = date_from.year - 1
            date_from = datetime.date(year, month, 1)
        else:
            date_from = datetime.date(date_from.year, date_from.month, 1)
        date_to = datetime.date.today()
        return date_from, date_to

class OrgLogView(UghOrLoruRequiredMixin, ReportDatesMixin, PaginateListView):
    template_name = 'org_log.html'
    context_object_name = 'logs'

    def get_queryset(self):
        org=self.request.user.profile.org

        self.collaborators = [ (self.request.user.pk, self.request.user.profile.last_name_initials()) ]
        cemeteries = Cemetery.editable_ugh_cemeteries(self.request.user)
        for profile in Profile.objects.filter(
                            org=org,
                            cemeteries__in=Cemetery.editable_ugh_cemeteries(self.request.user),
                            user__is_active=True,
                        ).exclude(
                            user__pk=self.request.user.pk
                        ).distinct():
            self.collaborators.append((profile.user.pk, profile.last_name_initials()))
        collaborators_pks = [ c[0] for c in self.collaborators ]
        q = Q(org=org, user__is_active=True) & ~Q(user__pk__in=collaborators_pks)
        other_users = [(profile.user.pk, profile.last_name_initials()) for profile in Profile.objects.filter(q)]
        self.choice_users = self.collaborators + other_users

        self.date_from, self.date_to = self.get_dates()

        form = self.get_form()
        if not self.request.GET:
            return Log.objects.none()

        users = [ c[0] for c in self.choice_users]

        q_users = Q(user__pk__in=users)
        if form.data and form.is_valid():
            self.date_from = form.cleaned_data.get('date_from')
            self.date_to = form.cleaned_data.get('date_to')
            q_users = Q(user__pk__in=form.cleaned_data.get('users') or [])

        logs = Log.objects.filter(q_users)
        if self.date_from:
            logs = logs.filter(dt__gte=self.date_from)
        if self.date_to:
            logs = logs.filter(dt__lt=self.date_to + datetime.timedelta(days=1))

        sort = self.request.GET.get('sort', self.SORT_DEFAULT)
        SORT_FIELDS = {
            'dt': 'dt',
            '-dt': '-dt',
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
        data = self.request.GET
        form = OrgLogForm(data=data or None)
        form.fields['users'].choices = self.choice_users
        if not data:
            form.initial['date_from'] = self.date_from
            form.initial['date_to'] = self.date_to
            form.initial['users'] = [ c[0] for c in self.collaborators ]
        return form

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
                logs = logs.filter(dt__lt=form.cleaned_data['date_to']+datetime.timedelta(days=1))

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

class OmsOperStatsView(UGHRequiredMixin, ReportDatesMixin, PaginateListView):
    template_name = 'oper_stats.html'
    context_object_name = 'dates'

    def dispatch(self, request, *args, **kwargs):
        if not settings.SHOW_OPER_STATS:
            raise Http404
        return super(OmsOperStatsView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.context_extra = None
        form = self.get_form()
        if form.data and form.is_valid():
            d_start = form.cleaned_data['date_from']
            d_end = form.cleaned_data['date_to']
        else:
            return []

        d_start = form.cleaned_data['date_from']
        d_end = form.cleaned_data['date_to']
        users = []
        for profile in Profile.objects.filter(org=self.request.user.profile.org):
            if profile.user:
                users.append(profile.user)
        q_users = Q(user__in=users)
        q_dt = Q(
            dt__gte=d_start,
            dt__lt=d_end + datetime.timedelta(days=1)
        )
        values = lambda qs: \
            QuerySetStats(qs, date_field='dt', aggregate=Count('id')). \
            time_series(d_start, d_end, interval='days')

        are_lorus_in_system = Org.objects.filter(type=Org.PROFILE_LORU).exists()

        # Раскидаем по таблицам для пользователей
        parms = [
            dict(
                name='current_burials',
                qs=Q(operation__in=(
                            LogOperation.CLOSED_BURIAL_FULL,
                            LogOperation.CLOSED_BURIAL_UGH,
                )),
                caption=_(u"Закрытые текущие захоронения") if are_lorus_in_system \
                          else _(u"Закрытые ручные захоронения"),
            ),
            dict(
                name='archive_burials',
                qs=Q(operation=LogOperation.CLOSED_BURIAL_ARCHIVE),
                caption=_(u"Закрытые архивные захоронения"),
            ),
            dict(
                name='inventoried_places',
                qs=Q(operation=LogOperation.PLACE_CREATED_MOBILE),
                caption=_(u"Места с мобильного приложения"),
            ),
            dict(
                name='inventoried_photos',
                qs=Q(operation=LogOperation.PHOTO_TO_PLACE_MOBILE),
                caption=_(u"Фото мест с мобильного приложения"),
            ),
            dict(
                name='place_certificates',
                qs=Q(operation=LogOperation.PLACE_PASSPORT_ISSUED),
                caption=_(u"Место получило ответственного, выдача паспорта места"),
            ),
        ]
        if settings.REDIRECT_LOGIN_TO_FRONT_END:
            parms += [
                dict(
                    name='rejected_photos',
                    qs=Q(operation=LogOperation.PLACE_PHOTO_REJECT),
                    caption=_(u"Брак фото, выявленный регистратором"),
                ),
                dict(
                    name='processed_places',
                    qs=Q(operation=LogOperation.PLACE_PHOTO_PROCESSED),
                    caption=_(u"Места, обработанные по фото"),
                ),
                dict(
                    name='inventoried_burials',
                    qs=Q(operation=LogOperation.BURIAL_PHOTO_PROCESSED),
                    caption=_(u"Захоронения, обработанные по фото"),
                ),
            ]
        mark = {}
        #   parm:
        #       {
        #           total:
        #           days:  [ .... ]
        #           totals:  [ .... ]
        #           users: [
        #               {
        #                   user: user
        #                   total: total
        #                   days: [ num1, num2 ... ]
        #               }
        #       ]
        #       }
        #
        for parm in parms:
            mark[parm['name']] = {}
            qs_org = Log.objects.filter(parm['qs'] & q_users)
            mark[parm['name']]['total'] = qs_org.filter(q_dt).count()
            mark[parm['name']]['values'] = values(qs_org)
            mark[parm['name']]['caption'] = parm['caption']
            if not mark[parm['name']]['total']:
                continue

            mark[parm['name']]['users'] = []
            # Только дни, в которых были результаты
            days = []
            day_totals = []
            dt = d_start
            while dt <= d_end:
                qs_day = Q(
                    dt__gte=dt,
                    dt__lt=dt + datetime.timedelta(days=1)
                )
                total = Log.objects. \
                        filter(parm['qs'] & qs_day & q_users).count()
                if total:
                    days.append(dt)
                    day_totals.append(total)
                dt = dt + datetime.timedelta(days=1)
            mark[parm['name']]['days'] = days
            mark[parm['name']]['day_totals'] = day_totals
            mark_users = []
            for user in users:
                qs_dt = q_dt
                qs_user = Q(user=user)
                total = Log.objects. \
                            filter(parm['qs'] & qs_dt & qs_user).count()
                if not total:
                    continue
                mark_user = dict(
                    user=user,
                    total=total,
                    )
                mark_user['days'] = []
                mark_user['days_users'] = []
                for dt in days:
                    qs_dt = Q(
                        dt__gte=dt,
                        dt__lt=dt + datetime.timedelta(days=1)
                    )
                    count = Log.objects. \
                                filter(parm['qs'] & qs_dt & qs_user).count()
                    mark_user['days'].append(count)
                mark_users.append(mark_user)
            mark_users.sort(key=lambda x: x['total'], reverse=True)
            mark[parm['name']]['users'] = mark_users

        self.context_extra = dict(
            mark=mark,
            parms=parms,
        )

        dates = SeriesTable(*[ mark[parm['name']]['values'] for parm in parms ])
        return dates

    def get_context_data(self, **kwargs):
        context = super(OmsOperStatsView, self).get_context_data(**kwargs)
        if self.context_extra:
            context.update(self.context_extra)
        return context

    def get_form(self):
        data = self.request.GET
        form = OmsOperStats(data=data or None)
        if data:
            form.fields['date_from'].required = True
            form.fields['date_to'].required = True
        else:
            date_from, date_to = self.get_dates()
            form.initial['date_from'] = date_from
            form.initial['date_to'] = date_to
        return form

oms_oper_stats = OmsOperStatsView.as_view()

class RegisterMixin(object):
    
    def send_email_to_confirm(self, obj):
        """
        Отправка письма с просьбой подтверждения регистрации
        """
        write_log(None, obj, _(u'%s : получена. Ожидание подтверждения') % obj)
        email_subject = u"%s %s" % (
            _(u"Подтверждение заявки на регистрацию на"),
            _(u"Похоронное Дело"),
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
        EmailMessage(email_subject, email_text, email_from, email_to).send()
        
class RegisterView(RegisterMixin, CreateView):
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
        self.send_email_to_confirm(obj)
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
                        status__in=(RegisterProfile.STATUS_APPROVED, ),
                        dt_modified__lt=datetime.datetime.now() - \
                                        datetime.timedelta(days=RegisterProfile.CLEAR_PROCESSED),):
                    r.delete()
                    write_log(
                        None,
                        self.object,
                        _(u'%(registerprofile)s : автоматическое удаление '
                          u'по истечении %(clear_processed)s дней') % dict(
                            registerprofile=r,
                            clear_processed=RegisterProfile.CLEAR_PROCESSED,
                    ))
                explain = _(
                            u'Спасибо за подтверждение заявки на регистрацию!\n'
                            u'Ваша заявка принята на <b>рассмотрение администратора системы</b>\n'
                )
                email_subject = "%s %s" % (unicode(_(u"Заявка на регистрацию в")),
                                           unicode(_(u"Похоронное Дело")),
                                          )
                try:
                    scan = self.object.registerprofilescan
                    scan = scan and scan.bfile and os.path.exists(scan.bfile.path) and scan.bfile.url or None
                except (AttributeError, RegisterProfileScan.DoesNotExist, ):
                    scan = None
                host = self.request.get_host()
                # Какие бы ни были домены первого уровня у "основного" org.pohoronnoedelo.XX,
                # ссылки в письме администратору должны вести на org.pohoronnoedelo.ru
                host = re.sub(
                    r'^org\.pohoronnoedelo\.[a-z]{2,}$',
                    r'org.pohoronnoedelo.ru',
                    host,
                    flags=re.I
                )
                email_text = render_to_string(
                                'register_notify_supervisor_email.txt',
                                { 
                                    'obj': self.object,
                                    'host': '%s://%s' % (request.is_secure() and 'https' or 'http',
                                                         host,
                                                        ),
                                    'scan': scan,
                                }
                )
                email_from = settings.DEFAULT_FROM_EMAIL
                email_to = settings.SUPPORT_EMAILS
                EmailMessage(email_subject, email_text, email_from, email_to, ).send()
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
                       ) % get_front_end_url(request)
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

    @transaction.commit_on_success
    def get(self, request, *args, **kwargs):
        registrant = get_object_or_404(RegisterProfile, pk=self.kwargs['pk'])
        if registrant.status == RegisterProfile.STATUS_APPROVED:
            messages.error(request, _(u'Заявка уже одобрена'))
        elif registrant.status != RegisterProfile.STATUS_CONFIRMED:
            messages.error(request, _(u'Статус заявки (%s) не соответствует ее одобрению') % \
                registrant.get_status_display()
            )
        else:
            try:
                registrant.status = RegisterProfile.STATUS_APPROVED
                registrant.save()
                try:
                    user, created = User.objects.get_or_create(
                                username=registrant.user_name,
                                defaults=dict(
                                    password=registrant.user_password,
                                    email=registrant.user_email or None,
                                )
                    )
                    if not created:
                        raise ServiceException(_(u"Пользователь уже в системе"))
                except IntegrityError:
                    raise ServiceException(_(u"Такой email уже имеется у кого-то из пользователей системы"))
                if registrant.org_address:
                    off_address = copy.deepcopy(registrant.org_address)
                    off_address.pk = None
                    off_address.save(force_insert=True)
                else:
                    off_address = None
                death_date_offer = True if registrant.org_type == Org.PROFILE_LORU else False
                try:
                    org=Org.objects.create(
                                type=registrant.org_type,
                                name=registrant.org_name,
                                full_name=registrant.org_full_name,
                                inn=registrant.org_inn,
                                director=registrant.org_director,
                                basis=registrant.org_basis,
                                email=registrant.user_email,
                                phones=registrant.org_phones,
                                fax=registrant.org_fax,
                                ogrn=registrant.org_ogrn,
                                off_address=off_address,
                                currency=registrant.org_currency,
                                subdomain=registrant.org_subdomain,
                                death_date_offer=death_date_offer,
                    )
                except IntegrityError:
                    raise ServiceException(_(u"Такой поддомен уже используется в системе"))
                if org.type == Org.PROFILE_UGH:
                    pd_ability = OrgAbility.objects.get(name=OrgAbility.ABILITY_PERSONAL_DATA)
                    org.ability.add(pd_ability)
                elif org.type == Org.PROFILE_LORU:
                    pd_ability = OrgAbility.objects.get(name=OrgAbility.ABILITY_TRADE)
                    org.ability.add(pd_ability)
                for bank in registrant.bankaccountregister_set.all():
                    if bank.off_address:
                        bank_address = copy.deepcopy(bank.off_address)
                        bank_address.pk = None
                        bank_address.save(force_insert=True)
                    else:
                        bank_address = None
                    BankAccount.objects.create(
                        organization=org,
                        bankname=bank.bankname,
                        rs=bank.rs,
                        bik=bank.bik,
                        ks=bank.ks,
                        off_address=bank_address,
                    )
                try:
                    fname = registrant.registerprofilescan.bfile.path
                    f = open(fname, 'r')
                    s = f.read()
                    f.close()
                    cert = OrgCertificate.objects.create(
                        creator=user,
                        org=org,
                    )
                    cert.bfile.save(os.path.basename(fname), ContentFile(s))
                except (AttributeError, RegisterProfileScan.DoesNotExist, IOError, ):
                    pass
                try:
                    fname = registrant.registerprofilecontract.bfile.path
                    f = open(fname, 'r')
                    s = f.read()
                    f.close()
                    contract = OrgContract.objects.create(
                        creator=user,
                        org=org,
                    )
                    contract.bfile.save(os.path.basename(fname), ContentFile(s))
                except (AttributeError, RegisterProfileContract.DoesNotExist, IOError, ):
                    pass
                org.create_wallet_rate()
                profile=Profile.objects.create(
                            user_last_name=registrant.user_last_name,
                            user_first_name=registrant.user_first_name,
                            user_middle_name=registrant.user_middle_name,
                            is_agent=True,
                            user=user,
                            org=org,
                            phones=registrant.org_phones,
                )
                transaction.commit()
            except ServiceException as excpt:
                transaction.rollback()
                messages.error(request, excpt.message)
            else:
                host = get_front_end_url(request)
                # Пользователю должно прийти письмо, в котором домен адреса Похоронного Дела
                # должен совпасть с доменом его страны, а не обязательно домена супервизора
                if registrant.org_address and registrant.org_address.country:
                    countries = { u'Россия': 'ru', u'Беларусь': 'by' }
                    if registrant.org_address.country.name in countries:
                        registrant_domain = countries[registrant.org_address.country.name]
                        match = re.search(r'^(https?\://[\.\w\-]+\.)(\w{2,})(\:\d{1,5})?(/)?$', host)
                        if match and match.group(2) != registrant_domain:
                            host = "%s%s%s%s" % (
                                match.group(1),
                                registrant_domain,
                                match.group(3),
                                match.group(4),
                            )
                write_log(request, registrant, _(u'%s : одобрена') % registrant)
                email_subject = unicode(_(u"Заявка на регистрацию одобрена"))
                email_text = render_to_string(
                    'register_approved_email.txt',
                    dict(
                        host=host,
                        obj=registrant,
                ))
                email_from = settings.DEFAULT_FROM_EMAIL
                email_to = (registrant.user_email, )
                EmailMessage(email_subject, email_text, email_from, email_to, ).send()
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

class OmsBurialStatsView(SupervisorProductionRequiredMixin, TemplateView):
    template_name = 'oms_burial_stats.html'

    def get_context_data(self, **kwargs):
        form = self.get_form()
        q = Q()
        if form.data and form.is_valid():
            if form.cleaned_data['date_from']:
                q &= Q(dt_modified__gte=form.cleaned_data['date_from'])
            if form.cleaned_data['date_to']:
                q &= Q(dt_modified__lt=form.cleaned_data['date_to']+datetime.timedelta(days=1))
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
        total['ughs'] = 0
        for o in Org.objects.filter(type=Org.PROFILE_UGH).order_by(*s):
            total['ughs'] += 1 
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

oms_burial_stats = OmsBurialStatsView.as_view()

class LoruOrderStatsView(SupervisorProductionRequiredMixin, PaginateListView):
    template_name = 'loru_order_stats.html'
    queryset = Org.objects.none()

    def get_context_data(self, **kwargs):

        def sort_key(org):
            sort_parm = re.sub(r'^\-', '', sort)
            try:
                result = org[sort_parm]
            except KeyError:
                result = org['name']
            return result

        data = super(LoruOrderStatsView, self).get_context_data(**kwargs)
        form = self.get_form()
        orgs = []
        sort = self.request.GET.get('sort', 'name')
        total={}
        total['loru_count'] = total['num_orders']= total['sum_orders'] = 0

        if form.data and form.is_valid():
            q_opt_order = Q(type=Order.TYPE_TRADE, annulated = False)
            q_order = Q(loru__isnull=False, annulated = False)
            if form.cleaned_data.get('date_from'):
                q_order &= Q(dt__gte=form.cleaned_data['date_from'])
                q_opt_order &= Q(dt_created__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                q_order &= Q(dt__lt=form.cleaned_data['date_to']+datetime.timedelta(days=1))
                q_opt_order &= Q(dt_created__lt=form.cleaned_data['date_to']+datetime.timedelta(days=1))
            supplier_name = form.cleaned_data.get('supplier')
            if supplier_name:
                q_order &= Q(loru__name__icontains=supplier_name)
                q_opt_order &= Q(loru__name__icontains=supplier_name)

            pks = {}
            currencies = set()
            for opt_order in Order.objects.filter(q_opt_order). \
                            select_related('loru', 'loru__name', 'loru__currency'):
                org_pk = opt_order.loru.pk
                if org_pk not in pks:
                    pks[org_pk] = dict(
                        name=opt_order.loru.name,
                        currency=opt_order.loru.currency.code,
                        num_orders=0,
                        sum_orders=0,
                    )
                    if len(currencies) < 2:
                        currencies.add(opt_order.loru.currency)
                org = pks[org_pk]
                org['num_orders'] += 1
                total['num_orders'] += 1
                
                this_sum= opt_order.total
                org['sum_orders'] += this_sum
                total['sum_orders'] +=  this_sum

            for order in Order.objects.filter(q_order). \
                            select_related('loru', 'loru__name', 'loru__currency'):
                org_pk = order.loru.pk
                if org_pk not in pks:
                    pks[org_pk] = dict(
                        name=order.loru.name,
                        currency=order.loru.currency.code,
                        num_orders=0,
                        sum_orders=0,
                    )
                    if len(currencies) < 2:
                        currencies.add(order.loru.currency)
                org = pks[org_pk]
                org['num_orders'] += 1
                total['num_orders'] += 1

                this_sum = order.total
                org['sum_orders'] += this_sum
                total['sum_orders'] +=  this_sum

            orgs = pks.values()

            all_sum_integers = True
            for org in orgs:
                f_sum = float(org['sum_orders'])
                if f_sum - f_sum // 1 != 0.0:
                    all_sum_integers = False
                    break
            if all_sum_integers:
                for org in orgs:
                    org['sum_orders'] = int(org['sum_orders'])
                total['sum_orders'] = int(total['sum_orders'])

            for org in orgs:
                org['sum_orders'] = number_format(org['sum_orders'], force_grouping=True)
            total['sum_orders'] = number_format(total['sum_orders'], force_grouping=True)

            total['currency'] = orgs[0]['currency'] if len(currencies) == 1 else ''
            orgs.sort(key=sort_key, reverse=sort.startswith('-'))

        total['loru_count'] = len(orgs)
        data.update({
            'orgs': orgs,
            'total': total,
            'sort': sort,
            'paginator': Paginator(orgs, per_page=25)
        })
        return data


    def get_form(self):
        return LoruOrdersStatsForm(data=self.request.GET or None)

loru_order_stats = LoruOrderStatsView.as_view()

class OmsCurrentStatsView(SupervisorProductionRequiredMixin, TemplateView):
    template_name = 'oms_current_stats.html'

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
        total['burials_count'] = total['places_cabinet_count'] = \
        total['places_invent_accessible'] = total['places_invent_remake_photo'] = \
        total['places_unidentified'] = total['places_free'] = 0
        q_published = Q(is_public_catalog=True)
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
                status=Burial.STATUS_CLOSED,
                annulated=False,
            ).count()
            total['burials_count'] += org['num_burials']

            org['places_invent_accessible'] = Place.unprocessed_count(org=o)
            total['places_invent_accessible'] += org['places_invent_accessible']

            org['places_invent_remake_photo'] = Place.objects.filter(
                cemetery__ugh=o,
                is_invent=True,
                placephoto__isnull=False,
                dt_wrong_fio__isnull=False,
            ).distinct().count()
            total['places_invent_remake_photo'] += org['places_invent_remake_photo']

            org['places_free'] = Place.objects.filter(
                cemetery__ugh=o,
                dt_free__isnull=False,
            ).distinct().count()
            total['places_free'] += org['places_free']

            org['places_unidentified'] = Place.objects.filter(
                cemetery__ugh=o,
                dt_unindentified__isnull=False,
            ).distinct().count()
            total['places_unidentified'] += org['places_unidentified']

            cabinets = Place.objects.filter(
                cemetery__ugh=o,
                responsible__login_phone__isnull=False,
            )
            org['num_places_cabinet'] = cabinets.count()
            total['places_cabinet_count'] += org['num_places_cabinet']

            ## вместо:
            ## User.objects.filter(username__in=\
            ##    cabinets.distinct('responsible__login_phone').
            ##    order_by('responsible__login_phone').
            ##    values_list('responsible__login_phone')
            ## ).count()
            ## применяем этот сырой запрос из-за cast(string to decimal)
            ##
            #query = r"""SELECT COUNT(*) FROM "auth_user"
                        #WHERE "auth_user"."username" ~ E'^\\d+$'
                        #and cast("auth_user"."username" as decimal) IN 
                        #(SELECT DISTINCT ON (U1."login_phone") U1."login_phone" FROM 
                        #"burials_place" U0 LEFT OUTER JOIN "persons_aliveperson" U1 
                        #ON (U0."responsible_id" = U1."baseperson_ptr_id") 
                        #INNER JOIN "burials_cemetery" U2 ON (U0."cemetery_id" = U2."id")
                        #WHERE (U1."login_phone" IS NOT NULL AND U2."ugh_id" = %s ))
                     #""" % o.pk
            #cursor = connection.cursor()
            #cursor.execute(query)
            #org['num_cabinets'] = cursor.fetchone()[0]

            org['num_cabinets'] = CustomerProfile.objects.filter(login_phone__in=\
                cabinets.distinct('responsible__login_phone').
                order_by('responsible__login_phone').
                values_list('responsible__login_phone')
            ).count()
            
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

oms_current_stats = OmsCurrentStatsView.as_view()

class LoruCurrentStatsView(SupervisorProductionRequiredMixin, TemplateView):
    template_name = 'loru_current_stats.html'

    def get_context_data(self, **kwargs):
        
        sort = self.request.GET.get('sort', 'name')
        
        def sort_key(org):
            sort_parm = re.sub(r'^\-', '', sort)
            try:
                result = org[sort_parm]
            except KeyError:
                result = org['name']
            return result

        orgs = []
        total={}
        total['loru_count'] = total['num_users'] = total['num_active_users'] = \
        total['num_stores'] = \
        total['num_products'] = total['num_published_products'] = \
        total['num_published_wholesales'] = \
        total['num_orders'] = \
        total['num_opt_orders_in'] = total['num_opt_orders_out'] = \
        total['num_burials'] = 0
        catalog_org_pk = Org.get_catalog_org_pk()
        q_published = Q(is_public_catalog=True)
        q_wholesales = Q(is_wholesale=True)

        for o in Org.objects.filter(type=Org.PROFILE_LORU):
            total['loru_count'] += 1
            org = {'name': o.name}
            org['off_address'] = o.off_address or ''
            org['phones'] = phones_from_text(o.phones)
            org['pk'] = o.pk

            org['num_users'] = Profile.objects.filter(org=o).count()
            total['num_users'] += org['num_users']

            org['num_active_users'] = Profile.objects.filter(org=o, user__is_active=True).count()
            total['num_active_users'] += org['num_active_users']

            org['num_stores'] = Store.objects.filter(loru=o).count()
            total['num_stores'] += org['num_stores']

            org['num_products'] = Product.objects.filter(loru=o).count()
            total['num_products'] += org['num_products']

            qs = q_published & Q(loru=o)
            org['num_published_products'] = Product.objects.filter(qs).count()
            total['num_published_products'] += org['num_published_products']

            qs = q_wholesales & Q(loru=o)

            org['num_published_wholesales'] = Product.objects.filter(qs).count()
            total['num_published_wholesales'] += org['num_published_wholesales']

            org['num_orders'] = Order.objects.filter(loru=o).count()
            total['num_orders'] += org['num_orders']

            org['currency'] = o.currency.code

            org['num_opt_orders_in'] = Order.objects.filter(loru=o, type=Order.TYPE_TRADE).count()
            total['num_opt_orders_in'] += org['num_opt_orders_in']
            org['sum_opt_orders_in'] = Order.objects.filter(loru=o, type=Order.TYPE_TRADE). \
                aggregate(total=Sum('cost'))['total'] or 0

            org['num_opt_orders_out'] = Order.objects.filter(applicant_organization=o, type=Order.TYPE_TRADE).count()
            total['num_opt_orders_out'] += org['num_opt_orders_out']
            org['sum_opt_orders_out'] = Order.objects.filter(applicant_organization=o, type=Order.TYPE_TRADE). \
                aggregate(total=Sum('cost'))['total'] or 0

            org['num_burials'] = Burial.objects.filter(
                source_type=Burial.SOURCE_FULL,
                status=Burial.STATUS_CLOSED,
                annulated=False,
                loru=o,
            ).count()
            total['num_burials'] += org['num_burials']

            orgs.append(org)

        orgs.sort(key=sort_key, reverse=sort.startswith('-'))

        return {
            'orgs':orgs,
            'total': total,
            'sort': sort,
        }

loru_current_stats = LoruCurrentStatsView.as_view()

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

class TestCaptcha2View(FormView):
    """
    Форма тестирования captcha 2
    """
    form_class = TestCaptcha2Form
    template_name = 'testcaptcha.html'

    def get_success_url(self):
        return reverse('testcaptcha2')

testcaptcha2 = TestCaptcha2View.as_view()

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

class FavoriteSupplierList(APIView):
    """
    List all loru's favorite suppliers
    """
    permission_classes = (PermitIfTrade,)

    def get(self, request):
        my_org = request.user.profile.org
        data_self = [OrgShort3Serializer(my_org).data]
        data_other = [OrgShort3Serializer(f.supplier).data for f in FavoriteSupplier.objects.filter(
                Q(loru=my_org) & ~Q(supplier=my_org),
        )]
        return Response(data=data_self + data_other, status=200)

api_loru_favorite_suppliers = FavoriteSupplierList.as_view()

class FavoriteSupplierEdit(APIView):
    """
    Add or delete loru's favorite suppliers
    """
    permission_classes = (PermitIfTrade,)

    def post(self, request, supplier_id):
        try:
            try:
                supplier = Org.objects.get(pk=supplier_id)
            except Org.DoesNotExist:
                raise ServiceException(_(u'Нет такого поставщика: %s') % supplier_id)
            if supplier.type != Org.PROFILE_LORU:
                raise ServiceException(_(u'Id = %s : это не поставщик (ЛОРУ)') % supplier_id)
            FavoriteSupplier.objects.get_or_create(
                loru=request.user.profile.org,
                supplier=supplier,
            )
        except ServiceException as excpt:
            data = dict(status='error', message=excpt.message)
            status_code = 400
        else:
            data = dict()
            status_code = 200
        return Response(data, status=status_code)

    def delete(self, request, supplier_id):
        FavoriteSupplier.objects.filter(
            loru=request.user.profile.org,
            supplier__pk=supplier_id,
        ).delete()
        return Response(data={}, status=200)

api_loru_favorite_suppliers_edit = FavoriteSupplierEdit.as_view()

class StoreList(APIView):
    """
    List all stores, or create a new store.
    """
    permission_classes = (PermitIfLoruOrUgh,)

    def get(self, request, format=None):
        stores = Store.objects.filter(loru=request.user.profile.org)
        serializer = StoreSerializer(stores, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        if is_ugh_user(request.user) and not request.user.profile.is_admin():
            raise PermissionDenied
        serializer = StoreSerializer(data=request.DATA, context={ 'request': request, })
        if serializer.is_valid():
            serializer.save()
            phones = request.DATA.get('phones')
            if phones is not None:
                Phone.create_default_phones(serializer.object, phones)
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)
    
api_loru_stores = StoreList.as_view()

class StoreDetail(APIView):
    """
    Retrieve, update or delete a store instance.
    """
    permission_classes = (PermitIfLoruOrUgh,)

    def get_object(self, request, pk):
        try:
            return Store.objects.get(loru=request.user.profile.org, pk=pk)
        except Store.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        store = self.get_object(request, pk)
        serializer = StoreSerializer(store)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        store = self.get_object(request, pk)
        if is_ugh_user(request.user) and not request.user.profile.is_admin():
            return PermissionDenied
        serializer = StoreSerializer(store, data=request.DATA, context={ 'request': request, })
        if serializer.is_valid():
            serializer.save()
            phones = request.DATA.get('phones')
            if phones is not None:
                Phone.create_default_phones(serializer.object, phones)
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk, format=None):
        store = self.get_object(request, pk)
        if is_ugh_user(request.user) and not request.user.profile.is_admin():
            return PermissionDenied
        store.delete()
        return Response(status=200, data={})

api_loru_store_detail = StoreDetail.as_view()

class ApiOrgSignupView(CheckRecaptcha2Mixin, RegisterMixin, APIView):
    """
    Регистрация ЛОРУ (нового поставщика)
    """
    parser_classes = (MultiPartParser,)
    
    @transaction.commit_on_success
    def post(self, request):
        try:
            recaptcha_data = request.DATA.get('captchaData')
            if not recaptcha_data:
                raise ServiceException(_(u'Нет captcha'))
            elif not self.check_recaptcha(self.request, recaptcha_data):
                raise ServiceException(_(u'Введена неверная captcha'))

            username = request.DATA.get('username', '').strip()
            if not username:
                raise ServiceException(_(u'Не задано имя пользователя для входа в систему'))
            try:
                validate_username(username)
            except ValidationError as e:
                raise ServiceException(_(u'Неверное имя пользователя для входа в систему: '
                                         u'%(username)s. %(message)s') % dict(
                    username=username,
                    message=e.messages and e.messages[0] or '',
                ))
            if User.objects.filter(username__iexact=username).exists():
                raise ServiceException(_(u"Имя  %s уже используется в системе") % username)
            q = Q(user_name__iexact=username) & \
                ~Q(status__in=(RegisterProfile.STATUS_DECLINED, RegisterProfile.STATUS_APPROVED, ))
            if RegisterProfile.objects.filter(q).exists():
                raise ServiceException(_(u"Имя  %s уже используется среди кандидатов на регистрацию") % username)

            email = request.DATA.get('email', '').strip()
            if not email:
                raise ServiceException(_(u'Не задан адрес электронной почты'))
            try:
                validate_email(email)
            except ValidationError:
                raise ServiceException(_(u'Неверный формат адреса электронной почты: %s') % email)

            if User.objects.filter(email__iexact=email).exists():
                raise ServiceException(_(u"Email %s уже используется в системе") % email)
            q = Q(user_email__iexact=email) & \
                ~Q(status__in=(RegisterProfile.STATUS_DECLINED, RegisterProfile.STATUS_APPROVED, ))
            if RegisterProfile.objects.filter(q).exists():
                raise ServiceException(_(u"Email %s уже используется среди кандидатов на регистрацию") % email)

            password = request.DATA.get('password', '')
            if not password.strip():
                raise ServiceException(_(u'Не задан пароль'))
            user_password = make_password(password)
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            user_activation_key = hashlib.sha1(salt+username).hexdigest()

            location = request.DATA.get('registredOffice')
            if not location:
                raise ServiceException(_(u'Не задан адрес организации'))
            try:
                location = json.loads(location)
            except ValueError:
                raise ServiceException(_(u'Неверный формат registredOffice'))
            coords = location.get('location')
            gps_x= coords and coords.get('longitude')
            gps_y= coords and coords.get('latitude')
            country, country_currency = Country.get_country_currency_by_coords(gps_y, gps_x)
            org_address = Location(
                addr_str=location.get('address', '').strip(),
                country=country,
                gps_x=gps_x,
                gps_y=gps_y,
            )
            currency_code = request.DATA.get('currency')
            if currency_code:
                try:
                    org_currency = Currency.objects.get(code=country_code)
                except Currency.DoesNotExist:
                    raise ServiceException(_(u'Неизвестный код валюты'))
            else:
                org_currency = country_currency or get_default_currency()

            user_last_name = request.DATA.get('userLastName', '').strip()
            if not user_last_name:
                raise ServiceException(_(u'Не задана фамилия пользователя'))
            user_first_name = request.DATA.get('userFirstName', '').strip()
            if not user_first_name:
                raise ServiceException(_(u'Не задано имя пользователя'))
            user_middle_name = request.DATA.get('userMiddleName', '').strip()

            org_name = request.DATA.get('orgName', '').strip()
            if not org_name:
                raise ServiceException(_(u'Не задано краткое наименование организации'))
            if re.search(r'^[\d\s]+$', org_name):
                raise ServiceException(_(u'Невозможное название организации (только из цифр)'))
            org_subdomain = request.DATA.get('subdomainName', '').lower().strip() or None
            if org_subdomain:
                if not re.search(r'^[\w-]+$', org_subdomain):
                    raise ServiceException(_(u'В поддомене допустимы лишь латинские буквы, цифры, _, -'))
                if Org.objects.filter(subdomain__iexact=org_subdomain).exists():
                    raise ServiceException(_(u'Есть уже организация с таким поддоменом'))
                q = Q(org_subdomain__iexact=org_subdomain) & \
                    ~Q(status__in=(RegisterProfile.STATUS_DECLINED, RegisterProfile.STATUS_APPROVED, ))
                if RegisterProfile.objects.filter(q).exists():
                    raise ServiceException(_(u'Есть уже кандидат на регистрацию с таким поддоменом'))
            org_types = dict(loru=Org.PROFILE_LORU, oms=Org.PROFILE_UGH)
            org_type = request.DATA.get('orgType')
            if not org_type or org_type not in org_types:
                raise ServiceException(_(u'Тип организации не задан или неверен'))
            org_type = org_types[org_type]
            org_phones = request.DATA.get('phones')
            fax_len = RegisterProfile._meta.get_field('org_fax').max_length
            org_fax=request.DATA.get('fax', '').strip()
            if len(org_fax) > fax_len:
                raise ServiceException(_(u'Факс: длина больше %d символов') % fax_len)
            if org_phones:
                try:
                    org_phones = "\n".join(json.loads(org_phones))
                except ValueError:
                    raise ServiceException(_(u'Неверный формат телефонов (phones)'))
            if not org_phones:
                raise ServiceException(_(u'Не указано ни одного телефона'))
            org_inn=request.DATA.get('tin', '').strip()
            org_basis = request.DATA.get('directorPowerSource', Org.BASIS_CHARTER)
            org_address.save()
            registerprofile = RegisterProfile.objects.create(
                status=RegisterProfile.STATUS_TO_CONFIRM,
                user_name=username,
                user_last_name=user_last_name,
                user_first_name=user_first_name,
                user_middle_name=user_middle_name,
                user_email=email,
                user_password=user_password,
                user_activation_key=user_activation_key,
                org_type=org_type,
                org_name=org_name,
                org_subdomain=org_subdomain,
                org_full_name=request.DATA.get('orgFullName', '').strip() or org_name,
                org_currency=org_currency,
                org_inn=org_inn,
                org_ogrn=request.DATA.get('OGRN', '').strip(),
                org_director=request.DATA.get('directorFullname', '').strip(),
                org_phones=org_phones,
                org_fax=org_fax,
                org_address=org_address,
                org_basis=org_basis,
            )

            banks = request.DATA.get('bankAccounts')
            if banks:
                name_len = BankAccountRegister._meta.get_field('bankname').max_length
                rs_len = BankAccountRegister._meta.get_field('rs').max_length
                bik_len = BankAccountRegister._meta.get_field('bik').max_length
                ks_len = BankAccountRegister._meta.get_field('ks').max_length
                try:
                    banks = json.loads(banks)
                except ValueError:
                    raise ServiceException(_(u'Неверный формат банковских счетов (bankAccounts)'))
                for bank in banks:
                    # Возможно: вх. bankAccounts=[{}]
                    # Возможно: [{"name":"","account":"","bik":"","correspondent":""}]
                    #
                    if not bank.get('name') or not bank.get('account'):
                        continue

                    bank['name'] = bank['name'].strip()
                    if not bank['name']:
                        raise ServiceException(_(u'Пустое наименование банка') )
                    if len(bank['name']) > name_len:
                        raise ServiceException(
                            _(u'Наименование банка, %(name)s, '
                              u'превышает максимальную длину, %d(name_len)') % dict(
                            name=bank['name'],
                            name_len=name_len,
                        ))

                    bank['account'] = bank['account'].strip()
                    if not re.search(r'^\d{6,%d}$' % rs_len, bank['account']):
                        raise ServiceException(_(u'Неверный банковский расчетный счет: %s') % bank['account'])

                    bank['bik'] = bank['bik'].strip()
                    if bank['bik'] and not re.search(r'^\d{3,%d}$' % bik_len, bank['bik']):
                        raise ServiceException(_(u'Неверный БИК: %s') % bank['bik'])

                    bank['correspondent'] = bank['correspondent'].strip()
                    if bank['correspondent'] and not re.search(r'^\d{6,%d}$' % ks_len, bank['correspondent']):
                        raise ServiceException(_(u'Неверный банковский корреспондентский счет: %s') % bank['correspondent'])

                    bank_address = bank.get('address') and bank['address'].strip() or ''
                    if bank_address:
                        bank_address = Location.objects.create(addr_str=bank_address)
                    else:
                        bank_address = None
                    BankAccountRegister.objects.create(
                        registerprofile=registerprofile,
                        bankname=bank['name'],
                        rs=bank['account'],
                        bik=bank['bik'],
                        ks=bank['correspondent'],
                        off_address=bank_address,
                    )

            cert = request.FILES.get('certificatePhoto')
            if cert:
                RegisterProfileScan.objects.create(
                    bfile=cert,
                    registerprofile=registerprofile,
                )

            # Будем использовать один и тот же шаблон и для договора с кандидатом на регистрацию,
            # и для договора с организацией, а там разные имена полей. "Приведем" эти имена
            # к тому, что есть в модели Org
            #
            for f in registerprofile._meta.get_all_field_names():
                if f.startswith('org_'):
                    setattr(registerprofile, f[4:], getattr(registerprofile, f))
            setattr(registerprofile, 'off_address', getattr(registerprofile, 'org_address'))

            try:
                pdf = PDFTemplateResponse(
                    request=request,
                    template='loru_contract.html' if registerprofile.org_type==Org.PROFILE_LORU \
                              else 'oms_contract.html',
                    context=dict(org=registerprofile)
                ).rendered_content
            except:
                raise ServiceException(_(u'Ошибка формирования договора.pdf. Проверьте настройки сервера'))
            
            #contract = RegisterProfileContract.objects.create(
                #registerprofile=registerprofile,
            #)
            #contract.bfile.save('contract.pdf', ContentFile(pdf))
            self.send_email_to_confirm(obj=registerprofile)
            return Response(status=200, data={
                'status': 'success',
                'message': _(
                    u"Вам отправлено письмо по адресу %s, "
                    u"в котором имеется ссылка, "
                    u"переход по которой направит вашу заявку "
                    u"на рассмотрение администратора системы"
                ) % registerprofile.user_email
            })

        except ServiceException as excpt:
            transaction.rollback()
            return Response(dict(status='error', message=excpt.message), status=400)

api_org_signup = ApiOrgSignupView.as_view()

class ApiCatalogSuppliersView(APIView):

    def get(self, request):
        return Response(
            data = [ OrgShort2Serializer(
                                    loru,
                                    context = dict(request=request),
                     ).data for loru in Org.objects.filter(ability__name=OrgAbility.ABILITY_TRADE) ],
            status=200
        )

api_catalog_suppliers = ApiCatalogSuppliersView.as_view()

class OrgDetailView(APIView):
    def get(self, request, org_slug):
        """
        Запрос данных организации по slug, или по id, если org_slug состоит только из цифр
        """
        if re.search(r'^\d+$', org_slug):
            kwargs = dict(pk=org_slug)
        else:
            kwargs = dict(slug=org_slug)
        obj = get_object_or_404(Org, **kwargs)
        return Response(status=200, data=OrgSerializer(obj, context = dict(request=request)).data)

api_catalog_suppliers_detail = OrgDetailView.as_view()

class ApiOptplacesSuppliersView(APIView):
    permission_classes = (PermitIfTradeOrSupervisor, )
    def get(self, request):
        return Response(
            data = [ OrgOptSupplierSerializer(loru).data for \
                        loru in Org.objects.filter(ability__name=OrgAbility.ABILITY_TRADE) ],
            status=200
        )

api_optplaces_suppliers = ApiOptplacesSuppliersView.as_view()

class ApiOptplacesSupplierDetailView(APIView):
    """
    Показ данных о ЛОРУ, поставщике интернет-заказа
    
    Общий доступ, чтобы можно было посмотреть price-list поставщика
    """
    def get(self, request, pk):
        obj = get_object_or_404(Org, pk=pk)
        return Response(status=200, data=OrgShort5Serializer(obj, context=dict(request=request)).data)

api_optplaces_suppliers_detail = ApiOptplacesSupplierDetailView.as_view()

class ApiShopsView(APIView):

    def get(self, request):
        q = Q(orgservice__service__name=Service.SERVICE_DELIVERY) & \
            Q(orgservice__enabled=True) & \
            Q(orgservice__orgserviceprice__measure__name='km')

        category_ids_got = self.request.GET.getlist('categories')
        category_ids = []
        for category_id in category_ids_got:
            try:
                # может быть '', 'null'
                category_ids.append(int(category_id))
            except ValueError:
                pass
        if category_ids:
            q &= Q(product__productcategory__pk__in=category_ids)
        else:
            q &= Q(product__productcategory__pk__in=ProductCategory.AVAILABLE_FOR_VISIT_PKS)

        s = request.GET.get('query')
        if s:
            q2 = Q(off_address__city__name__icontains=s) | \
                 Q(off_address__addr_str__icontains=s) | \
                 Q(product__name__icontains=s)
            q &=q2

        return Response(
            data = [ ShopSerializer(shop, context=dict(request=request)).data for \
                        shop in Org.objects.filter(q).distinct() ],
            status=200
        )

api_shops = ApiShopsView.as_view()

class ApiShopsMixin(object):

    def get_shop(self, pk, authorized_only=False, check_subdomain=False):
        """
        Получить магазин (поставщик) по pk

        Если authorized_only==True, то проверка, авторизован ли пользователь,
        чтоб менять данные по этому поставщику
        Если check_subdomain == True, то посмотреть, есть ли get параметр findBySubdomain,
        и если он есть, то pk это не цифровой идентификатор, а поддомен
        """
        seek_kwargs = dict(pk=pk)
        if check_subdomain:
            if 'findBySubdomain' in self.request.GET:
                seek_kwargs = dict(subdomain=pk)
            else:
                if not re.search(r'^\d+$', pk):
                    # Поиск по id. Только цифры
                    raise Http404
        try:
            shop = Org.objects.get(**seek_kwargs)
            if authorized_only:
                try:
                    if self.request.user.profile.org != shop:
                        raise Http404
                except (Profile.DoesNotExist, AttributeError):
                    raise Http404
            return shop
        except Org.DoesNotExist:
            raise Http404

class ApiShopsGalleryView(ApiShopsMixin, APIView):
    parser_classes = (MultiPartParser,)
    
    def get(self, request, pk):
        shop = self.get_shop(pk, authorized_only=False)
        return Response(
            data = [
                OrgGallerySerializer(item, context=dict(request=request)).data \
                    for item in OrgGallery.objects.filter(org=shop).order_by('-date_of_creation')
            ],
            status=200
        )

    def post(self, request, pk):
        try:
            shop = self.get_shop(pk, authorized_only=True)
            photo = request.FILES.get('photo')
            if photo:
                if photo.size > OrgGallery.MAX_IMAGE_SIZE * 1024 * 1024:
                    raise ServiceException(_(u"Размер фото превышает %d Мб") % OrgGallery.MAX_IMAGE_SIZE)
                if not get_image(photo):
                    raise ServiceException(_(u"Загруженное фото не является изображением"))
            else:
                raise ServiceException(_(u"Нет загружаемого фото (photo)"))
            item = OrgGallery.objects.create(
                org=shop,
                bfile=photo,
                creator=request.user,
                comment=request.DATA.get('title'),
            )
            return Response(
                data = OrgGallerySerializer(item, context=dict(request=request)).data,
                status=200
            )
        except ServiceException as excpt:
            return Response(data=dict(status='error', message=excpt.message), status=400)

api_shops_gallery = ApiShopsGalleryView.as_view()

class ApiShopsDetailView(ApiShopsMixin, APIView):

    def get(self, request, pk):
        shop = self.get_shop(pk, authorized_only=False, check_subdomain=True)
        return Response(
            data = ShopDetailSerializer(shop, context=dict(request=request)).data,
            status=200
        )

api_shops_detail = ApiShopsDetailView.as_view()

class ApiShopsReviewsView(ApiShopsMixin, APIView):

    def get(self, request, pk):
        shop = self.get_shop(pk, authorized_only=False)
        return Response(
            data = [ OrgReviewSerializer(review).data \
                     for review in OrgReview.objects.filter(org=shop).order_by('-dt_created')],
            status=200
        )

    def post(self, request, pk):
        try:
            shop = self.get_shop(pk, authorized_only=False)
            if not is_cabinet_user(request.user):
                raise PermissionDenied
            mapping = dict(
                title='subject',
                commonText='common_text',
                positiveText='positive_text',
                negativeText='negative_text',
            )
            kwargs = dict()
            for key in mapping:
                if request.DATA.get(key) is not None:
                    kwargs[mapping[key]] = request.DATA[key]
            if 'isPositive' in request.DATA:
                kwargs['is_positive'] = request.DATA['isPositive']
            # Не должно быть пустого отзыва. Хотя бы только оценка
            if kwargs.get('is_positive') not in (True, False):
                for key in mapping:
                    if kwargs.get(mapping[key]):
                        break
                else:
                    raise ServiceException(_(u"Пустой отзыв недопустим"))
            kwargs.update(dict(
                org=shop,
                creator=request.user,
            ))
            review = OrgReview.objects.create(**kwargs)
            return Response(
                data = OrgReviewSerializer(review).data,
                status=200
            )
        except ServiceException as excpt:
            return Response(data=dict(status='error', message=excpt.message), status=400)

api_shops_reviews = ApiShopsReviewsView.as_view()

class ApiClientSiteMixin(object):

    def get_org(self, token):
        return get_object_or_404(Org, client_site_token=token)

class ApiClientSiteDetailView(ApiClientSiteMixin, APIView):

    def get(self, request, token):
        org = self.get_org(token)
        return Response(status=200, data=OrgClientSiteSerializer(org).data)

api_client_site_detail = ApiClientSiteDetailView.as_view()

class ApiClientEmployeesView(ApiClientSiteMixin, APIView):

    def get(self, request, token):
        org = self.get_org(token)
        qs = Q(org=org, user__is_active=True, out_of_staff=False)

        store_id = request.GET.get('departmentId')
        if store_id:
            qs &= Q(store__pk=store_id)

        cemetery_id = request.GET.get('cemeteryId')
        if cemetery_id:
            qs &= Q(cemeteries__pk=cemetery_id, role__name=Role.ROLE_REGISTRATOR)

        return Response(
            status=200,
            data=ProfileClientSiteSerializer(
                Profile.objects.filter(qs),
                context=dict(request=request),
                many=True,
            ).data
        )

api_client_site_employees = ApiClientEmployeesView.as_view()

class ApiClientDepartmentsView(ApiClientSiteMixin, APIView):

    def get(self, request, token):
        org = self.get_org(token)
        return Response(
            status=200,
            data=Store2Serializer(
                Store.objects.filter(loru=org),
                context=dict(request=request),
                many=True,
            ).data
        )

api_client_site_departments = ApiClientDepartmentsView.as_view()

class ApiClientSiteMessagesView(ApiClientSiteMixin, APIView):
    """
    Послать сообщение клиенту (на email организации) в форме обратной связи

    Пример входных данных:
    {
        "fullName": "Иванов И.И",
        "phoneNumber": "+375291234567",
        "email": "email@email.ru",
        "subject": "Тема",
        "text": "Текст вопроса",
    }

    Status codes:
        200 - если все нормально
        400 - если произошла ошибка валидации входных данных

    """
    def post(self, request, token):
        org = self.get_org(token)
        try:
            email_to = org.email and org.email.strip()
            try:
                validate_email(email_to)
            except ValidationError:
                raise ServiceException(_(u"Неверный или не задан адрес электронной почты организации"))

            email_reply_to = request.DATA.get('email', '').strip()
            try:
                validate_email(email_reply_to)
            except ValidationError:
                raise ServiceException(_(u"Неверный или не задан адрес электронной почты отправителя"))

            subject = request.DATA.get('subject', '').strip()
            email_subject = subject if subject else _(u'Сообщение на сайт')

            email_text = request.DATA.get('text', '').strip()
            if not email_text:
                raise ServiceException(_(u"Нет текста сообщения"))

            full_name = request.DATA.get('fullName', '').strip()
            phone = request.DATA.get('phoneNumber', '').strip()
            email_text += u"\n\n----------"
            if full_name:
                email_text += u"\n%s" % full_name
            if phone:
                email_text += _(u"\nТелефон: %s") % phone
            email_text += _(u"\nEmail: %s") % email_reply_to

            headers = { 'Reply-To': email_reply_to }
            # Если в From: поставить задавшего вопрос, например, user@yandex.ru,
            # то письмо придет в email_to (адреса гугловской почты) с "замечаниями"
            # в заголовке, что письмо пришло не от yandex, так и в спам может попасть.
            # Посему реальный отправитель будет в Reply-To:
            #
            email_from = _(u"Сообщение на сайт <%s>") % settings.DEFAULT_FROM_EMAIL
            EmailMessage(email_subject, email_text, email_from, (email_to,), headers=headers, ).send()
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

api_client_site_messages = ApiClientSiteMessagesView.as_view()

class ApiVideoMixin(object):

    def get_or_add_video(self, yid):
        youtubevideo, created = None, None
        try:
            youtube = Youtube(yid)
            yid = youtube.get_id()
        except Youtube.ExcptId:
            return youtubevideo, created
        youtubevideo, created = YoutubeVideo.objects.get_or_create(
            yid=yid,
        )
        if created:
            try:
                parms = youtube.get_parms()
                youtubevideo.url = parms['url']
                youtubevideo.title = parms['title']
                youtubevideo.title_photo_url = parms['title_photo_url']
                youtubevideo.save()
            except Youtube.Excpt:
                pass
            try:
                captions = youtube.get_captions()
                for num, caption in enumerate(captions):
                    YoutubeCaption.objects.create(
                        youtubevideo=youtubevideo,
                        num=num,
                        start=caption['start'],
                        stop=caption['stop'],
                        text=caption['text'],
                    )
            except Youtube.Excpt:
                pass
        return youtubevideo, created

class ApiVideoVotesView(ApiVideoMixin, APIView):

    def get(self, request, yid):
        youtubevideo = get_object_or_404(YoutubeVideo, yid=yid)
        offset = request.GET.get('offset') and int(request.GET['offset'])
        count = int(request.GET.get('count', '20'))

        #votes = YoutubeVote.objects.filter(youtubevideo=youtubevideo).\
                    #order_by('-dt_created')
        #if offset and count:
            #votes = votes[offset:offset+count]
        #elif offset:
            #votes = votes[offset:]
        #elif count:
            #votes = votes[:count]
        #serializer = YoutubeVoteSerializer(votes, many=True)
        # data = serializer.data

        # Надо не показывать несколько голосов от одного пользователя в секунду

        req_str = '''
            SELECT
                '%(yid)s' AS id,
                "datetime",
                "timestamp",
                "type"
            FROM
                (
                    SELECT DISTINCT ON (time, user_id)
                        "dt_created",
                        to_char(dt_created AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') as "datetime",
                        "time" as "timestamp",
                        "like" as "type",
                        "user_id"
                    FROM users_youtubevote 
                    WHERE youtubevideo_id = %(youtubevideo_id)s
                    ORDER BY "time", "user_id"
                )
            AS foo
            ORDER BY "datetime" DESC
            %(limit_str)s %(offset_str)s;
        ''' % dict(
                yid=yid,
                youtubevideo_id=youtubevideo.pk,
                offset_str='OFFSET %s' % offset if offset else '',
                limit_str='LIMIT %s' % count if count else '',
        )
        cursor = connection.cursor()
        cursor.execute(req_str)
        data = dictfetchall(cursor)
        return Response(data=data)

    def post(self, request, yid):
        if not request.user.is_authenticated():
            raise PermissionDenied
        youtubevideo, created = self.get_or_add_video(yid)
        if not youtubevideo:
            return Response(
                data=dict(message=_(u"Ошибка идентификатора Youtube видео")),
                status=400,
            )
        type_ = (request.DATA.get('type') or YoutubeVote.LIKE_UP).lower()
        if type_ not in (YoutubeVote.LIKE_UP, YoutubeVote.LIKE_DOWN,):
            type_ = YoutubeVote.LIKE_UP
        timestamp = max(request.DATA.get('timestamp') or 0, 0)
        vote = YoutubeVote.objects.create(
            youtubevideo=youtubevideo,
            user=request.user,
            time=timestamp,
            like=type_,
        )
        serializer = YoutubeVoteSerializer(vote)
        return Response(serializer.data, status=200)

api_video_votes = ApiVideoVotesView.as_view()

class ApiVideoTimestampsVotes(ApiVideoMixin, APIView):

    def get(self, request, yid, second):
        """
        Список проголосовавших
        """
        youtubevideo = get_object_or_404(YoutubeVideo, yid=yid)
        time = second and int(second) or 0
        q = Q(youtubevideo=youtubevideo, time=time)
        like = request.GET.get('type')
        if like:
            q &= Q(like=like)
        return Response(data=[ SocialUserSerializer(vote.user).data \
            for vote in YoutubeVote.objects.filter(q).distinct('user')
        ])

api_video_timestamps_votes = ApiVideoTimestampsVotes.as_view()

class ApiVideoAggregatedVotesView(APIView):

    def get(self, request, yid):
        req_str = '''
            SELECT
                "time" as "timestamp",
                "like" as "type",
                Count(*) as "total"
            FROM
                (
                    SELECT
                        "time",
                        "like",
                        "user_id"
                    FROM "users_youtubevote"
                    INNER JOIN "users_youtubevideo" ON 
                        ("users_youtubevote"."youtubevideo_id" = "users_youtubevideo"."id")
                    WHERE "users_youtubevideo"."yid" = '%(yid)s'
                    GROUP BY "time", "like", "user_id"
                )
            AS "foo"
            GROUP BY "time", "like"
            ORDER BY "timestamp";
        '''
        cursor = connection.cursor()
        cursor.execute(req_str % dict(yid=yid))
        # -----------------------------------
        data = dictfetchall(cursor)
        # -----------------------------------
        #data = {
            #YoutubeVote.LIKE_UP: [],
            #YoutubeVote.LIKE_DOWN: [],
        #}
        #for row in cursor.fetchall():
            #if row[1] == YoutubeVote.LIKE_UP:
                #data[YoutubeVote.LIKE_UP].append(
                    #dict(
                        #timestamp=row[0],
                        #total=row[2],
                #))
            #elif row[1] == YoutubeVote.LIKE_DOWN:
                #data[YoutubeVote.LIKE_DOWN].append(
                    #dict(
                        #timestamp=row[0],
                        #total=row[2],
                #))
        # -----------------------------------

        # Работало такое, но нельзя показывать несколько голосов
        # от одного пользователя в секунду.
        # data = dict()
        #for like in (YoutubeVote.LIKE_UP, YoutubeVote.LIKE_DOWN,):
            #data[like] = YoutubeVote.objects.\
                            #extra(select={'timestamp': 'time'}). \
                            #values('timestamp'). \
                            #filter(like=like, youtubevideo=youtubevideo).order_by('time').\
                            #annotate(total=Count('time'))

        return Response(data, status=200)

api_video_aggregated_votes = cache_page(60)(ApiVideoAggregatedVotesView.as_view())

class ApiVideosView(ApiVideoMixin, APIView):

    def get(self, request):
        qs = YoutubeVideo.objects.filter(is_hidden=False).order_by('-dt_created')
        data = YoutubeVideoSerializer(qs, many=True).data
        return Response(data, status=200)

    def post(self, request):
        status_code = 200
        try:
            if not request.user.is_authenticated():
                raise PermissionDenied
            yid = request.DATA.get('youtube_url_or_id')
            if not yid:
                raise ServiceException(_(u"Не задан идентификатор или URL Youtube видео"))
            youtubevideo, created = self.get_or_add_video(yid)
            if not youtubevideo:
                raise ServiceException(_(u"Ошибка идентификатора или URL Youtube видео"))
            data = YoutubeVideoSerializer(youtubevideo).data
        except ServiceException as excpt:
            data = dict(message=excpt.message)
            status_code = 400
        return Response(data=data, status=status_code)

api_videos = ApiVideosView.as_view()

class ApiVideoStaitsticsView(APIView):

    def get(self, request, yid):
        youtubevideo = get_object_or_404(YoutubeVideo, yid=yid)
        data = dict(
            total_users=User.objects.filter(is_active=True).count(),
            total_video_users=YoutubeVote.objects.filter(
                                youtubevideo=youtubevideo, like=YoutubeVote.LIKE_UP,
                                ).distinct('user').count(),
            total_votes=YoutubeVote.objects.filter(youtubevideo=youtubevideo).count(),
        )
        return Response(data, status=200)

api_video_statistics = ApiVideoStaitsticsView.as_view()

class ApiVideoCaptionsView(APIView):

    def get(self, request, yid):
        youtubevideo = get_object_or_404(YoutubeVideo, yid=yid)
        qs = YoutubeCaption.objects.filter(youtubevideo=youtubevideo).order_by('num')
        data = YoutubeCaptionSerializer(qs, many=True).data
        return Response(data, status=200)

api_video_subtitles = ApiVideoCaptionsView.as_view()

class ApiVideoCaptionsVotesView(APIView):

    def get(self, request, yid):
        youtubevideo = get_object_or_404(YoutubeVideo, yid=yid)
        qs = YoutubeCaption.objects.filter(youtubevideo=youtubevideo).order_by('num')
        data = YoutubeCaptionVoteSerializer(qs, many=True).data
        return Response(data, status=200)

    def post(self, request, yid):
        if not request.user.is_authenticated():
            raise PermissionDenied
        caption_id = request.DATA.get('subtitle_id')
        if not caption_id:
            raise Http404
        youtubecaption = get_object_or_404(
            YoutubeCaption,
            youtubevideo__yid=yid,
            pk=caption_id
        )
        type_ = (request.DATA.get('type') or YoutubeVote.LIKE_UP).lower()
        if type_ not in (YoutubeVote.LIKE_UP, YoutubeVote.LIKE_DOWN,):
            type_ = YoutubeVote.LIKE_UP
        vote = YoutubeCaptionVote.objects.create(
            youtubecaption=youtubecaption,
            user=request.user,
            like=type_,
        )
        serializer = YoutubeCaptionVoteSerializer(youtubecaption)
        return Response(serializer.data, status=200)

api_video_subtitles_votes = ApiVideoCaptionsVotesView.as_view()

class VideoListView(SupervisorRequiredMixin, PaginateListView):
    template_name = 'video_list.html'
    context_object_name = 'videos'

    def __init__(self, *args, **kwargs):
        super(VideoListView, self).__init__(*args, **kwargs)
        self.SORT_DEFAULT = '-dt'

    def get_form(self):
        return VideoSearchForm(data=self.request.GET or None)

    def get_queryset(self):
        videos = YoutubeVideo.objects.all()
        sort = self.request.GET.get('sort', self.SORT_DEFAULT)
        SORT_FIELDS = {
            'dt': 'dt_created',
            '-dt': '-dt_created',
            'title': 'title',
            '-title': '-title',
        }
        try:
            s = SORT_FIELDS[sort]
        except KeyError:
            s = SORT_FIELDS[self.SORT_DEFAULT]
        if not isinstance(s, list):
            s = [s]
        return videos.order_by(*s)

videos = VideoListView.as_view()

class ApiVideoDetailView(APIView):

    @transaction.commit_on_success
    def get(self, request, yid):
        youtubevideo = get_object_or_404(YoutubeVideo, yid=yid)

        get_parms_supervisor = ('refresh', 'hide', 'show',)
        for p in get_parms_supervisor:
            if request.GET.get(p) and not is_supervisor(request.user):
                raise PermissionDenied

        if request.GET.get('refresh'):
            y = Youtube(yid)
            y_parms = y.get_parms()
            do_save = False
            if y_parms:
                if y_parms['title'] and y_parms['title'] != youtubevideo.title:
                    youtubevideo.title = y_parms['title']
                    do_save = True
                if y_parms['title_photo_url'] and \
                   y_parms['title_photo_url'] != youtubevideo.title_photo_url:
                    youtubevideo.title_photo_url = y_parms['title_photo_url']
                    do_save = True
            if do_save:
                youtubevideo.save()

        elif request.GET.get('hide'):
            youtubevideo.is_hidden = True
            youtubevideo.save()

        elif request.GET.get('show'):
            youtubevideo.is_hidden = False
            youtubevideo.save()

        return Response(data=YoutubeVideoSerializer(youtubevideo).data, status=200)

    @transaction.commit_on_success
    def delete(self, request, yid):
        if not is_supervisor(request.user):
            raise PermissionDenied
        youtubevideo = get_object_or_404(YoutubeVideo, yid=yid)
        youtubevideo.delete()
        return Response(data={}, status=200)

api_video_detail = ApiVideoDetailView.as_view()

class ApiVideoStatisticsCurrentUserView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, yid):

        # 'like' - зарезервированное sql слово, и наверное, поэтому не получается :
        # ...
        # .extra(select={'timestamp': 'time', 'type': 'like'}
        # .values('timestamp', 'type')
        # ...

        columns = ['timestamp', 'type']
        data = [ dict(zip(columns, row)) for row in \
            YoutubeVote.objects.filter(
                youtubevideo__yid=yid,
                user=request.user,
            ) \
            .values_list('time', 'like') \
            .distinct('time', 'like') \
            .order_by('time')
        ]
        return Response(data=data, status=200)

api_video_statistics_current_user = ApiVideoStatisticsCurrentUserView.as_view()

class ThanksListView(SupervisorRequiredMixin, PaginateListView):
    template_name = 'thank_list.html'
    context_object_name = 'thanks'

    def __init__(self, *args, **kwargs):
        super(ThanksListView, self).__init__(*args, **kwargs)
        self.SORT_DEFAULT = 'dt_created'

    def get_form(self):
        return ThanksForm(data=self.request.GET or None)

    def get_queryset(self):
        thanked = self.request.GET.get('thanked')
        if thanked:
            thanks = Thank.objects.filter(
                user__customerprofile__isnull=False,
                customperson__pk=thanked,
            )
        else:
            thanks = Thank.objects.none()
        sort = self.request.GET.get('sort', self.SORT_DEFAULT)
        SORT_FIELDS = {
            'dt_created': 'dt_created',
            '-dt_created': '-dt_created',
            'dt_modified': 'dt_modified',
            '-dt_modified': '-dt_modified',
            'fio': [
                'user__customerprofile__user_last_name',
                'user__customerprofile__user_first_name',
                'user__customerprofile__user_middle_name',
                ],
            '-fio': [
                '-user__customerprofile__user_last_name',
                '-user__customerprofile__user_first_name',
                '-user__customerprofile__user_middle_name',
                ],
        }
        try:
            s = SORT_FIELDS[sort] 
        except KeyError:
            s = SORT_FIELDS[self.SORT_DEFAULT]
        if not isinstance(s, list):
            s = [s]
        return thanks.order_by(*s)

thanks = ThanksListView.as_view()

class ApiThankDetailView(APIView):
    permission_classes = (PermitIfSupervisor,)

    @transaction.commit_on_success
    def delete(self, request, pk):
        thank = get_object_or_404(Thank, pk=pk)
        thank.delete()
        return Response(data={}, status=200)

api_thank_detail = ApiThankDetailView.as_view()

class ApiVkBotHandlerView(APIView):
    """
    Vkontakte CallBackApi

    См. https://habrahabr.ru/post/329150/
    """

    # TODO Убрать DEBUG code

    def get_user_info(self, data):
        msg_invalid_id = "No or invalid user_id"
        user_name = u''
        try:
            user_id = data['object']['user_id']
            if not user_id:
                raise ServiceException(msg_invalid_id)
        except KeyError:
            raise ServiceException(msg_invalid_id)
        try:
            r = urllib2.urlopen(
                "https://api.vk.com/method/users.get?user_ids=%s&v=5.0" % user_id
            )
            raw_data = r.read().decode(r.info().getparam('charset') or 'utf-8')
            user_data = json.loads(raw_data)
            user_name = user_data['response'][0]['first_name']
        except (urllib2.HTTPError, urllib2.URLError,
                KeyError, ValueError, IndexError,):
            pass
        return user_id, user_name

    def send_message(self, dict_greet):
        parms = urlencode(dict_greet)
        try:
            r = urllib2.urlopen(
                'https://api.vk.com/method/messages.send?%s' % parms
            )
        except (urllib2.HTTPError, urllib2.URLError,):
            raise ServiceException(msg_failed_send)

    def write_log(self, data, user_id, bot_settings):
        if bot_settings.get('log_file'):
            string = u"%s %s https://vk.com/id%s" % (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data['type'],
                user_id,
            )
            if data['type'] == 'message_new':
                try:
                    string += u" %s" % data['object']['body']
                except KeyError:
                    pass
            string += "\n"
            string = string.encode('utf-8')
            try:
                f = open(bot_settings['log_file'], 'a+')
                f.write(string)
                f.close()
            except IOError:
                pass

    def post(self, request, group):
        content_type = 'text/plain'
        message = 'ok'
        msg_failed_send = "Failed to send message to the user"
        data=request.DATA
        if settings.DEBUG:
            print "DEBUG: ..."
            print data
        try:
            if not hasattr(settings, 'VK_BOT') or \
                not settings.VK_BOT.get(group):
                raise ServiceException(
                    "No vk groups or no group '%s' defined." % group,
                )
            bot_settings = settings.VK_BOT[group]
            data_secret = data.get('secret', '')
            data_type = data.get('type', '')
            secretKey = bot_settings.get('secretKey', '')

            # проверяем secretKey
            if data_secret != secretKey and data_type != 'confirmation':
                raise ServiceException(
                    "No 'secret' or invalid 'secret' in inbound data when type is not confirmation",
                )

            if data_type == 'confirmation':
                message = bot_settings['confirmationToken']

            elif data_type == 'message_new':
                user_id, user_name = self.get_user_info(data)
                msg_to_user = u"Ваше сообщение зарегистрировано!<br>" \
                              u"Мы постараемся ответить в ближайшее время."
                if user_name:
                    msg_to_user = u"%s! %s" % (user_name, msg_to_user,)
                msg_to_user = msg_to_user.encode('utf-8')
                dict_greet = dict(
                    message=msg_to_user,
                    user_id=user_id,
                    access_token=bot_settings['token'],
                    v='5.0'
                )
                self.send_message(dict_greet)
                self.write_log(data, user_id, bot_settings)

            elif data_type == 'group_join':
                user_id, user_name = self.get_user_info(data)
                if bot_settings.get('msg_join'):
                    msg_to_user = bot_settings['msg_join']
                else:
                    msg_to_user = u"Добро пожаловать в наше сообщество!"
                if user_name:
                    msg_to_user = u"%s! %s" % (user_name, msg_to_user,)
                msg_to_user = msg_to_user.encode('utf-8')
                dict_greet = dict(
                    message=msg_to_user,
                    user_id=user_id,
                    access_token=bot_settings['token'],
                    v='5.0'
                )
                self.send_message(dict_greet)
                self.write_log(data, user_id, bot_settings)

            elif data_type == 'group_leave':
                user_id, user_name = self.get_user_info(data)
                if bot_settings.get('msg_leave'):
                    msg_to_user = bot_settings['msg_leave']
                else:
                    msg_to_user = u"Нам жаль прощаться с Вами. До новой встречи!"
                if user_name:
                    msg_to_user = u"%s! %s" % (user_name, msg_to_user,)
                msg_to_user = msg_to_user.encode('utf-8')
                dict_greet = dict(
                    message=msg_to_user,
                    user_id=user_id,
                    access_token=bot_settings['token'],
                    v='5.0'
                )
                self.send_message(dict_greet)
                self.write_log(data, user_id, bot_settings)

            status_code = 200
        except ServiceException as excpt:
            status_code = 400
            message = excpt.message
        return HttpResponse(message, content_type=content_type, status=status_code)

api_vk_bot_handler = ApiVkBotHandlerView.as_view()
