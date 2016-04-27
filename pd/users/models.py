# coding=utf-8
import datetime
import decimal
import random
import string
import urllib2
import json, re
import hashlib

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import models, transaction, IntegrityError
from django.db.models.loading import get_model
from django.db.models.deletion import ProtectedError
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from autoslug import AutoSlugField

from rest_framework import permissions

from geo.models import Location
from pd.models import BaseModel, Files, GetLogsMixin, validate_gt0, validate_username, \
                      validate_phone_as_number, SafeDeleteMixin, PhotoFiles
from logs.models import Log, write_log, LogOperation

from pd.utils import DigitsValidator, LengthValidator, NotEmptyValidator, \
                     phones_from_text, capitalize
from pd.views import ServiceException

class PhonesMixin(object):
    @property
    def phone_set(self):
        ct = ContentType.objects.get_for_model(self)
        Phone = get_model('persons', 'Phone')
        return Phone.objects.filter(obj_id=self.pk, ct=ct)

    @property
    def phone_list(self):
        return [ phone.number for phone in self.phone_set ]

    def phone_str_list(self):
        return phones_from_text(self.phones)

class UserPhoto(Files):
    """
    Аватарки пользователя
    """
    # Макс. размер в мегабайтах
    MAX_SIZE = 5
    # Мин. ширина в пикселях
    MIN_SIZE_X = 200

    user = models.OneToOneField(User, related_name='user_photo_list')

class Role(models.Model):

    ROLE_ADMIN = 'admin'
    ROLE_REGISTRATOR = 'registrator'

    name = models.CharField(_(u"Код"), max_length=255, editable=False)
    title = models.CharField(_(u"Название"), max_length=255, editable=False)

    class Meta:
        verbose_name = _(u'Роль пользователя')

    def __unicode__(self):
        return self.title

class CommonProfile(BaseModel):
    USERNAME_HELPTEXT = _(u'До 30 символов: латинские буквы, цифры, дефисы, знаки подчеркивания, @')

    user = models.OneToOneField('auth.User', null=True)
    user_last_name = models.CharField(_(u"Фамилия"), max_length=255, null=True, blank=True)
    user_first_name = models.CharField(_(u"Имя"), max_length=255, null=True, blank=True)
    user_middle_name = models.CharField(_(u"Отчество"), max_length=255, null=True, blank=True)
    phones = models.TextField(_(u"Телефоны (если несколько, то через ; или ,)"), blank=True, null=True)
    birthday = models.DateField(_(u"Дата рождения у провайдера"), null=True, editable=False)
    site = models.URLField(_(u"Сайт пользователя"), max_length=255, default='', editable=False)

    class Meta:
        abstract = True
        ordering = ('user_last_name', 'user_first_name', 'user_middle_name', )

    def __unicode__(self):
        return self.user and (self.full_name() or self.user.username) or u'%s' % self.pk

    def full_name(self, put_middle_name=True):
        name = ""
        if self.user_last_name:
            name = self.user_last_name
            if self.user_first_name:
                name = u"{0} {1}".format(name, self.user_first_name)
                if put_middle_name and self.user_middle_name:
                    name = u"{0} {1}".format(name, self.user_middle_name)
        if not name:
            name = self.user.get_full_name()
        return name

    def last_name_initials(self):
        """
        Фамилия И.О.
        """
        name = ""
        if self.user_last_name:
            name = self.user_last_name
            if self.user_first_name:
                name = u"{0} {1}.".format(name, self.user_first_name[0])
                if self.user_middle_name:
                    name = u"{0}{1}.".format(name, self.user_middle_name[0])
        return self.user and (name or self.user.username) or u'%s' % self.pk

    def phone_list(self):
        return phones_from_text(self.phones)

    @classmethod
    def generate_password(cls):
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        # Очень трудно эти символы различать в смс-ках. Да и на экране, если без copy-paste
        # Удалим их из возможных в пароле:
        for c in '0OlI1':
            chars = chars.replace(c, '')
        password = ''.join(random.choice(chars) for x in range(5))
        return password

    def user_dict(self):
        return dict(
            id=self.user.pk,
            lastName=self.user_last_name,
            firstName=self.user_first_name,
            middleName=self.user_middle_name,
            organization=None,
        )

    def save(self, *args, **kwargs):
        self.user_first_name = capitalize(self.user_first_name)
        self.user_last_name = capitalize(self.user_last_name)
        self.user_middle_name = capitalize(self.user_middle_name)
        super(CommonProfile, self).save(*args, **kwargs)


class CustomerProfile(CommonProfile):
    # Дата/время согласия с пользовательским соглашением, служит еще как BooleanField:
    tc_confirmed = models.DateTimeField(_(u"Подтверждено пользовательское соглашение"), null=True, editable=False)
    login_phone = models.DecimalField(_(u"Мобильный телефон для входа в кабинет"), max_digits=15, decimal_places=0,
                  blank=True, null=True, db_index=True,
                  help_text=_(u'В международном формате, начиная с кода страны, без "+", например 79101234567'),
                  validators = [validate_phone_as_number, ])

    class Meta:
        unique_together = ('login_phone', )

    @classmethod
    def create_cabinet(cls, responsible, request):
        assert responsible and \
               hasattr(responsible, 'login_phone') and \
               responsible.login_phone, \
               u'Cannot create cabinet user for the specified responsible'
        user, created = User.objects.get_or_create(username=responsible.login_phone)
        if created:
            user.is_active = True
        password = cls.generate_password()
        user.set_password(password)
        user.save()
        customprofile, created = cls.objects.get_or_create(user=user,
                                    defaults={
                                        'user_last_name': responsible.last_name,
                                        'user_first_name': responsible.first_name,
                                        'user_middle_name': responsible.middle_name,
                                        'login_phone': decimal.Decimal(responsible.login_phone)
                                    }
                                )
        responsible.user = user
        responsible.save()
        write_log(
            request,
            user,
            _(
                u"Создан пользователь кабинета\n"
                u"логин: %(username)s\n"
                u"ФИО: %(full_name)s"
            ) % dict(
                username=user.username,
                full_name=customprofile.full_name(),
        ))
        if is_trade_user(request.user):
            write_log(request, user, operation=LogOperation.INVITE_CUSTOMER_TO_TEMPLE)
        return user, password

