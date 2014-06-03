# coding=utf-8
import datetime
import decimal
import random
import string
import urllib2
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.loading import get_model
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from rest_framework import permissions

from geo.models import Location
from pd.models import BaseModel, Files, GetLogsMixin, validate_gt0, validate_username
from logs.models import Log

from pd.utils import DigitsValidator, LengthValidator, NotEmptyValidator


class PhonesMixin(object):
    @property
    def phone_set(self):
        ct = ContentType.objects.get_for_model(self)
        Phone = get_model('persons', 'Phone')
        return Phone.objects.filter(obj_id=self.pk, ct=ct)


class CommonProfile(BaseModel):
    USERNAME_HELPTEXT = _(u'До 30 символов: латинские буквы, цифры, дефис, знак подчеркивания')

    user = models.OneToOneField('auth.User', null=True)
    user_last_name = models.CharField(_(u"Фамилия"), max_length=255, null=True, blank=True)
    user_first_name = models.CharField(_(u"Имя"), max_length=255, null=True, blank=True)
    user_middle_name = models.CharField(_(u"Отчество"), max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.user and (self.full_name() or self.user.username) or u'%s' % self.pk

    def full_name(self):
        name = ""
        if self.user_last_name:
            name = self.user_last_name
            if self.user_first_name:
                name = u"{0} {1}".format(name, self.user_first_name)
                if self.user_middle_name:
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

    @classmethod
    def generate_password(cls):
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        # Очень трудно эти символы различать в смс-ках. Да и на экране, если без copy-paste
        # Удалим их из возможных в пароле:
        for c in '0OlI1':
            chars = chars.replace(c, '')
        password = ''.join(random.choice(chars) for x in range(5))
        return password

class CustomerProfile(CommonProfile):
    # Дата/время согласия с пользовательским соглашением, служит еще как BooleanField:
    tc_confirmed = models.DateTimeField(_(u"Подтверждено пользовательское соглашение"), null=True, editable=False)

    @classmethod
    def create_cabinet(cls, responsible):
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
                                    }
                                )
        return password

class CustomerProfilePhoto(Files):
    customerprofile = models.OneToOneField(CustomerProfile)
    
class Profile(CommonProfile):
    org = models.ForeignKey('users.Org', null=True)

    is_agent = models.BooleanField(_(u"Агент"), default=False, blank=True)

    cemetery = models.ForeignKey('burials.Cemetery', verbose_name=_(u"Кладбище"), blank=True, null=True)
    area = models.ForeignKey('burials.Area', verbose_name=_(u"Участок"), blank=True, null=True)

    lat = models.DecimalField(max_digits=30, decimal_places=27, blank=True, null=True)
    lng = models.DecimalField(max_digits=30, decimal_places=27, blank=True, null=True)

    def is_loru(self):
        return self.org and self.org.type == Org.PROFILE_LORU

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

def is_cabinet_user(user):
    try:
        user.customerprofile
        return True
    except (AttributeError, CustomerProfile.DoesNotExist, ):
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
    
