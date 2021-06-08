import datetime

from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import gettext as _

from users.models import Org, Profile
from halls.models import Hall, HallWeekly

class HallItemForm(forms.ModelForm):

    class Meta:
        model = Hall
        exclude = ('org', )

    def clean_title(self):

        # Делаем почти все проверки в этом поле, включая проверки
        # по другим полям. Иначе, если бы был метод clean_time_start
        # и он породил бы исключение, то строчка разбивается.
        #
        title = self.cleaned_data['title'].strip()
        f = self
        if f['DELETE'].value():
            if f.instance and f.instance.pk and f.instance.halltimetable_set.exists():
                raise forms.ValidationError(_('Зал с назначенными сеансами удалить нельзя'))
        if not title:
            raise forms.ValidationError(_('Название зала не может быть пустым'))
        for f in self.formset:
                if f is not self and \
                   self['title'].value().strip() and \
                   f['title'].value().strip().upper() == self['title'].value().strip().upper():
                    raise forms.ValidationError(_('Залы не могут иметь одинаковые названия'))
        return title

class BaseHallFormset(BaseInlineFormSet):
    def __init__(self, request, *args, **kwargs):
        super(BaseHallFormset, self).__init__(*args, **kwargs)
        for f in self.forms:
            f.formset = self

HallFormset = inlineformset_factory(
    Org,
    Hall,
    form=HallItemForm,
    formset=BaseHallFormset,
    extra=1
)

class HallWeeklyItemForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(HallWeeklyItemForm, self).__init__(*args, **kwargs)
        f_dow = self.fields['dow']
        f_dow.widget.attrs.update(disabled="True")
        f_dow.label = ''
        f_dow.required = False

    def clean_dow(self):

        # Делаем почти все проверки в этом поле, включая проверки
        # по другим полям. Иначе, если бы был метод clean_time_start
        # и он породил бы исключение, то строчка разбивается.
        #
        dow = self.cleaned_data['dow']
        f = self
        dts = dict()
        for t in ('time_start', 'time_end', ):
            ft_value = f[t].value().strip()
            if ft_value == '24:00' and t == 'time_end':
                dts[t] = datetime.datetime.strptime('23:59', "%H:%M")
                dts[t] += datetime.timedelta(seconds=60)
            else:
                try:
                    dts[t] = datetime.datetime.strptime(ft_value, "%H:%M")
                except ValueError:
                    raise forms.ValidationError(_('Неверно: %s') % f[t].label)
        if dts['time_start'] >= dts['time_end']:
            raise forms.ValidationError(_('Время окончания работы зала меньше времени начала'))
        diff = dts['time_end'] - dts['time_start']
        if int(diff.total_seconds()/60) < int(f['interval'].value()):
            raise forms.ValidationError(_('Время работы зала меньше минимального времени на его посещение'))
        return dow

    class Meta:
        model = HallWeekly
        exclude = ('hall', )

class BaseHallWeeklyFormset(BaseInlineFormSet):
    def __init__(self, request, *args, **kwargs):
        super(BaseHallWeeklyFormset, self).__init__(*args, **kwargs)
        for f in self.forms:
            f.formset = self

HallWeeklyFormset = inlineformset_factory(
    Hall,
    HallWeekly,
    form=HallWeeklyItemForm,
    formset=BaseHallWeeklyFormset,
    extra=0,
    can_delete=False,
    
)

class HallTimeTableForm(forms.Form):

    hall_date_from = forms.DateField(label=_("Дата"))
    halls = forms.MultipleChoiceField(label=_("Залы"),choices=())

class HallTimeForm(forms.Form):

    hall_date_from = forms.DateField(label=_("Дата"))

class HallsExportForm(forms.ModelForm):

    TITLE_BY_NUMBER = 'number'
    TITLE_BY_TITLE = 'title'
    TITLE_BY_CHOICES = (
        (TITLE_BY_NUMBER, _('Выбранные залы в выводе нумеруются (Зал №1, Зал №2 ...)')),
        (TITLE_BY_TITLE, _('В выводе названия выбранных залов')),
    )

    date_from = forms.DateField(required=True, label=_("Дата"))
    halls = forms.MultipleChoiceField(label=_("Доступные залы"), choices = [], required=False)
    titleby = forms.ChoiceField(
        label='',
        choices=TITLE_BY_CHOICES,
        widget=forms.RadioSelect,
        initial=TITLE_BY_NUMBER,
    )

    class Meta:
        model = Profile
        fields = ('date_from', 'halls', 'titleby', )

    def clean_date_from(self):
        d = self.cleaned_data['date_from']
        if d > datetime.date.today():
            raise forms.ValidationError(_("Дата больше текущей"))
        return d

    def clean_halls(self):
        halls = self.cleaned_data['halls']
        if len(halls) == 0:
            raise forms.ValidationError(_("Не заданы залы"))
        return halls
