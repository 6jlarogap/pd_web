# coding=utf-8
import json
import datetime

from django.utils.translation import ugettext as _
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe

from burials.models import Burial
from logs.models import write_log


class ChildrenJSONMixin:
    def universal_children_json(self, parent, children_rel, filter_kw=None):
        parents = {}
        filter_kw = filter_kw or {}
        if self.fields.get(parent):
            for c in self.fields[parent].queryset:
                parents[c.pk] = [[a.pk, u'%s' % a] for a in getattr(c, children_rel).filter(**filter_kw)]
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
        return self.universal_children_json('agent', 'dover_set')

    def loru_agents_json(self):
        return self.universal_children_json('applicant_organization', 'profile_set', filter_kw={'is_agent': True})

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