class PermitIfLoru(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_loru_user(request.user)

class PermitIfUgh(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_ugh_user(request.user)

def get_mail_footer(user):
    footer = ''
    if user.is_authenticated():
        is_customer = is_cabinet_user(user)
        pr = user.customerprofile if is_customer else user.profile
        footer = _(     u'\n\n'
                        u'Пользователь: %s %s %s\n'
                        u'Email: %s\n'
                  ) % (
                        user.username,
                        '/' if pr.full_name() else '',
                        pr.full_name(),
                        user.email,
                       )
        if not is_customer:
            footer += _(    u'\n\n'
                            u'Организация: %s\n'
                            u'Email организации: %s\n'
                        ) % (
                                pr.org,
                                pr.org and pr.org.email,
                            )
    return footer

def get_default_currency():
    Currency = models.get_model('billing', 'Currency')
    return Currency.objects.get(code=settings.CURRENCY_DEFAULT_CODE)

class Oauth(models.Model):
    PROVIDER_YANDEX = 'yandex'
    PROVIDER_FACEBOOK = 'facebook'
    PROVIDER_GOOGLE = 'google'
    OAUTH_PROVIDERS = (
        (PROVIDER_YANDEX, _(u"Яндекс")),
        (PROVIDER_FACEBOOK, _(u"Facebook")),
        (PROVIDER_GOOGLE, _(u"Google")),
    )
    
    OAUTH_URLS = {
        PROVIDER_YANDEX: "https://login.yandex.ru/info?format=json&oauth_token=%s",
        PROVIDER_FACEBOOK: "https://graph.facebook.com/me?access_token=%s",
        PROVIDER_GOOGLE: "https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token=%s",
    }

    user = models.OneToOneField('auth.User')
    provider = models.CharField(_(u"Провайдер"), max_length=100, choices=OAUTH_PROVIDERS)
    uid = models.CharField(_(u"Ид пользователя у провайдера"), max_length=255,)
    
    class Meta:
        unique_together = ('user', 'provider',)

    @classmethod
    def check_token(cls, provider, token, username=None, password=None, profile=None):
        """
        Проверить token у провайдера.
        
        Если задан username, то создать пользователя с паролем password и
        атрибутами профиля profile
        Возвращает user, status: 
            user:   объект пользователя или None при неуспешной аутентификации/регистрации,
            status: сообщение об ошибке, если таковая произошла
        """
        user = message = None
        if isinstance(token, unicode):
            token = token.encode('utf-8')
        token=urllib2.quote(token)
        try:
            url = Oauth.OAUTH_URLS[provider] % token
            r = urllib2.urlopen(url)
            data = json.loads(r.read().decode(r.info().getparam('charset') or 'utf-8'))
            uid = unicode(data['id'])
            if uid:
                if username:
                    # Регистрация нового пользователя
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults = {
                            'email': profile and profile.get('email') or '',
                        }
                    )
                    if created:
                        cls.objects.create(
                            user=user,
                            provider=provider,
                            uid=uid,
                        )
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
                    else:
                        message = _(u'Такой пользователь, %s, уже имеется') % username
                else:
                    # Проверка, есть ли такой пользовательским
                    user = cls.objects.filter(provider=provider, uid=uid)[0].user
        except KeyError:
            message = _(u'Провайдер Oauth, %s, не поддерживается') % provider
        except urllib2.URLError:
            message = _(u'Ошибка связи с провайдером %s') % provider
        except ValueError:
            message = _(u'Ошибка интерпретации ответа от провайдера %s') % provider
        except IndexError:
            message = _(u'Пользователь не найден среди зарегистрированных у провайдера %s') % provider
        return user, message

class Org(GetLogsMixin, BaseModel):
    NUM_EMPTY = 'empty'
    NUM_YEAR_UGH = 'year_ugh'
    NUM_YEAR_CEMETERY = 'year_cemetery'
    NUM_YEAR_MONTH_UGH = 'year_month_ugh'
    NUM_YEAR_MONTH_CEMETERY = 'year_month_cemetery'
    NUM_TYPES = (
        (NUM_EMPTY, _(u'Оставить пустым')),
        (NUM_YEAR_UGH, _(u'Год + порядковый (в пределах организации)')),
        (NUM_YEAR_CEMETERY, _(u'Год + порядковый (в пределах кладбища)')),
        (NUM_YEAR_MONTH_UGH, _(u'Год + месяц + порядковый (в пределах организации)')),
        (NUM_YEAR_MONTH_CEMETERY, _(u'Год + месяц + порядковый (в пределах кладбища)')),
    )

    PROFILE_ZAGS = 'zags'
    PROFILE_LORU = 'loru'
    PROFILE_UGH = 'ugh'
    PROFILE_COMPANY = 'company'
    PROFILE_TYPES = (
        (PROFILE_COMPANY, _(u"Юрлицо")),
        (PROFILE_ZAGS, _(u"ЗАГС")),
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
   
    type = models.CharField(_(u"Тип"), max_length=255, choices=PROFILE_TYPES)
    name = models.CharField(_(u"Название организации"), max_length=255, default='')
    full_name = models.CharField(_(u"Полное название"), max_length=255, default='')
    inn = models.CharField(_(u"ИНН"), max_length=255, default='')
    kpp = models.CharField(_(u"КПП"), max_length=255, default='', blank=True)
    ogrn = models.CharField(_(u"ОГРН/ОГРЮЛ"), max_length=255, default='', blank=True)
    director = models.CharField(_(u"Директор"), max_length=255, default='')
    email = models.EmailField(_(u"Email"), null=True, blank=True)
    phones = models.TextField(_(u"Телефоны"), blank=True, null=True)
    off_address = models.ForeignKey('geo.Location', verbose_name=_(u"Юр. адрес"), null=True, blank=True)
    numbers_algo = models.CharField(_(u"Заполнение номера захоронения"), max_length=255, choices=NUM_TYPES,
                                    default=NUM_EMPTY)
    opf_order = models.CharField(_(u"Заказчик по умолчанию в заказе"), max_length=255,
                                    choices=list(OPF_CHOICES)[1:], default=OPF_ORG)
    opf_order_customer_mandatory = models.BooleanField(_(u"Данные заказчика при оформлении заказа обязательны"),
                                    default=True)
    # название поля не заканчивается на date, чтоб не угодить под специфический datePicker widget для дат:
    plan_date_days_before = models.PositiveIntegerField(_(u"Кол-во дней для ввода плановой даты захоронения в прошлом"), default=0)
    max_graves_count = models.PositiveIntegerField(_(u"Максимальное число могил в месте"), default=5,
                                validators=[validate_gt0])
    worktime = models.CharField(_(u"Время работы (ЧЧ:ММ - ЧЧ:ММ)"), max_length=255, default='', blank=True)
    site = models.URLField(_(u"Сайт"), default='', blank=True)
    currency = models.ForeignKey('billing.Currency', verbose_name=_(u"Валюта"), default=get_default_currency)

    class Meta:
        verbose_name = _(u'Организация')
        verbose_name_plural = _(u'Организации')

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
    def get_supervisor_email(cls):
        """
        Возвращает email-адрес Супервизора или seltings.DEFAULT_FROM_EMAIL
        """
        email = settings.DEFAULT_FROM_EMAIL
        try:
            email = cls.get_supervisor().email or email
        except AttributeError:
            pass
        return email

    @classmethod
    def get_add_pay_recipient(cls):
        """
        Возвращает организацию-получателя (и распределителя ;) доходов от рекламы
        """
        result = None
        try:
            return cls.objects.filter(inn=settings.ORG_AD_PAY_RECIPIENT['inn'])[0]
        except IndexError:
            return None

    @classmethod
    def get_pd_fund(cls):
        """
        Возвращает организацию-получателя (и распределителя ;) доходов от рекламы
        """
        result = None
        try:
            return cls.objects.filter(inn=settings.ORG_PD_FUND['inn'])[0]
        except IndexError:
            return None

class Store(models.Model, PhonesMixin):
    """
    Склады, магазины у ЛОРУ
    """
    name = models.CharField(_(u"Название"), max_length=255, default='')
    loru = models.ForeignKey(
        Org, verbose_name=_(u"ЛОРУ"), limit_choices_to={'type': Org.PROFILE_LORU},
        on_delete=models.PROTECT,
    )
    address = models.ForeignKey('geo.Location', verbose_name=_(u"Адрес"))
    # phones: могут быть разных типов, пользуемся моделью persons.Phone

class BankAccount(models.Model):
    """
    Банковские реквизиты
    """
    organization = models.ForeignKey(Org, verbose_name=u"Организация")
    rs = models.CharField(u"Расчетный счет", max_length=20, validators=[DigitsValidator(), LengthValidator(20), ])
    ks = models.CharField(u"Корреспондентский счет", max_length=20, blank=True, validators=[DigitsValidator(), LengthValidator(20), ])
    bik = models.CharField(u"БИК", max_length=9, validators=[DigitsValidator(), LengthValidator(9), ])
    bankname = models.CharField(u"Наименование банка", max_length=64, validators=[NotEmptyValidator(1), ])
    ls = models.CharField(u"Л/с", max_length=11, blank=True, null=True, validators=[LengthValidator(11), ])

class ProfileLORU(models.Model):
    ugh = models.ForeignKey(Org, related_name='loru_list', limit_choices_to={'type': Org.PROFILE_UGH}, verbose_name=_(u"ОМС"))
    loru = models.ForeignKey(Org, related_name='ugh_list', limit_choices_to={'type': Org.PROFILE_LORU}, verbose_name=_(u"ЛОРУ"))

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

class RegisterProfile(BaseModel):

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
    org_inn = models.CharField(_(u"ИНН"), max_length=255, default='')
    org_director = models.CharField(_(u"ФИО директора"), max_length=255, default='')
    org_phones = models.TextField(_(u"Телефоны"),
                                  help_text=_(u'В международном формате: +код-страны-код-города-номер-телефона')
                                 )
    org_address = models.ForeignKey(Location, editable=False, null=True)

    def __unicode__(self):
        fio = u'%s %s.' % (self.user_last_name, self.user_first_name[0].upper(), )
        if self.user_middle_name:
            fio += u'%s.' % self.user_middle_name[0].upper()
        return _(u'Заявка: %s/"%s"/%s/%s/%s') % (self.get_org_type_display(), self.org_name,
                                                 fio, self.user_name, self.user_email, )
    
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

    @classmethod
    def get_logs(cls):
        ct = ContentType.objects.get_for_model(cls)
        return Log.objects.filter(ct=ct).order_by('-pk')

class RegisterProfileScan(Files):
    """
    Файлы-сканы, прикрепляемые к завкам на регистрацию
    """
    registerprofile = models.OneToOneField(RegisterProfile)
