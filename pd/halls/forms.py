import datetime

from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext as _

from users.models import Org
from halls.models import Hall

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
        dts = dict()
        for t in ('time_start', 'time_end', ):
            try:
                dts[t] = datetime.datetime.strptime(f[t].value().strip(), "%H:%M")
            except ValueError:
                raise forms.ValidationError(_('Неверно: %s') % f[t].label)
        if dts['time_start'] >= dts['time_end']:
            raise forms.ValidationError(_('Время окончания работы зала меньше времени начала'))
        diff = dts['time_end'] - dts['time_start']
        if int(diff.total_seconds()/60) < int(f['interval'].value()):
            raise forms.ValidationError(_('Время работы зала меньше минимального времени на его посещение'))
        return title

    def clean(self):
        cleaned_data = super(HallItemForm, self).clean()
        for f in self.formset:
                if f is not self and \
                   self['title'].value().strip() and \
                   f['title'].value().strip().upper() == self['title'].value().strip().upper():
                    raise forms.ValidationError(_('Залы не могут иметь одинаковые названия'))
        return cleaned_data

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

class HallTimeTableForm(forms.Form):

    hall_date_from = forms.DateField(label=_("Дата"))
    halls = forms.MultipleChoiceField(label=_("Залы"),choices=())

class HallTimeForm(forms.Form):

    hall_date_from = forms.DateField(label=_("Дата"))
