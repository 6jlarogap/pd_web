# coding=utf-8
import json
import datetime
from django import forms
from django.conf import settings
from django.forms.extras.widgets import SelectDateWidget, RE_DATE, _parse_date_fmt
from django.utils.dates import MONTHS
from django.utils.formats import get_format

from django.utils.translation import ugettext as _
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe

from burials.models import Burial
from logs.models import write_log
from pd.models import UnclearDate


class ChildrenJSONMixin:
    def universal_children_json(self, parent, children_rel, filter_kw=None, related=None):
        parents = {}
        filter_kw = filter_kw or {}
        related = related or []
        if self.fields.get(parent):
            for c in self.fields[parent].queryset:
                qs = getattr(c, children_rel).select_related(*related).filter(**filter_kw)
                parents[c.pk] = [[a.pk, u'%s' % a] for a in qs]
        return mark_safe(json.dumps(parents))

    def cemetery_areas_json(self):
        return self.universal_children_json('cemetery', 'area_set')

    def cemetery_times_json(self):
        parents = {}
        if self.fields.get('cemetery'):
            for c in self.fields['cemetery'].queryset:
                parents[c.pk] = c.get_time_choices(
                    date=self.instance.plan_date or self.initial.get('plan_date'),
                    request=self.request
                )
        return mark_safe(json.dumps(parents))

    def agent_dover_json(self):
        return self.universal_children_json('agent', 'dover_set', related=['agent', 'agent__user'])

    def loru_agents_json(self):
        return self.universal_children_json('applicant_organization', 'profile_set', filter_kw={'is_agent': True}, related=['user'])

class LoggingFormMixin:
    def get_prefix(self, form):
        return u''

    def collect_log_data(self):
        self.changed_list = []
        obj = self.instance
        if obj and obj.pk:
            obj = Burial.objects.get(pk=obj.pk)
            for form in [self] + self.forms:
                prefix = self.get_prefix(form)
                for f in form.changed_data:
                    old_value = obj and getattr(obj, f, None) or form.initial.get(f) or ''
                    new_value = form.cleaned_data.get(f) or ''

                    if isinstance(old_value, datetime.date):
                        old_value = old_value.strftime('%d.%m.%Y')
                    if isinstance(new_value, datetime.date):
                        new_value = new_value.strftime('%d.%m.%Y')
                    if isinstance(old_value, datetime.time):
                        old_value = old_value.strftime('%H:%M')
                    if isinstance(new_value, datetime.time):
                        new_value = new_value.strftime('%H:%M')

                    if getattr(form.fields[f], 'choices', None):
                        old_value = dict(form.fields[f].choices).get(old_value, old_value)
                        new_value = dict(form.fields[f].choices).get(new_value, new_value)

                    if old_value != new_value:
                        self.changed_list.append((u'%s%s' % (prefix, form.fields[f].label), old_value, new_value))

    def put_log_data(self, msg=_(u'Захоронение сохранено')):
        if self.changed_list or not self.instance or not self.instance.pk:
            changed_data_str = u'\n'.join([u'%s: %s -> %s' % cd for cd in self.changed_list])
            write_log(self.request, self.instance, msg + u'\n' + changed_data_str)
        else:
            write_log(self.request, self.instance, msg)

class PartialFormMixin:
    def _partial_html_output(self, fields=None, exclude=None, *args, **kwargs):
        old_fields = self.fields
        self.fields = SortedDict([(k,v) for k,v in self.fields.items() if (fields and k in fields) or (exclude and not k in exclude) or (not fields and not exclude)])
        result = self._html_output(*args, **kwargs)
        self.fields = old_fields
        return result

    def as_p_partial(self, fields=None, exclude=None):
        return self._partial_html_output(
            fields = fields,
            exclude = exclude,
            normal_row = '<p%(html_class_attr)s>%(label)s %(field)s%(help_text)s</p>',
            error_row = '%s',
            row_ender = '</p>',
            help_text_html = ' <span class="helptext">%s</span>',
            errors_on_separate_row = True)

    def print_fields_code(self):
        result = '<textarea>'
        for f in self.fields:
            result += '%(errors)s\n<p>%(label)s %(field)s%(help_text)s</p>\n\n' % {
                'label': '{{ form.%s.label_tag }}' % f,
                'field': '{{ form.%s }}' % f,
                'help_text': '<span class="helptext">{{ form.%s.help_text }}</span>' % f,
                'errors': '{{ form.%s.errors }}' % f,
                }
        result += "</textarea>"
        return result