class Profile(CommonProfile):
    org = models.ForeignKey('users.Org', null=True)

    is_agent = models.BooleanField(_(u"Агент"), default=False, blank=True)
    out_of_staff = models.BooleanField(_(u"Внештатный сотрудник"), default=False, blank=True)
    title = models.CharField(_(u"Должность"), max_length=255, blank=True)

    cemetery = models.ForeignKey('burials.Cemetery', verbose_name=_(u"Кладбище"), blank=True, null=True)
    area = models.ForeignKey('burials.Area', verbose_name=_(u"Участок"), blank=True, null=True)

    role = models.ManyToManyField(Role, verbose_name=_(u"Роли в организации"), blank=True)
    cemeteries = models.ManyToManyField('burials.Cemetery',
                 verbose_name=_(u"Доступные кладбища"), related_name='rw_profiles', blank=True)

    store = models.ForeignKey('users.Store', verbose_name=_(u"Подразделение"), blank=True, null=True)

    lat = models.DecimalField(max_digits=30, decimal_places=27, blank=True, null=True)
    lng = models.DecimalField(max_digits=30, decimal_places=27, blank=True, null=True)

    def is_loru(self):
        return self.org and self.org.type == Org.PROFILE_LORU

    def is_trade(self):
        return self.org and self.org.is_trade()

    def is_ugh(self):
        return self.org and self.org.type == Org.PROFILE_UGH

    def is_supervisor(self):
        return hasattr(settings, 'SUPERVISOR_ORG_INN') and \
               self.org and \
               self.org.inn == settings.SUPERVISOR_ORG_INN

    def can_create_burials(self):
        return self.is_ugh() or self.is_loru()

    def get_coords(self):
        if self.lat and self.lng:
            return ','.join([self.lat, self.lng])
        return ''

    def user_dict(self):
        result = super(Profile, self).user_dict()
        result.update(dict(
            organization=dict(
                id=self.org.pk,
                name=self.org.name,
            ) if self.org else None
        ))
        return result

    def is_admin(self):
        return self.role.filter(name=Role.ROLE_ADMIN).exists()

    def is_registrator(self):
        return self.is_ugh() and self.role.filter(name=Role.ROLE_REGISTRATOR).exists()

    def has_all_cemeteries(self):
        Cemetery = get_model('burials', 'Cemetery')
        return self.cemeteries.all().count() == Cemetery.objects.filter(ugh=self.org).count()

def is_cabinet_user(user):
    try:
        user.customerprofile
        return True
    except (AttributeError, CustomerProfile.DoesNotExist, ):
        return False
    
def is_trade_user(user):
    try:
        return user.profile.is_trade()
    except (AttributeError, Profile.DoesNotExist, ):
        return False
    
def is_loru_user(user):
    try:
        return user.profile.is_loru()
    except (AttributeError, Profile.DoesNotExist, ):
        return False
    
def is_ugh_user(user):
    try:
        return user.profile.is_ugh()
    except (AttributeError, Profile.DoesNotExist, ):
        return False
    
def is_supervisor(user):
    try:
        return user.profile.is_supervisor()
    except (AttributeError, Profile.DoesNotExist, ):
        return False

def get_profile(user):
    profile = None
    if user:
        if is_cabinet_user(user):
            profile = user.customerprofile
        else:
            try:
                profile = user.profile
            except (AttributeError, Profile.DoesNotExist, ):
                pass
    return profile

def user_dict(user):
    result = None
    if user:
        profile = get_profile(user)
        if profile:
            result = profile.user_dict()
    return result

