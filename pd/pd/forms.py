# coding=utf-8
import json
import datetime
import re

import django
from django import forms
from django.conf import settings
from django.db.models.fields.files import FieldFile
from django.forms.extras.widgets import SelectDateWidget, RE_DATE, _parse_date_fmt
from django.utils.dates import MONTHS
from django.utils.formats import get_format
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.forms.widgets import ClearableFileInput, CheckboxInput

from django.utils.translation import ugettext as _
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe

from captcha.fields import ReCaptchaField

from burials.models import Burial, Area, PlaceSize
from logs.models import write_log
from pd.models import UnclearDate
from pd.utils import host_country_code, get_image
from users.models import Profile, Dover


class ChildrenJSONMixin:
    def universal_children_json(self, parent, ch_model, ch_rel, filter_kw=None, related=None):
        parents = {}
        filter_kw = filter_kw or {}
        related = related or []
        if self.fields.get(parent):
            parent_qs = self.fields[parent].queryset
            ch_qs = ch_model.objects.filter(**filter_kw).filter(**{ch_rel+'__in': parent_qs})
            ch_qs = ch_qs.select_related(ch_rel, *related)
            for c in ch_qs:
                p = getattr(c, ch_rel)
                if not parents.get(p.pk):
                    parents[p.pk] = []
                parents[p.pk].append([c.pk, u'%s' % c])
        return mark_safe(json.dumps(parents))

    def cemetery_areas_json(self):
        return self.universal_children_json('cemetery', Area, 'cemetery', related=['purpose'])

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
        kw = {'target_org': self.request.user.profile.org}
        return self.universal_children_json('agent', Dover, 'agent', filter_kw=kw, related=['agent', 'agent__user'])

    def place_size_json(self):
        sizes = {}
        for place_size in PlaceSize.objects.filter(org=self.request.user.profile.org):
            sizes[place_size.graves_count] = {'place_length': str(place_size.place_length),
                                              'place_width': str(place_size.place_width)
                                             }
        return mark_safe(json.dumps(sizes))

    def actual_dover_list(self):
        today = datetime.date.today()
        actual_dover_ids = Dover.objects.filter(begin__lte=today, end__gte=today)
        actual_dover_ids = actual_dover_ids.filter(target_org=self.request.user.profile.org)
        actual_dover_ids = actual_dover_ids.values_list('id', flat=True)
        return actual_dover_ids

    def loru_agents_json(self):
        kw = {'is_agent': True}
        return self.universal_children_json('applicant_organization', Profile, 'org', filter_kw=kw, related=['user'])

class LoggingFormMixin:
    def get_prefix(self, form):
        return u''

    def collect_log_data(self):
        self.changed_list = []
        obj = self.instance
        if obj and obj.pk:
            if isinstance(obj, Burial):
                obj = Burial.objects.get(pk=obj.pk)
            else:
                obj = None
            forms = self.forms if hasattr(self, 'forms') else []
            for form in [self] + forms:
                prefix = self.get_prefix(form)
                for f in form.changed_data:
                    if f in ('password1', 'password2',):
                        continue
                    old_value = obj and getattr(obj, f, None) or form.initial.get(f)
                    new_value = form.cleaned_data.get(f)
                    if not old_value and not isinstance(old_value, bool):
                        old_value = ''
                    if not new_value and not isinstance(new_value, bool):
                        new_value = ''

                    if isinstance(old_value, datetime.date) or isinstance(old_value, UnclearDate):
                        old_value = old_value.strftime('%d.%m.%Y')
                    if isinstance(new_value, datetime.date) or isinstance(new_value, UnclearDate):
                        new_value = new_value.strftime('%d.%m.%Y')
                    if isinstance(old_value, datetime.time):
                        old_value = old_value.strftime('%H:%M')
                    if isinstance(new_value, datetime.time):
                        new_value = new_value.strftime('%H:%M')

                    if isinstance(form.fields[f], django.forms.models.ModelMultipleChoiceField):
                        if not old_value:
                            old_value = u"[]"
                        else:
                            old_value = u", ".join([unicode(form.fields[f]._queryset.model.objects.get(pk=u)) for u in old_value])
                            old_value = u"[" + old_value + u"]"
                        if not new_value:
                            new_value = u"[]"
                        else:
                            new_value = u"[" + u", ".join([unicode(u) for u in new_value]) + u"]"

                    if getattr(form.fields[f], 'queryset', None):
                        pass
                    elif getattr(form.fields[f], 'choices', None):
                        old_value = dict(form.fields[f].choices).get(old_value, old_value)
                        new_value = dict(form.fields[f].choices).get(new_value, new_value)

                    if old_value != new_value and form.fields[f].label:
                        self.changed_list.append((u'%s%s' % (prefix, form.fields[f].label), old_value, new_value))

    def put_log_data(self, msg=_(u'Захоронение сохранено'), log_instance=None):
        """
        Поместить сведения об изменениях в объекте формы в журнал

        msg:            заголовок изменений
        log_instance:   обычно это объект формы, но возможна ситуация,
                        когда в журнал вносятся данные об одном объекте,
                        а изменения касаются другого, например при правке данных
                        пользователя запись производится в журнал организации
        """
        if not log_instance:
            log_instance = self.instance
        if self.changed_list:
            changed_data_str = u'\n'.join([u'%s: %s -> %s' % cd for cd in self.changed_list])
            changed_data_str = changed_data_str. \
                                replace(u'True -> False', _(u'выключ.')). \
                                replace(u'False -> True', _(u'включ.'))
            write_log(self.request, log_instance, msg + u'\n' + changed_data_str)

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

