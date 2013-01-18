# -*- coding: utf-8 -*-

from django.core.validators import RegexValidator, MinLengthValidator

import datetime

class DigitsValidator(RegexValidator):
    regex = '^\d+$'
    message = u'Допускаются только цифры'
    code = 'digits'

    def __init__(self):
        super(DigitsValidator, self).__init__(regex=self.regex)

class LengthValidator(MinLengthValidator):
    compare = lambda self, v, l: v != l
    message = u'Длина %(limit_value)s'
    code = 'length_custom'

class VarLengthValidator(MinLengthValidator):
    compare = lambda self, v, l:  not l[0] <= v <= l[1]
    message = u'Длина %(limit_value)s'
    code = 'length_custom1'

class NotEmptyValidator(MinLengthValidator):
    compare = lambda self, v, l:  not v
    clean = lambda self, x: unicode(x).strip()
    message = u'Не пусто'
    code = 'not_empty'

PER_PAGE_VALUES = (
    (10, '10'),
    (25, '25'),
    (50, '50'),
)

ORDER_BY_VALUES = (
    ('person__last_name', '+фамилии'),
    ('-person__last_name', '-фамилии'),
    ('person__first_name', '+имени'),
    ('-person__first_name', '-имени'),
    ('person__middle_name', '+отчеству'),
    ('-person__middle_name', '-отчеству'),
    ('date_fact', '+дате захоронения'),
    ('-date_fact', '-дате захоронения'),
    ('account_number', '+номеру в книге учета'),
    ('-account_number', '-номеру в книге учета'),
    ('place__area', '+участку'),
    ('-place__area', '-участку'),
    ('place__row', '+ряду'),
    ('-place__row', '-ряду'),
    ('place__seat', '+месту'),
    ('-place__seat', '-месту'),
    ('place__cemetery__name', '+кладбищу'),
    ('-place__cemetery__name', '-кладбищу'),
    )

class UnclearDate:
    def __init__(self, year, month=None, day=None):
        self.d = datetime.date(year, month or 1, day or 1)
        self.no_day = not day
        self.no_month = not month

    def strftime(self, format):
        if self.no_day:
            format = format.replace('%d', '-')
        if self.no_month:
            format = format.replace('%m', '-')
        return self.d.strftime(format)

    @property
    def year(self):
        return self.d.year

    @property
    def month(self):
        return not self.no_month and self.d.month or None

    @property
    def day(self):
        return not self.no_month and self.d.day or None

