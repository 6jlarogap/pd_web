import datetime

from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext as _

from users.models import Org
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