class PermitIfTrade(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_trade_user(request.user)

class PermitIfTradeOrSupervisor(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_trade_user(request.user) or is_supervisor(request.user)

class PermitIfTradeOrCabinet(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_trade_user(request.user) or is_cabinet_user(request.user)

class PermitIfUgh(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_ugh_user(request.user)

class PermitIfLoruOrUgh(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_loru_user(request.user) or \
               is_ugh_user(request.user)

class PermitIfCabinet(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_cabinet_user(request.user)

def get_mail_footer(user):
    footer = ''
    if user.is_authenticated():
        is_customer = is_cabinet_user(user)
        pr = user.customerprofile if is_customer else user.profile
        footer = _(     u'\n\n'
                        u'Пользователь: %(username)s %(slash)s %(full_name)s\n'
                        u'Email: %(email)s\n'
                  ) % dict(
                        username=user.username,
                        slash='/' if pr.full_name() else '',
                        full_name=pr.full_name(),
                        email=user.email or '',
                       )
        if not is_customer:
            footer += _(    u'\n\n'
                            u'Организация: %(org)s\n'
                            u'Email организации: %(email)s\n'
                        ) % dict(
                                org=pr.org and pr.org or '',
                                email=pr.org and pr.org.email or '',
                            )
    return footer

def get_default_currency():
    Currency = models.get_model('billing', 'Currency')
    return Currency.objects.only('pk').get(code=settings.CURRENCY_DEFAULT_CODE)

class Oauth(BaseModel):
    PROVIDER_YANDEX = 'yandex'
    PROVIDER_FACEBOOK = 'facebook'
    PROVIDER_GOOGLE = 'google'
    PROVIDER_VKONTAKTE = 'vk'
    PROVIDER_ODNOKLASSNIKI = 'odnoklassniki'
    OAUTH_PROVIDERS = (
        (PROVIDER_YANDEX, _(u"Яндекс")),
        (PROVIDER_FACEBOOK, _(u"Facebook")),
        (PROVIDER_GOOGLE, _(u"Google")),
        (PROVIDER_VKONTAKTE, _(u"ВКонтакте")),
        (PROVIDER_ODNOKLASSNIKI, _(u"Одноклассники")),
    )

    # Куда идти для получения данных от провайдера и имена возвращаемых полей,
    # например, кото-то из провайдеров возвращает фамилию в last_name,
    # кто-то в family_name, а кто-то вообще не возвращает фамилию,
    # а только типа display_name. Если провайдер не возвращает, например,
    # first_name, то в соответствующей profile_detail будет 'first_name': None
    #
    PROVIDER_DETAILS = {
        PROVIDER_YANDEX: {
            'url': "https://login.yandex.ru/info?format=json&oauth_token=%(accessToken)s",
            'uid': 'id',
            'first_name': "first_name",
            'last_name': "last_name",
            'middle_name': None,
            'display_name': "real_name",
            'email': 'default_email',
            'birthday': 'birthday',
            'birthday_format': '%Y-%m-%d',
            'photo': 'default_avatar_id',
            'photo_template': u'https://avatars.yandex.net/get-yapic/%(photo_id)s/islands-200'
        },
        PROVIDER_FACEBOOK: {
            'url': "https://graph.facebook.com/me?"
                   "fields=id,name,first_name,last_name,middle_name,"
                   "picture.width(200).height(200),email&"
                   "access_token=%(accessToken)s",
            'uid': 'id',
            'first_name': "first_name",
            'last_name': "last_name",
            'middle_name': "middle_name",
            'display_name': "name",
            'email': 'email',
            'photo': 'picture',
        },
        PROVIDER_GOOGLE: {
            'url': "https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token=%(accessToken)s",
            'uid': 'id',
            'first_name': "given_name",
            'last_name': "family_name",
            'middle_name': None,
            'display_name': "name",
            'email': 'email',
            'photo': 'picture',
        },
        PROVIDER_VKONTAKTE: {
            'url': "https://api.vk.com/method/users.get?access_token=%(accessToken)s"
                   "&fields=uid,first_name,last_name,bdate,photo_200,contacts,site",
            'uid': 'uid',
            'first_name': "first_name",
            'last_name': "last_name",
            'middle_name': None,
            'display_name': None,
            'birthday': 'bdate',
            'birthday_format': '%d.%m.%Y',
            'photo': 'photo_200',
            # Если такое приходит в фото, то это заглушка под отсутствие фото,
            # например, http://vk.com/images/camera_200.png
            'no_photo_re': r'/images/camera_\S*\.\S{3}$',
            'site': 'site',
        },
        PROVIDER_ODNOKLASSNIKI: {
            # Внимание! Именно http://
            'url': "http://api.odnoklassniki.ru/fb.do?method=users.getCurrentUser&"
                   "access_token=%(accessToken)s&"
                   "application_key=%(public_key)s&"
                   "fields=user.*&"
                   "format=json&"
                   "sig=%(signature)s",
            'uid': 'uid',
            'first_name': "first_name",
            'last_name': "last_name",
            'middle_name': None,
            'display_name': "name",
            'email': 'email',
            'birthday': 'birthday',
            'birthday_format': '%Y-%m-%d',
            'photo': 'pic190x190',
        },
    }

    user = models.ForeignKey('auth.User')
    provider = models.CharField(_(u"Провайдер"), max_length=100, choices=OAUTH_PROVIDERS)
    uid = models.CharField(_(u"Ид пользователя у провайдера"), max_length=255,)
    last_name = models.CharField(_(u"Фамилия у провайдера"), max_length=255, default='')
    first_name = models.CharField(_(u"Имя у провайдера"), max_length=255, default='')
    middle_name = models.CharField(_(u"Отчество у провайдера"), max_length=255, default='')
    display_name = models.CharField(_(u"Отображаемое имя у провайдера"), max_length=255, default='')
    email = models.EmailField(_(u"Email у провайдера"), max_length=255, default='')
    photo = models.URLField(_(u"Фото у провайдера"), max_length=255, default='')
    birthday = models.DateField(_(u"Дата рождения у провайдера"), null=True)
    phones = models.TextField(_(u"Телефоны (если несколько, то через ; или ,)"), null=True)
    site = models.URLField(_(u"Сайт пользователя"), max_length=255, default='')

    class Meta:
        # Не может быть двух пользователей с одним uid у того же провайдера!
        unique_together = ('provider', 'uid')

    def get_display_name(self):
        return self.display_name or \
               " ".join((self.first_name, self.last_name, )).strip()

    @classmethod
    @transaction.commit_on_success
    def check_token(cls, oauth_dict, signup_dict=None, bind_dict=None):
        """
        Проверить token у провайдера Oauth. Token & provider в входном oauth_dict
        
        oauth_dict:
        {
            "provider": "yandex",
            "accessToken": "....."
        }
        Проверяем у provider'a accessToken. Если успешно, то имеем uid
        пользователя у этого provider'a.
        После этого:
        *   Если задан signup_dict:
                {
                    'username': <username>, если нет, то генерируем имя
                    'password': <password>,
                    'profile': {
                        'lastname':
                        'firstname':
                        'middlename':
                        'email':
                    },
                    signup_if_absent: true или нет такого пользователя
                }
            то:
                - при bool(signup_if_absent) = False:
                    создать пользователя username c паролем password и атрибутами профиля profile.
                    Если profile не передан, то заполняем фио из данных социальной сети.
                    Если уже есть provider, uid в таблице Oauth, то ошибка.
                - при bool(signup_if_absent) = True:
                    Если есть provider, uid в таблице Oauth, то берем оттуда user'a и 
                    нормально завершаем функцию.
                    Если комбинация provider, uid в таблице Oauth не существует, то создаем
                    пользователя, как если бы bool(signup_if_absent) = False.
         *   Если задан bind_dict:
                {
                    'user': <объект user>,
                },
             то привязываем этого пользователя в таблице Oauth
         *  В остальных случаях проверка, что у нас есть такая запись в таблице Oauth

        Возвращает user, oauth, message: 
            user:       объект пользователя или None при неуспешной аутентификации/регистрации,
            oauth:      соответствующий этому пользователю только что созданный объект в таблице Oauth
            message:    словарь, который может состоять из { 'message': 'Сообщение об ошибке',
                        'errorCode': 'символический_код_ошибки' }
        """
        
        user = oauth = error_code = None
        message = {}
        provider = oauth_dict['provider']
        msg_intergrity_error = _(u'Есть уже пользователь, прикрепленный к этой учетной записи %s') % provider
        try:
            try:
                provider_details = Oauth.PROVIDER_DETAILS[provider]
            except KeyError:
                raise ServiceException(_(u'Провайдер Oauth, %s, не поддерживается') % provider)

            if provider == Oauth.PROVIDER_ODNOKLASSNIKI:
                oauth_dict['public_key'] = settings.OAUTH_PROVIDERS_KEYS[provider]['public_key']
                #
                # <signature> = md5(
                #    "application_key={$public_key}format=jsonmethod=users.getCurrentUser" .
                #     md5("{$tokenInfo['access_token']}{$client_secret}")) (php код)
                #
                m = hashlib.md5()
                m.update("%s%s" % (
                        oauth_dict['accessToken'],
                        settings.OAUTH_PROVIDERS_KEYS[provider]['private_key'],
                    )
                )
                m2 = m.hexdigest()
                m = hashlib.md5()
                m.update(
                    "application_key=%sfields=user.*format=jsonmethod=users.getCurrentUser%s" % (
                        settings.OAUTH_PROVIDERS_KEYS[provider]['public_key'],
                        m2,
                    )
                )
                oauth_dict['signature'] = m.hexdigest()

            for parm in ('accessToken', 'public_key', 'signature', ):
                if oauth_dict.get(parm):
                    if isinstance(oauth_dict[parm], unicode):
                        oauth_dict[parm] = oauth_dict[parm].encode('utf-8')
                    oauth_dict[parm] = urllib2.quote(oauth_dict[parm])
            url = provider_details['url'] % oauth_dict

            try:
                msg_debug = u", url: %s" % url if settings.DEBUG else ""
                r = urllib2.urlopen(url)
                raw_data = r.read().decode(r.info().getparam('charset') or 'utf-8')
            except urllib2.HTTPError as excpt:
                raise ServiceException(
                    _(u'Ошибка в ответе от провайдера %(provider)s, '
                      u'код: %(code)s, статус: %(reason)s%(msg_debug)s') % dict(
                        provider=provider,
                        code=excpt.getcode(),
                        reason=excpt.reason,
                        msg_debug=msg_debug
                ))
            except urllib2.URLError as excpt:
                reason = u": %s" % excpt.reason if excpt.reason else ''
                raise ServiceException(
                    _(u'Ошибка связи с провайдером%(reason)s%(msg_debug)s') % dict(
                        reason=reason,
                        msg_debug=msg_debug,
            ))

            try:
                data = json.loads(raw_data)
                if provider == Oauth.PROVIDER_VKONTAKTE and data.get('response'):
                    data = data['response'][0]
                uid = data[provider_details['uid']]
            except (KeyError, ValueError, IndexError):
                msg_debug = u" DEBUG: Request: %s. Response: %s" % (url, raw_data, ) \
                            if settings.DEBUG else u""
                raise ServiceException(
                    _(u"Ошибка интерпретации ответа от провайдера %(provider)s.%(msg_debug)s") % dict(
                        provider=provider, msg_debug=msg_debug,
                ))
            if not uid:
                raise ServiceException(_(u'Получен пустой %s от провайдера') % provider_details['uid'])

            uid = unicode(uid)
            user_details = {}
            for key in (
                    'first_name',
                    'last_name',
                    'middle_name',
                    'display_name',
                    'email',
                    'birthday',
                    'photo',
                    'site',
                    ):
                real_key = provider_details.get(key)
                if real_key:
                    user_details[key] = data.get(real_key, '')
                    if isinstance(user_details[key], basestring):
                        user_details[key] = user_details[key].strip()
                    if user_details[key]:
                        if key == 'birthday':
                            date_format = provider_details.get('birthday_format', '%Y-%m-%d')
                            try:
                                user_details[key] = datetime.datetime.strptime(
                                    user_details[key],
                                    date_format,
                                )
                            except ValueError:
                                del user_details[key]
                        elif key == 'photo':
                            if provider == Oauth.PROVIDER_YANDEX:
                                user_details[key] = provider_details['photo_template'] % \
                                                    dict(photo_id=user_details[key])
                            elif provider == Oauth.PROVIDER_VKONTAKTE:
                                if re.search(provider_details['no_photo_re'], user_details[key]):
                                    del user_details[key]
                            elif provider == Oauth.PROVIDER_GOOGLE:
                                user_details[key] = u"%s?sz=200" % user_details[key]
                            elif provider == Oauth.PROVIDER_FACEBOOK:
                                try:
                                    user_details[key] = user_details[key]['data']['url']
                                except (TypeError, KeyError):
                                    del user_details[key]
                        elif key == 'site':
                            if not re.search(r'^\w+\://', user_details[key]):
                                user_details[key] = u"http://%s" % user_details[key]
                            validate = URLValidator(verify_exists=False)
                            try:
                                validate(user_details[key])
                            except ValidationError:
                                del user_details[key]
                    else:
                        del user_details[key]
            if provider == Oauth.PROVIDER_VKONTAKTE:
                user_details['phones'] = u';'.join(
                                [ data.get(key, '') for key in ('mobile_phone', 'home_phone')]
                ).strip(u';').strip()
                if not user_details['phones']:
                    del user_details['phones']
            if signup_dict:
                try:
                    oauth = cls.objects.filter(provider=provider, uid=uid)[0]
                    user = oauth.user
                    if signup_dict.get('signup_if_absent'):
                        return user, oauth, message
                    else:
                        raise ServiceException(msg_intergrity_error)
                except IndexError:
                    pass

            if signup_dict:
                username = signup_dict.get('username')
                password = signup_dict.get('password')
                profile = signup_dict.get('profile') or {}
                email = profile.get('email') or user_details.get('email') or None
                if username:
                    try:
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults = {
                                'email': email,
                            }
                        )
                        if not created:
                            raise ServiceException(_(u'Такой пользователь, %s, уже имеется') % username)
                    except IntegrityError:
                        raise ServiceException(_(u'Есть уже пользователь с таким email: %s') % email)
                else:
                    chars = string.ascii_lowercase + string.digits
                    while True:
                        username  = ''.join(random.choice(chars) for x in range(8))
                        try:
                            user = User.objects.create(
                                username=username,
                                email=None,
                            )
                        except IntegrityError:
                            pass
                        else:
                            break
                    # Хорошо было бы дать здесь user.email = email; user.save(),
                    # Проверить, не было бы ошибки, а если бы была, то
                    # ингорировать. Но бд при такой ошибке говорит, что
                    # игнорирует всё до конца транзакции
                    if email:
                        if User.objects.filter(email=email).exists():
                            if profile.get('email'):
                                # задана была почта пользователем
                                raise ServiceException(_(u'Есть уже пользователь с таким email: %s') % email)
                            #else:
                                # Не устанавливаю user.email: Человек авторизовался из соц сети,
                                # была подхвачена его почта, но записывать эту почту в User нельзя,
                                # так как там такая почта уже есть
                        else:
                            try:
                                user.email = email
                                user.save()
                            except IntegrityError:
                                raise ServiceException(_(u'Есть уже пользователь с таким email: %s') % email)
                    password = CommonProfile.generate_password()
                try:
                    oauth = cls.objects.create(
                        user=user,
                        provider=provider,
                        uid=uid,
                        **user_details
                    )
                except IntegrityError:
                    raise ServiceException(msg_intergrity_error)
                if password:
                    user.set_password(password)
                    user.save()
                kwargs = {
                    'user_last_name': profile.get('lastname', '') or \
                                      user_details.get('last_name', ''),

                    'user_first_name': profile.get('firstname', '') or \
                                       user_details.get('first_name', ''),

                    'user_middle_name': profile.get('middlename', '') or \
                                        user_details.get('middle_name', ''),
                    'phones': user_details.get('phones'),
                    'birthday': user_details.get('birthday'),
                    'site': user_details.get('site', ''),
                }

                CustomerProfile.objects.create(
                    user=user,
                    tc_confirmed = datetime.datetime.now(),
                    **kwargs
                )
            elif bind_dict:
                # Привязка существующего пользователя к провайдеру
                user = bind_dict['user']
                try:
                    oauth, created = cls.objects.get_or_create(
                        user=user,
                        provider=provider,
                        uid=uid,
                        defaults=user_details
                    )
                except IntegrityError:
                    raise ServiceException(msg_intergrity_error)

                if not created:
                    for key in user_details:
                        setattr(oauth, key, user_details[key])
                    oauth.save()
            else:
                # Проверка, есть ли такой пользователь
                try:
                    oauth = cls.objects.filter(provider=provider, uid=uid)[0]
                    user = oauth.user
                except IndexError:
                    error_code = u"oauth_provider_not_attached"
                    raise ServiceException(_(u'Пользователь не найден среди зарегистрированных у провайдера %s') % provider)
        except ServiceException as excpt:
            transaction.rollback()
            message['message'] = excpt.message
            if error_code:
                message['errorCode'] = error_code
        return user, oauth, message

class ThankUser(models.Model):
    """
    Пользователь- кандидат на выражение благодарности
    """
    login_phone = models.DecimalField(_(u"Мобильный телефон для входа в кабинет"),
                                      max_digits=15, decimal_places=0, editable=False,
                                      unique=True)
    password = models.CharField(_(u"Пароль"), max_length=255, editable=False)

class Thank(BaseModel):
    """
    Благодарности

    Благодарности выносят пользователи (auth.User) по отношению к persons.CustomPerson
    """
    user = models.ForeignKey('auth.User', verbose_name=_(u"Пользователь"),)
    customperson = models.ForeignKey('persons.CustomPerson', verbose_name=_(u"Персона"),)

    class Meta:
        unique_together = ('user', 'customperson')

class OrgAbility(models.Model):
    ABILITY_TRADE = 'trade'
    ABILITY_PERSONAL_DATA = 'personal-data'
    ORG_ABILITIES = (
        (ABILITY_TRADE, _(u'Торговля')),
        (ABILITY_PERSONAL_DATA, _(u'Персональные данные')),
    )
    name = models.CharField(_(u"Название"), max_length=255, unique=True, choices=ORG_ABILITIES)
    title = models.CharField(_(u"Заглавие"), max_length=255)

    def __unicode__(self):
        return self.title

class Org(GetLogsMixin, BaseModel):
    NUM_EMPTY = 'empty'
    NUM_MANUAL = 'manual'
    NUM_YEAR_UGH = 'year_ugh'
    NUM_YEAR_CEMETERY = 'year_cemetery'
    NUM_YEAR_MONTH_UGH = 'year_month_ugh'
    NUM_YEAR_MONTH_CEMETERY = 'year_month_cemetery'
    NUM_TYPES = (
        (NUM_EMPTY, _(u'Оставить пустым')),
        (NUM_MANUAL, _(u'Вручную')),
        (NUM_YEAR_UGH, _(u'Год + порядковый (в пределах организации)')),
        (NUM_YEAR_CEMETERY, _(u'Год + порядковый (в пределах кладбища)')),
        (NUM_YEAR_MONTH_UGH, _(u'Год + месяц + порядковый (в пределах организации)')),
        (NUM_YEAR_MONTH_CEMETERY, _(u'Год + месяц + порядковый (в пределах кладбища)')),
    )

    PROFILE_ZAGS = 'zags'
    PROFILE_LORU = 'loru'
    PROFILE_UGH = 'ugh'
    PROFILE_COMPANY = 'company'
    PROFILE_MEDIC = 'medic'
    PROFILE_TYPES = (
        (PROFILE_COMPANY, _(u"Юрлицо")),
        (PROFILE_ZAGS, _(u"ЗАГС")),
        (PROFILE_MEDIC, _(u"Мед. учреждение")),
        (PROFILE_LORU, _(u"ЛОРУ")),
        (PROFILE_UGH, _(u"ОМС")),
    )

    OPF_EMPTY = 'empty'
    OPF_ORG = 'org'
    OPF_PERSON = 'person'
    OPF_CHOICES = (
        (OPF_EMPTY, _(u'Без заказчика')),
        (OPF_ORG, _(u'ЮЛ')),
        (OPF_PERSON, _(u'ФЛ')),
    )
   
    BASIS_CHARTER = 'charter'
    BASIS_CONDITION = 'condition'
    BASIS_CERTIFICATE = 'certificate'
    BASIS_PROXY = 'proxy'
    BASIS_CHOICES = (
        (BASIS_CHARTER, _(u'устава')),
        (BASIS_CONDITION, _(u'положения')),
        (BASIS_CERTIFICATE, _(u'свидетельства')),
        (BASIS_PROXY, _(u'доверенности')),
    )
    
    type = models.CharField(_(u"Тип"), max_length=255, choices=PROFILE_TYPES)
    ability = models.ManyToManyField(OrgAbility, editable=False)
    name = models.CharField(_(u"Название организации"), max_length=255, default='')
    slug = AutoSlugField(populate_from='name', max_length=255, editable=False,
                         unique=True, null=True, always_update=True)
    client_site_token = models.CharField(_(u"Токен клиентского сайта"), max_length=255, 
                        null=True, editable=False)
    full_name = models.CharField(_(u"Полное название"), max_length=255, default='', blank=True)
    description = models.TextField(_(u"Описание, направление деятельности"), blank=True, null=True)
    inn = models.CharField(_(u"ИНН"), max_length=255, default='', blank=True)
    kpp = models.CharField(_(u"КПП"), max_length=255, default='', blank=True)
    ogrn = models.CharField(_(u"ОГРН/ОГРЮЛ"), max_length=255, default='', blank=True)
    director = models.CharField(_(u"Директор"),
                                max_length=255, default='', blank=True)
    basis = models.CharField(_(u"Основание действия директора"), max_length=255, 
                             choices=BASIS_CHOICES, default=BASIS_CHARTER)
    email = models.EmailField(_(u"Email"), null=True, blank=True)
    phones = models.TextField(_(u"Телефоны"), blank=True, null=True)
    fax = models.CharField(_(u"Факс"), max_length=20, default='', blank=True)
    sms_phone = models.DecimalField(_(u"Мобильный телефон для СМС- уведомлений"), max_digits=15, decimal_places=0,
                  blank=True, null=True,
                  help_text=_(u'В международном формате, начиная с кода страны, без "+", например 79101234567'),
                  validators = [validate_phone_as_number, ])
    worktime = models.CharField(_(u"Время работы (ЧЧ:ММ - ЧЧ:ММ)"), max_length=255, default='', blank=True)
    site = models.URLField(_(u"Сайт"), default='', blank=True)
    shop_site = models.URLField(_(u"Сайт магазина"), default='', blank=True)
    currency = models.ForeignKey('billing.Currency', verbose_name=_(u"Валюта"), default=get_default_currency,
                                 help_text=_(u' При смене валюты она будет заменена у всех товаров (услуг) без корректировки цен'))
    is_wholesale_with_vat = models.BooleanField(_(u"Оптовые цены продуктов с НДС"), default=False)
    off_address = models.ForeignKey('geo.Location', verbose_name=_(u"Юр. адрес"), null=True, blank=True)
    subdomain = models.CharField(_(u"Поддомен"), max_length=255, null=True, editable=False)

    # Блок настроек умолчаний по заказам у ЛОРУ -----------------------------
    opf_order_customer_mandatory = models.BooleanField(_(u"Данные заказчика при оформлении заказа обязательны"),
                                    default=True)
    opf_order = models.CharField(_(u"Заказчик по умолчанию в заказе"), max_length=255,
                                    choices=list(OPF_CHOICES)[1:], default=OPF_ORG)
    # ----------------------------------------------------------------------

    # Блок настроек умолчаний по захоронениям -------------------------------
    numbers_algo = models.CharField(_(u"Заполнение номера захоронения"), max_length=255, choices=NUM_TYPES,
                                    default=NUM_MANUAL)
    # название поля не заканчивается на date, чтоб не угодить под специфический datePicker widget для дат:
    opf_burial = models.CharField(_(u"Заявитель по умолчанию в захоронении"), max_length=255,
                                    choices=list(OPF_CHOICES)[1:], default=OPF_ORG)
    death_date_offer = models.BooleanField(_(u"Предлагать дату смерти в новом захоронении"), default=False)
    hide_deadman_address = models.BooleanField(_(u"Скрыть адрес усопшего"), default=False)
    plan_time_required = models.BooleanField(_(u"Плановое время захоронения обязательно"), default=True)
    # название поля не заканчивается на date, чтоб не угодить под специфический datePicker widget для дат:
    plan_date_days_before = models.PositiveIntegerField(_(u"Кол-во дней для ввода плановой даты захоронения в прошлом"), default=3)
    max_graves_count = models.PositiveIntegerField(_(u"Максимальное число могил в месте"), default=5,
                                validators=[validate_gt0])
    # ----------------------------------------------------------------------

    class Meta:
        verbose_name = _(u'Организация')
        verbose_name_plural = _(u'Организации')
        unique_together = ('subdomain', )

    def __unicode__(self):
        return self.name

    def is_inactive(self):
        return not self.profile_set.filter(user__is_active=True).exists()

    def get_loru_list(self):
        return [ul.loru for ul in self.loru_list.all()]

    def create_wallet_rate(self, currency=None):
        """
        Создать кошелек и тарифы (тарифы -- только для ОМС) для организации
        """
        if not currency:
            currency = self.currency
        Wallet = models.get_model('billing', 'Wallet')
        wallet, created = Wallet.objects.get_or_create(
            org=self,
            currency=currency,
        )
        if self.type == self.PROFILE_UGH:
            Rate = models.get_model('billing', 'Rate')
            for action in (Rate.RATE_ACTION_PUBLISH, Rate.RATE_ACTION_UPDATE, ):
                rate, created = Rate.objects.get_or_create(
                    wallet=wallet,
                    action=action,
                    defaults = dict(
                        date_from=datetime.date.today(),
                        rate=decimal.Decimal('0.00'),
                    )
                )

    @classmethod
    def get_supervisor(cls):
        """
        Возвращает организацию-Супервизора или None
        """
        result = None
        if hasattr(settings, 'SUPERVISOR_ORG_INN'):
            try:
                result = cls.objects.filter(inn=settings.SUPERVISOR_ORG_INN)[0]
            except IndexError:
                pass
        return result

    @classmethod
    def get_catalog_org_pk(cls):
        """
        Возвращает первичный ключ организации-получателя (и распределителя ;)
        доходов от рекламы. Эта же организация является хранителем публичного
        каталога товаров и услуг
        """
        if settings.ORG_AD_PAY_RECIPIENT_PK is None:
            try:
                return cls.objects.filter(inn=settings.ORG_AD_PAY_RECIPIENT['inn'])[0].pk
            except IndexError:
                return 0
        else:
            return settings.ORG_AD_PAY_RECIPIENT_PK

    def phone_list(self):
        return phones_from_text(self.phones)

    def favorites_for_template(self):
        """
        [dict(name=favorite_name1, pk=favorite_pk1), dict(name=favorite_name2, pk=favorite_pk2), ...]

        Для шаблона, где в меню показаны избранные поставщики
        """
        def favorite_item(loru):
            name = loru.name.strip()
            if len(name) > 50:
                name = u"%s..." % name[:47]
            return dict(name=name, pk=loru.pk)

        result = []
        favorites = FavoriteSupplier.objects.filter(loru=self).exclude(supplier=self).order_by('supplier__name')
        if favorites.count():
            result.append(favorite_item(self))
            for favorite in favorites:
                result.append(favorite_item(favorite.supplier))
        return result

    def can_personal_data(self):
        """
        Может ли организация оперировать персональными данными в захоронениях
        """
        if self.type == self.PROFILE_UGH:
            return self.ability.filter(name=OrgAbility.ABILITY_PERSONAL_DATA).exists()
        elif self.type == self.PROFILE_LORU:
            # Если этот лору состоит в реестре у ОМС, никто из которых
            # не может вводить персональные данные, то и ему это запрещено
            return self.ugh_list.filter(ugh__ability__name=OrgAbility.ABILITY_PERSONAL_DATA).exists()
        else:
            return False

    def is_ugh(self):
        return self.type == Org.PROFILE_UGH

    def is_loru(self):
        return self.type == Org.PROFILE_LORU

    def is_trade(self):
        return self.ability.filter(name=OrgAbility.ABILITY_TRADE).exists()

    def phones_str(self):
        phones = self.phones or ''
        return u"; ".join(phones_from_text(phones))

class OrgWebPay(BaseModel):
    """
    Данные, в том числе секретные, поставщика в платежной системе WebPay
    """
    org = models.OneToOneField(Org)
    wsb_storeid = models.CharField(_(u"Идентификатор организации в системе WebPay"), max_length=255)
    secret = models.CharField(_(u"Секретный ключ"), max_length=255)

    # Это название должно совпадать с org.name, но в WebPay заказчик может ввести другое название.
    # Не исключено, что WebPay проверяет или будет проверять совпадение wsb_store в запросе
    # на оплату и наименование организации, каким оно прописано в WebPay
    #
    wsb_store = models.CharField(_(u"Название организации на форме оплаты WebPay"), max_length=255)

    # WebPay сейчас работает только с BYR; кроме того, валюта есть свойство организации,
    # так что поле wsb_currency_id может оказаться избыточным.
    # Но не исключается, что
    # - WebPay будет работать с другими валютами, в т.ч. с конвертацией,
    # - при возможности конвертации валюта организации может отличаться от WebPay
    # Посему, несмотря на избыточность поля, храним его в этой таблице
    #
    wsb_currency_id = models.CharField(_(u"Код валюты согласно ISO4271"), max_length=255, default='BYR')

    #  Версия формы оплаты, сейчас "2", но могут появляться новые
    #
    wsb_version = models.CharField(_(u"Версия формы оплаты"), max_length=255)

    # Будет устанавливаться в False по окончании тестирования
    #
    wsb_test = models.BooleanField(_(u"Тестовая среда"), default=True)

class OrgCertificate(Files):
    """
    Сканы свидетельств о регистрации
    """
    org = models.OneToOneField(Org)

class OrgGallery(Files):
    """
    Галерея организации. Для поставщиков товаров/услуг: образцы работ
    """
    org = models.ForeignKey(Org)

class OrgReview(BaseModel):
    """
    Отзывы об организации. Для поставщиков
    """
    org = models.ForeignKey(Org, editable=False, on_delete=models.PROTECT)
    subject = models.CharField(_(u"Тема отзыва"), max_length=255, blank=True)
    is_positive = models.NullBooleanField(_(u"Оценка положительная/отрицательна/без оценки"),
                                           null=True)
    common_text = models.TextField(_(u"Текст"), blank=True, null=True)
    positive_text = models.TextField(_(u"Текст положительной оценки"), blank=True, null=True)
    negative_text = models.TextField(_(u"Текст отрицательной оценки"), blank=True, null=True)
    creator = models.ForeignKey('auth.User', verbose_name=_(u"Создатель"),
                                on_delete=models.PROTECT, editable=False)

class OrgContract(Files):
    """
    Сгенерированный pdf договора с заказчиком
    """
    org = models.OneToOneField(Org)

class Store(models.Model, PhonesMixin):
    """
    Склады, магазины у ЛОРУ
    """
    name = models.CharField(_(u"Название"), max_length=255, default='')
    loru = models.ForeignKey(Org, verbose_name=_(u"ЛОРУ"), on_delete=models.PROTECT)
    address = models.ForeignKey('geo.Location', verbose_name=_(u"Адрес"))
    # phones: могут быть разных типов, пользуемся моделью persons.Phone

    def __unicode__(self):
        return self.name

    def delete(self):
        self.phone_set.delete()
        for photo in StorePhoto.objects.filter(store=self):
            photo.delete()
        super(Store, self).delete()
        try:
            self.address.delete()
        except (AttributeError, IntegrityError):
            pass

    def worktimes(self):
        return [{
                'dayindex': dayindex,
                'from': '09:00',
                'to': '18:00',
                'dinner': {
                    'from': '13:00',
                    'to': '14:00',
            }} for dayindex in range(1,6)]

class StorePhoto(PhotoFiles):
    store = models.OneToOneField(Store)

class FavoriteSupplier(models.Model):
    """
    Избранные поставщики у ЛОРУ
    """
    loru = models.ForeignKey(Org, verbose_name=_(u"ЛОРУ"),
        related_name='favorite_loru', on_delete=models.PROTECT, )
    supplier = models.ForeignKey(Org, verbose_name=_(u"ЛОРУ"),
        related_name='favorite_supplier_list', on_delete=models.PROTECT, )

    class Meta:
        unique_together = ('loru', 'supplier', )

class BankAccountCommon(models.Model):
    """
    Банковские реквизиты
    """
    class Meta:
        abstract = True
        
    rs = models.CharField(u"Расчетный счет", max_length=20, validators=[DigitsValidator(), LengthValidator(20), ])
    ks = models.CharField(u"Корреспондентский счет", max_length=20, blank=True, validators=[DigitsValidator(), LengthValidator(20), ])
    bik = models.CharField(u"БИК", max_length=9, validators=[DigitsValidator(), LengthValidator(9), ])
    bankname = models.CharField(u"Наименование банка", max_length=64, validators=[NotEmptyValidator(1), ])
    ls = models.CharField(u"Л/с", max_length=11, blank=True, null=True, validators=[LengthValidator(11), ])
    off_address = models.ForeignKey('geo.Location', verbose_name=_(u"Юр. адрес"), null=True, editable=False)

class BankAccount(BankAccountCommon):
    """
    Банковские реквизиты организации
    """
    organization = models.ForeignKey(Org, verbose_name=u"Организация")

class ProfileLORU(models.Model):
    ugh = models.ForeignKey(Org, related_name='loru_list', limit_choices_to={'type': Org.PROFILE_UGH}, verbose_name=_(u"ОМС"))
    loru = models.ForeignKey(Org, related_name='ugh_list', limit_choices_to={'type': Org.PROFILE_LORU}, verbose_name=_(u"ЛОРУ"))

    class Meta:
        verbose_name = _(u'ЛОРУ у ОМС')
        unique_together = ('ugh', 'loru')


def add_loru_to_public_catalog(sender, instance, created, **kwargs):
    if created and instance.type == Org.PROFILE_LORU:
        add_pay_recipient = Org.objects.get(
            inn=settings.ORG_AD_PAY_RECIPIENT['inn'],
            type=Org.PROFILE_UGH,
        )
        ProfileLORU.objects.create(ugh=add_pay_recipient, loru=instance)

models.signals.post_save.connect(add_loru_to_public_catalog, sender=Org)

class Dover(models.Model):
    agent = models.ForeignKey(Profile, verbose_name=_(u"Агент"), limit_choices_to={'is_agent': True})
    target_org = models.ForeignKey(Org, null=True, editable=False)
    number = models.CharField(_(u"Номер"), max_length=255)
    begin = models.DateField(_(u"Начало"))
    end = models.DateField(_(u"Окончание"))
    document = models.FileField(_(u"Скан доверенности"), upload_to='dover', blank=True, null=True)

    class Meta:
        verbose_name = _(u'Доверенность')
        verbose_name_plural = _(u'Доверенности')

    def __unicode__(self):
        return u'%s (%s - %s)' % (self.number, self.begin.strftime('%d.%m.%Y'), self.end.strftime('%d.%m.%Y'))

class RegisterProfile(SafeDeleteMixin, BaseModel):

    REG_ORG_UGH = Org.PROFILE_UGH
    REG_ORG_LORU = Org.PROFILE_LORU
    REG_ORG_TYPES = (
        (REG_ORG_UGH, _(u"Учет захоронений")),
        (REG_ORG_LORU, _(u"Учет заказов")),
    )
    
    STATUS_TO_CONFIRM = 'to_confirm'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_APPROVED = 'approved'
    STATUS_DECLINED = 'declined'
    STATUS_CHOICES = (
        (STATUS_TO_CONFIRM, _(u"Ожидание подтверждения")),
        (STATUS_CONFIRMED, _(u"Заявка подтверждена")),
        (STATUS_DECLINED, _(u"В регистрации отказано")),
        (STATUS_APPROVED, _(u"Пользователь в системе")),
    )
    
    # При подтверждении очередной заявки, существующие заявки, которые
    # уже обработаны (одобрены или получили отказ) и существуют
    # более этого числа дней, удаляются
    #
    CLEAR_PROCESSED = 30

    status = models.CharField(_(u"Статус заявки"), max_length=255, choices=STATUS_CHOICES, editable=False)
    user_name = models.CharField(_(u"Имя для входа в систему (login)"), max_length=30,
                                 validators=[validate_username], help_text=Profile.USERNAME_HELPTEXT)
    user_last_name = models.CharField(_(u"Фамилия"), max_length=255)
    user_first_name = models.CharField(_(u"Имя"), max_length=255)
    user_middle_name = models.CharField(_(u"Отчество (необязательно)"), max_length=255, null=True, blank=True)
    user_email = models.EmailField(_(u"Email"))
    # Сразу hash (django.contrib.auth.hashers.make_password(raw_password)):
    user_password = models.CharField(_(u"Пароль"), max_length=255, editable=False, default='')
    user_activation_key = models.CharField(_(u'Ключ активации'), max_length=40, editable=False)
    org_type = models.CharField(_(u"Тип организации"), max_length=255, choices=REG_ORG_TYPES, default=REG_ORG_UGH)
    org_name = models.CharField(_(u"Краткое название организации"), max_length=255, default='')
    org_full_name = models.CharField(_(u"Полное название организации"), max_length=255, default='')
    org_currency = models.ForeignKey('billing.Currency', verbose_name=_(u"Валюта"), default=get_default_currency)
    org_inn = models.CharField(_(u"ИНН"), max_length=255, default='')
    org_ogrn = models.CharField(_(u"ОГРН/ОГРЮЛ"), max_length=255, default='', blank=True)
    org_director = models.CharField(_(u"Директор"),
                                    max_length=255, default='')
    org_basis = models.CharField(_(u"Основание действия директора"), max_length=255, 
                             choices=Org.BASIS_CHOICES, default=Org.BASIS_CHARTER)
    org_phones = models.TextField(_(u"Телефоны"),
                                  help_text=_(u'В международном формате: +код-страны-код-города-номер-телефона')
                                 )
    org_fax = models.CharField(_(u"Факс"), max_length=20, default='', blank=True)
    org_address = models.ForeignKey(Location, editable=False, null=True)
    org_subdomain = models.CharField(_(u"Поддомен"), max_length=255, null=True, editable=False)

    def __unicode__(self):
        fio = u'%s %s.' % (self.user_last_name, self.user_first_name[0].upper(), )
        if self.user_middle_name:
            fio += u'%s.' % self.user_middle_name[0].upper()
        return _(u'Заявка: %(type)s/"%(org_name)s"/%(fio)s/%(user_name)s/%(user_email)s') % dict(
            type=self.get_org_type_display(),
            org_name=self.org_name,
            fio=fio,
            user_name=self.user_name,
            user_email=self.user_email,
        )
    
    @transaction.commit_on_success
    def delete(self):
        self.safe_delete('org_address', self)
        try:
            self.registerprofilescan.delete()
        except RegisterProfileScan.DoesNotExist:
            pass
        try:
            self.registerprofilecontract.delete()
        except RegisterProfileContract.DoesNotExist:
            pass
        for bank in self.bankaccountregister_set.all():
            self.safe_delete('off_address', bank)
            bank.delete()
        super(RegisterProfile, self).delete()
        
    def is_to_confirm(self):
        return self.status == self.STATUS_TO_CONFIRM

    def is_confirmed(self):
        return self.status == self.STATUS_CONFIRMED

    def is_approved(self):
        return self.status == self.STATUS_APPROVED

    def is_declined(self):
        return self.status == self.STATUS_DECLINED

    def orgs_same_inn(self):
        return Org.objects.filter(inn=self.org_inn)

    def same_username(self):
        return not self.is_approved() and not self.is_declined() and \
               User.objects.filter(username__iexact=self.user_name).exists()

    def same_email(self):
        return not self.is_approved() and not self.is_declined() and \
               User.objects.filter(email__iexact=self.user_email).exists()

    def same_subdomain(self):
        return self.org_subdomain and not self.is_approved() and not self.is_declined() and \
               Org.objects.filter(subdomain__iexact=self.org_subdomain).exists()

    @classmethod
    def get_logs(cls):
        ct = ContentType.objects.get_for_model(cls)
        return Log.objects.filter(ct=ct).order_by('-pk')

class RegisterProfileScan(Files):
    """
    Файлы-сканы, прикрепляемые к заявкам на регистрацию
    """
    registerprofile = models.OneToOneField(RegisterProfile)

class RegisterProfileContract(Files):
    """
    PDF файлы договоров с кандидатами на регистрацию
    """
    registerprofile = models.OneToOneField(RegisterProfile)

class BankAccountRegister(BankAccountCommon):
    """
    Банковские реквизиты кандидата на регистрацию
    """
    registerprofile = models.ForeignKey(RegisterProfile, verbose_name=u"Организация")