class StrippedStringsMixin(object):
    
   def clean(self):
       for field in self.cleaned_data:
           if isinstance(self.cleaned_data[field], basestring):
               self.cleaned_data[field] = self.cleaned_data[field].strip()
       return self.cleaned_data

class CommentForm(StrippedStringsMixin, forms.Form):
    comment = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={'rows': 10, 'cols': 60, }
        ),
        required=False,
    )

class UnclearSelectDateWidget(SelectDateWidget):
    month_unclear = False
    year_unclear = False

    def __init__(self, attrs=None, years=None, required=True):
        if not years:
            # С 20 декабря будет показан и следующий год
            years = range((datetime.date.today() + datetime.timedelta(days=12)).year, 1899, -1)
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
                        v = datetime.datetime.strptime(value, input_format)
                        year_val, month_val, day_val = v.year, v.month, v.day
                    except ValueError:
                        pass
                else:
                    match = RE_DATE.match(value)
                    if match:
                        year_val, month_val, day_val = [int(v) for v in match.groups()]

        # choices = [(i, i) for i in self.years]
        # year_html = self.create_select(name, self.year_field, value, year_val, choices, {'class': 'date-year'})
        year_html = self.create_year_input(name, self.year_field, year_val, {
                    'class': 'date-year',
                    'type': 'text',
                    'maxlength': '4',
        })
        # choices = zip(MONTHS.keys(), MONTHS.keys())
        choices = MONTHS.items()
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
        if not y and m == d == "0" or \
           not y and m == d == "":
            return None

        self.no_day = self.no_month = False

        if y:
            y = y.strip()
            if re.search(r'^0+$', y):
                y = "0"
        if (m or d) and not y:
            y = "0"
        if y:
            try:
                ud = UnclearDate(int(y), int(m), int(d))
            except ValueError:
                return '%s-%s-%s' % (y, m, d)
            else:
                return ud
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

    def create_year_input(self, name, field, val, attrs):
        from django.forms.widgets import Input
        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name
        local_attrs = self.build_attrs(id=field % id_, **attrs)
        s = Input(attrs=attrs)
        input_html = s.render(field % name, unicode(val).rjust(4, '0') if val else val, local_attrs)
        return input_html

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
        if not value and self.required:
            raise forms.ValidationError(self.error_messages['required'])
        if isinstance(value, basestring):
            if not re.search(r'^\d{1,4}\-\d{1,2}-\d{1,2}$', value):
                raise forms.ValidationError(
                    _(u'Была введена неверная дата (г-м-д): %s') % value
                )
            try:
                datetime.datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                y, m, d = value.split('-')
                raise forms.ValidationError(
                    _(u'Была введена неверная дата (дд-мм-гггг): %(day)s-%(month)s-%(year)s') % dict(
                    day=d.rjust(2,'0'), month=m.rjust(2,'0'), year=y.rjust(4,'0'),
                ))
        elif isinstance(value, UnclearDate) and not value.no_day and value.no_month:
            raise forms.ValidationError(_(u'Нет месяца в дате'))
        return value

class OurReCaptchaField(ReCaptchaField):
    
    def __init__(self, *args, **kwargs):
        super(OurReCaptchaField, self).__init__(*args, **kwargs)
        self.error_messages['captcha_invalid'] = _(u'Неверно. Попробуйте еще раз.')

