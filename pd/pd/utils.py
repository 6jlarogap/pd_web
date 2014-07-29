# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.validators import RegexValidator, MinLengthValidator
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
