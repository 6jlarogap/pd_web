# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.validators import RegexValidator, MinLengthValidator
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _

import datetime
from pytz import timezone, utc
import re

class DigitsValidator(RegexValidator):
    regex = '^\d+$'
    message = _(u'Допускаются только цифры')
    code = 'digits'

    def __init__(self):
        super(DigitsValidator, self).__init__(regex=self.regex)

class LengthValidator(MinLengthValidator):
    compare = lambda self, v, l: v != l
    message = _(u'Длина %(limit_value)s')
    code = 'length_custom'

class VarLengthValidator(MinLengthValidator):
    compare = lambda self, v, l:  not l[0] <= v <= l[1]
    message = _(u'Длина %(limit_value)s')
    code = 'length_custom1'

class NotEmptyValidator(MinLengthValidator):
    compare = lambda self, v, l:  not v
    clean = lambda self, x: unicode(x).strip()
    message = _(u'Не пусто')
    code = 'not_empty'

def utcisoformat(dt, remove_mcsec=True):
    """
    Return a datetime object in ISO 8601 format in UTC, without microseconds
    or time zone offset other than 'Z', e.g. '2011-06-28T00:00:00Z'.
    """
    # Convert datetime to UTC, remove microseconds, remove timezone, convert to string
    TZ = timezone(settings.TIME_ZONE)
    if remove_mcsec:
        dt = dt.replace(microsecond=0)
    return TZ.localize(dt).astimezone(utc).replace(tzinfo=None).isoformat() + 'Z'

def host_country_code(request):
    """
    Получить строку 'ru' запроса типа http://org.pohoronnodelo.ru

    Если к системе обращаются по ip-адресу или localhost или host,
    возвращается пустая строка
    """
    m = re.search(r'\.([a-zA-Z]{2,})(?:\:\d+)?$', request.get_host())
    if m:
        return m.group(1).lower()
    else:
        return ''

def phones_from_text(phones_text):
    phones = []
    if phones_text:
        for phone in phones_text.split('\n'):
            phone = phone.strip()
            if phone:
                phones.append(phone)
    return phones

class PhonesFromTextMixin(object):

    def phones_func(self, obj):
        return phones_from_text(obj.phones)

def str_to_bool_or_None(s):
    """
    Строку 'true' или 'false' преобразовать в boolean True/False или None, если строка не 'true'/'false'

    Применяется при разборе multipart/form-data параметров, чтоб были аналогичны разбору json параметров
    """
    result = None
    if isinstance(s, basestring):
        s = s.lower()
        if s == 'true':
            result = True
        elif s == 'false':
            result = False
    return result

class EmailMessage(EmailMessage):
    """
    Формирование, отправка почты
    
    В добавок к EmailMessage от django:
        - если почта от какого-то другого сервера, нежели производственного,
        тему письма предваряем "[dev] "
    """

    def send(self, **kwargs):
        if not settings.PRODUCTION_SITE:
            self.subject = u"[dev] %s" % self.subject
        if settings.BCC_OUR_MAIL:
            self.bcc.append(settings.BCC_OUR_MAIL)
        super(EmailMessage, self).send(**kwargs)

class CreatedAtMixin(object):
    def createdAt_func(self, instance):
        return utcisoformat(instance.dt_created)

    def modifiedAt_func(self, instance):
        return utcisoformat(instance.dt_modified)