class BaseModelForm(forms.ModelForm):
    """
    Базовая форма для базовой модели (с датой создания, модификации)
    
    При сохранении ModelForm, даже если ничего не изменилось
    в полях формы по сравнении с реальными данными,
    поле даты/времени последней модификации тоже меняется,
    что не отражает настоящую дату/время последней модификации,
    поэтому сохранение объекта формы поизводится только если
    в полях формы произошли изменения.
    """

    def save(self, forceCommit=False, commit=True, *args, **kwargs):
        """
        Сохранение instance формы в базу -- при commit=True -- если:
        - в полях формы произошли изменения;
        - операция insert (а не update существующей записи):
            можно считать в этом случае, что изменения произошли:
            не было ничего и вдруг должно возникнуть в базе;
        - если задан параметр forceCommit
            (на тот случай, если форма зависит от других форм и это надо учесть)
        """
        obj = super(BaseModelForm, self).save(commit=False, *args, **kwargs)
        if commit and (self.changed_data or not self.instance.pk or forceCommit):
            obj.save()
        return obj

class CustomUploadModelForm(forms.ModelForm):
    
    # Если такой макс. размер не устраивает, то в потомках класса
    # надо менять в соответствующий __init__(self)
    #
    MAX_UPLOAD_SIZE_MB = 2

    # 'bfile' -- такое имя у нас в моделях для файлового поля

    # Вызывается после инициализации формы-потомка:
    #
    def init_bfile(self):
        self.fields['bfile'].label = _(u'Скан')
        # Это пришлось сделать, чтобы при ошибке file upload
        # показывать исходный файл:
        try:
            self.fields['bfile'].widget.url = None
            if self.instance.pk:
                self.fields['bfile'].widget.url_ = self.instance.bfile.url
        except AttributeError:
            pass

    def clean_bfile(self):
        bfile = self.cleaned_data.get('bfile')
        # В upload file field может оказаться:
        # - типа None или пустой строки
        # - типа FieldFile, если уже есть файл в form.instance, а новый на замену его не ввели
        # - типа ...UploadFile (много разных таких типов),
        #        когда выполнен POST с прикрепленным файлом
        if bfile and not isinstance(bfile, FieldFile):
            if bfile.size > self.MAX_UPLOAD_SIZE_MB * 2**20:
                raise forms.ValidationError(
                    _(u'Попытка загрузки файла %(filename)s, превышен максимальный размер: %(max_size)s Мб.') % \
                    dict(filename=bfile._name, max_size=self.MAX_UPLOAD_SIZE_MB)
                )
            # К сожалению, разработчик поздно заметил, что есть тип поля в модели:
            # ImageFile, где есть проверка, что прикрепляемый к форме файл является
            # изображением, а модели с файловыми полями-изображениями были уже созданы.
            # Посему проверка здесь, если необходимо.
            if hasattr(self, 'CHECK_IF_IMAGE') and self.CHECK_IF_IMAGE:
                if not get_image(bfile):
                    raise forms.ValidationError(_(u"Прикрепленный файл не являлся изображением"))
        return bfile

class CustomClearableFileInput(ClearableFileInput):
    
    def __init__(self, show_clear_checkbox_=True, *args, **kwargs):
        super(CustomClearableFileInput, self).__init__(*args, **kwargs)
        self.show_clear_checkbox_ = show_clear_checkbox_

    def render(self, name, value, attrs=None):

        if self.show_clear_checkbox_:
            self.template_with_initial = u'%(initial_text)s: %(initial)s<br />%(clear_template)s<br />%(input_text)s:<br /> %(input)s<br />'
            self.template_with_clear = u'<label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s:</label> %(clear)s'
        else:
            self.template_with_initial = u'%(initial_text)s: %(initial)s<br />%(input_text)s:<br /> %(input)s<br />'
            self.template_with_clear = ''

        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }
        template = u'%(input)s'
        substitutions['input'] = super(ClearableFileInput, self).render(name, value, attrs)

        url = value and hasattr(value, "url") and value.url or \
              hasattr(self, "url_") and self.url_
        if url:
            template = self.template_with_initial
            substitutions['initial'] = (u'<a href="%s" target="_blank">%s</a>'
                                        % (escape(url),
                                           "("+_(u"просмотр")+")"))

            if self.show_clear_checkbox_ and not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)

class AppOrgFormMixin(object):

    def init_app_org_label(self):
        country_code = host_country_code(self.request)
        if country_code == 'by':
            self.fields['applicant_organization'].label += _(u' (наименование или УНП)')
        else:
            self.fields['applicant_organization'].label += _(u' (наименование или ИНН)')

    def opf_valid(self, main_form_class):
        """
        is_valid() для форм, где выбирается или организация, или физ-лицо
        """
        is_valid = super(main_form_class, self).is_valid()
        if not is_valid:
            return False
        if self.cleaned_data.get('opf') == 'org':
            for form_name in ('applicant_form', 'applicant_address_form', 'applicant_id_form', ):
                try:
                    f = getattr(self, form_name)
                    self.forms.remove(f)
                except (AttributeError, ValueError,):
                    continue
        return all([f.is_valid() for f in self.forms])
