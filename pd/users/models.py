# coding=utf-8
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

from geo.models import DFiasAddrobj
from logs.models import Log
from pd.models import BaseModel, Files
from pd.utils import DigitsValidator, LengthValidator, NotEmptyValidator


class Profile(models.Model):
    user = models.OneToOneField('auth.User', null=True)
    user_first_name = models.CharField(_(u"Имя"), max_length=255, null=True, blank=True)
    user_middle_name = models.CharField(_(u"Отчество"), max_length=255, null=True, blank=True)
    user_last_name = models.CharField(_(u"Фамилия"), max_length=255, null=True, blank=True)
    org = models.ForeignKey('users.Org', null=True)

    is_agent = models.BooleanField(_(u"Агент"), default=False, blank=True)

    cemetery = models.ForeignKey('burials.Cemetery', verbose_name=_(u"Кладбище"), blank=True, null=True)
    area = models.ForeignKey('burials.Area', verbose_name=_(u"Участок"), blank=True, null=True)

    country = models.ForeignKey('geo.Country', verbose_name=_(u"Страна"), blank=True, null=True)
    region_fias = models.CharField(_(u"Регион"), blank=True, null=True, max_length=255)

    lat = models.DecimalField(max_digits=30, decimal_places=27, blank=True, null=True)
    lng = models.DecimalField(max_digits=30, decimal_places=27, blank=True, null=True)

    def __unicode__(self):
        return self.user and (self.full_name() or self.user.username) or u'%s' % self.pk

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

    def full_name(self):
        name = ""
        if self.user_last_name and self.user_first_name:
            name = u"{0} {1}".format(self.user_last_name, self.user_first_name)
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
        if self.user_last_name and self.user_first_name:
            name = u"{0} {1}.".format(self.user_last_name, self.user_first_name[0])
            if self.user_middle_name:
                name = u"{0}{1}.".format(name, self.user_middle_name[0])
        if not name:
            name = self.user.last_name
            if name and self.user.first_name:
                name = u"{0} {1}.".format(name, self.user.first_name[0])
        return self.user and (name or self.user.username) or u'%s' % self.pk

    def get_region(self):
        if self.region_fias:
            return DFiasAddrobj.objects.get(parentguid='', aoguid=self.region_fias)

    def get_coords(self):
        if self.lat and self.lng:
            return ','.join([self.lat, self.lng])
        return ''

class Org(BaseModel):
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
    archive_burial_fact_date_required = models.BooleanField(_(u"Дата архивного захоронения обязательна"), default=False)

    class Meta:
        verbose_name = _(u'Организация')
        verbose_name_plural = _(u'Организации')

    def __unicode__(self):
        return self.name

    def get_logs(self):
        ct = ContentType.objects.get_for_model(self)
        return Log.objects.filter(ct=ct, obj_id=self.pk).order_by('-pk')

    def is_inactive(self):
        return not self.profile_set.filter(user__is_active=True).exists()

    def get_loru_list(self):
        return [ul.loru for ul in self.loru_list.all()]

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
            email = cls.get_supervisor().email or email_from
        except AttributeError:
            pass
        # Система должна быть настроена на отправку почты
        # через действующий почтовый ящик на действующем сервере,
        # см. параметры settings.EMAIL_ ...
        # - если не удастся связаться с этим почтовым ящиком
        #   для отправки письма, здесь будет какое-то smtplib.SMTPException
        # - если недействительный получатель письма, то 
        #   email_from получит об этом сообщение средствами электронной
        #   почты, не относящимися к этому приложению.
        #
        return email

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
        (STATUS_APPROVED, _(u"Заявка подтверждена")),
    )

    status = models.CharField(_(u"Статус заявки"), max_length=255, choices=STATUS_CHOICES, editable=False)
    user_name = models.CharField(_(u"Имя для входа в систему (login)"), max_length=30)
    user_last_name = models.CharField(_(u"Фамилия"), max_length=255)
    user_first_name = models.CharField(_(u"Имя"), max_length=255)
    user_middle_name = models.CharField(_(u"Отчество"), max_length=255, null=True, blank=True)
    user_email = models.EmailField(_(u"Email"))
    # Сразу hash (django.contrib.auth.hashers.make_password(raw_password)):
    user_password = models.CharField(_(u"Пароль"), max_length=255, editable=False, default='')
    user_activation_key = models.CharField(_(u'Ключ активации'), max_length=40, editable=False)
    org_type = models.CharField(_(u"Тип организации"), max_length=255, choices=REG_ORG_TYPES, default=REG_ORG_UGH)
    org_name = models.CharField(_(u"Краткое название организации"), max_length=255, default='')
    org_full_name = models.CharField(_(u"Полное название организации"), max_length=255, default='')
    org_inn = models.CharField(_(u"ИНН"), max_length=255, default='')
    org_director = models.CharField(_(u"ФИО директора"), max_length=255, default='')
    org_phone = models.CharField(_(u"Телефон"), max_length=30, default='')
    org_fax = models.CharField(_(u"Факс"), max_length=30, null=True, blank=True)

    def __unicode__(self):
        return _(u"Заявка от организации %s, %s") % (self.org_name, self.user_email)
    
    def is_to_confirm(self):
        return self.status == self.STATUS_TO_CONFIRM

    def is_confirmed(self):
        return self.status == self.STATUS_CONFIRMED

    def is_approved(self):
        return self.status == self.STATUS_APPROVED

    def is_declined(self):
        return self.status == self.STATUS_DECLINED

class RegisterProfileScan(Files):
    """
    Файлы-сканы, прикрепляемые к завкам на регистрацию
    """
    registerprofile = models.OneToOneField(RegisterProfile)
