# -*- coding: utf-8 -*-

from django.core.validators import RegexValidator, MinLengthValidator
from django.utils.translation import ugettext_lazy as _

import datetime

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