class CommentForm(forms.Form):
    comment = forms.CharField(label=_(u'Комментарий'), widget=forms.Textarea)

class UnclearSelectDateWidget(SelectDateWidget):
    month_unclear = False
    year_unclear = False

    def __init__(self, attrs=None, years=None, required=True):
        if not years:
            years = range(datetime.date.today().year, 1899, -1)
        return super(UnclearSelectDateWidget, self).__init__(attrs, years, required)

    def render(self, name, value, attrs=None):
        if isinstance(value, datetime.date):
            value = UnclearDate(value.year, value.month, value.day)

        try:
            year_val = value.year
            month_val = None if value.no_month else value.month
            day_val = None if value.no_day else value.day
        except AttributeError:
            year_val = month_val = day_val = None
            if isinstance(value, basestring):
                if settings.USE_L10N:
                    try:
                        input_format = get_format('DATE_INPUT_FORMATS')[0]
                        # Python 2.4 compatibility:
                        #     v = datetime.datetime.strptime(value, input_format)
                        # would be clearer, but datetime.strptime was added in
                        # Python 2.5
                        v = datetime.datetime(*(datetime.time.strptime(value, input_format)[0:6]))
                        year_val, month_val, day_val = v.year, v.month, v.day
                    except ValueError:
                        pass
                else:
                    match = RE_DATE.match(value)
                    if match:
                        year_val, month_val, day_val = [int(v) for v in match.groups()]

        choices = [(i, i) for i in self.years]
        year_html = self.create_select(name, self.year_field, value, year_val, choices, {'class': 'date-year'})
        choices = zip(MONTHS.keys(), MONTHS.keys())
        month_html = self.create_select(name, self.month_field, value, month_val, choices, {'class': 'date-month'})
        choices = [(i, i) for i in range(1, 32)]
        day_html = self.create_select(name, self.day_field, value, day_val,  choices, {'class': 'date-day'})

        output = []
        for field in _parse_date_fmt():
            if field == 'year':
                output.append(year_html)
            elif field == 'month':
                output.append(month_html)
            elif field == 'day':
                output.append(day_html)
        return mark_safe(u'\n'.join(output))

    def value_from_datadict(self, data, files, name):
        from django.forms.extras.widgets import get_format, datetime_safe

        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = data.get(self.day_field % name)
        if y == m == d == "0" or y == m == d == "":
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
                    return ud
            else:
                return '%s-%s-%s' % (y, m, d)
        return data.get(name, None)

    def create_select(self, name, field, value, val, choices, attrs):
        from django.forms.extras.widgets import Select
        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name
        choices.insert(0, self.none_value)
        local_attrs = self.build_attrs(id=field % id_, **attrs)
        s = Select(choices=choices)
        select_html = s.render(field % name, val, local_attrs)
        return select_html

class UnclearDateField(forms.DateField):
    widget = UnclearSelectDateWidget()
    empty_strings_allowed = True

    def __init__(self, *args, **kwargs):
        super(UnclearDateField, self).__init__(*args, **kwargs)
        self.widget.required = self.required

    def to_python(self, value):
        if not value:
            return None
        if isinstance(value, UnclearDate):
            return value
        return super(UnclearDateField, self).to_python(value)

    def prepare_value(self, value):
        if not value:
            return None
        if isinstance(value, UnclearDate):
            return value
        return value

    def clean(self, value):
        return value

