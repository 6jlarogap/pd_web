import datetime

from django import forms
from django.conf import settings
from django.forms.extras import SelectDateWidget
from utils.models import UnclearDate


class UnclearSelectDateWidget(SelectDateWidget):
    month_unclear = False
    year_unclear = False
    no_day = False
    no_month = False

    def value_from_datadict(self, data, files, name):
        from django.forms.extras.widgets import get_format, datetime_safe

        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = data.get(self.day_field % name)
        if y == m == d == "0":
            return None

        self.no_day = self.no_month = False

        if y:
            if settings.USE_L10N:
                input_format = get_format('DATE_INPUT_FORMATS')[0]
                try:
                    ud = UnclearDate(int(y), int(m), int(d))
                except ValueError, e:
                    return '%s-%s-%s' % (y, m, d)
                else:
                    self.no_month = ud.no_month
                    self.no_day = ud.no_day
                    date_value = datetime_safe.new_date(ud.d)
                return date_value.strftime(input_format)
            else:
                return '%s-%s-%s' % (y, m, d)
        return data.get(name, None)

    def render(self, name, value, attrs=None):
        if value:
            if isinstance(value, basestring):
                value = datetime.datetime.strptime(value, '%d.%m.%Y')
            year, month, day = value.year, value.month, value.day
            value = UnclearDate(year, not self.no_month and month or None, not self.no_day and day or None)
        return super(UnclearSelectDateWidget, self).render(name, value, attrs)

    def create_select(self, name, field, value, val, choices):
        from django.forms.extras.widgets import Select
        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name
        choices.insert(0, self.none_value)
        local_attrs = self.build_attrs(id=field % id_)
        s = Select(choices=choices)
        select_html = s.render(field % name, val, local_attrs)
        return select_html

class UnclearDateField(forms.DateField):
    today = datetime.date.today()

    widget = UnclearSelectDateWidget(years=range(today.month > 10 and today.day > 20 and (today.year + 1) or today.year, 1900, -1))

    def to_python(self, value):
        if isinstance(value, UnclearDate):
            return value
        return super(UnclearDateField, self).to_python(value)

