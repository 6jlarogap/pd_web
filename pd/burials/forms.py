import datetime
import json
import random
import string
import re

from django import forms
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models, transaction, IntegrityError
from django.db.models.aggregates import Max
from django.db.models.deletion import ProtectedError
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.db.models.query_utils import Q

from burials.models import Cemetery, Area, Burial, Place, ExhumationRequest, BurialComment, BurialFiles, Grave, PlaceSize
from persons.models import AlivePerson
from geo.models import Location
from geo.forms import LocationForm
from orders.models import Order
from pd.forms import PartialFormMixin, ChildrenJSONMixin, LoggingFormMixin, CommentForm, StrippedStringsMixin, CustomUploadModelForm
from persons.forms import DeadPersonForm, DeathCertificateForm, AlivePersonForm, PersonIDForm
from persons.models import DeathCertificate, PersonID, IDDocumentType, OrderDeadPerson
from users.forms import BaseOrgForm
from users.models import Org, Profile, Dover, Role
from logs.models import write_log
from pd.models import SafeDeleteMixin
from pd.utils import rus_to_lat, reorder_form_fields
from pd.forms import AppOrgFormMixin

OPF_CHOICES = list(Org.OPF_CHOICES)[1:]

class BaseAreaFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseAreaFormset, self).__init__(*args, **kwargs)
        for f in self.forms:
            f.formset = self

    def clean(self):
        for df in getattr(self, 'deleted_forms', []):
            if df.instance and df.instance.burial_set.exists():
                msg = _('Участок %(name)s с <a href="/burials/?area=%(name)s" '
                        'target="_blank">захоронениями</a> удалить нельзя')
                raise forms.ValidationError(mark_safe(msg % dict(name=df.instance.name)))

class AreaItemForm(StrippedStringsMixin, forms.ModelForm):

    class Meta:
        model = Area
        fields = '__all__'

    def clean(self):
        StrippedStringsMixin.clean(self)
        for f in self.formset:
            if (f is not self) and f['name'].value().strip() == self['name'].value().strip():
                raise forms.ValidationError(_('Участки не могут иметь одинаковые названия'))
        return self.cleaned_data

AreaFormset = inlineformset_factory(Cemetery, Area, form=AreaItemForm, formset=BaseAreaFormset, can_delete=True)

EMPTY = (('', '--------'),)

class BurialSearchForm(forms.Form):
    """
    Форма поиска на главной странице.
    """

    PAGE_CHOICES = (
        (10, 10),
        (25, 25),
        (50, 50),
        (100, 100),
    )

    fio = forms.CharField(required=False, max_length=100, label=_("ФИО"))
    no_last_name = forms.BooleanField(required=False, initial=False, label=_("Неизв."))
    ident_number_search = forms.CharField(required=False, max_length=100, label=_("Идентификационный номер"))
    birth_date_from = forms.DateField(required=False, label=_("Дата рожд. с"))
    birth_date_to = forms.DateField(required=False, label=_("по"))
    death_date_from = forms.DateField(required=False, label=_("Дата смерти с"))
    death_date_to = forms.DateField(required=False, label=_("по"))
    burial_date_from = forms.DateField(required=False, label=_("Дата захор. с"))
    burial_date_to = forms.DateField(required=False, label=_("по"))
    account_number_from = forms.IntegerField(required=False, label=_("Рег. № с"))
    account_number_to = forms.IntegerField(required=False, label=_("по"))
    applicant_org = forms.CharField(required=False, max_length=60, label=_("Заявитель-ЮЛ"))
    applicant_person = forms.CharField(required=False, max_length=40, label=_("Заявитель-ФЛ"))
    loru_in_burials = forms.CharField(required=False, max_length=60, label=_("Посредник (ЛОРУ)"))
    responsible = forms.CharField(required=False, max_length=40, label=_("Ответственный"))
    operation = forms.ChoiceField(required=False, choices=EMPTY + Burial.BURIAL_TYPES, label=_("Вид захоронения"))
    burial_container = forms.TypedChoiceField(required=False, label=_("Тип захоронения"), choices=EMPTY + tuple(Burial.container_list_advanced()))
    cemeteries_editable = forms.BooleanField(label=_("Свои кладбища"), required=False, initial=True)
    cemetery = forms.CharField(required=False, label=_("Кладбище"))
    area = forms.CharField(required=False, label=_("Участок"))
    row = forms.CharField(required=False, label=_("Ряд"))
    place = forms.CharField(required=False, label=_("Участок/место в колумбарии"))
    no_responsible = forms.BooleanField(required=False, initial=False, label=_("Без отв."))
    is_inbook = forms.NullBooleanField(required=False, initial=None, label=_("Отметка об ответственном"))
    source = forms.TypedChoiceField(required=False, label=_("Источник"))
    status = forms.TypedChoiceField(required=False, label=_("Статус"))
    comment = forms.CharField(required=False, label=_("Комментарий"))
    file_comment = forms.CharField(required=False, label=_("Описание файла"))
    annulated = forms.BooleanField(required=False, initial=False, label=_("Аннулировано"))
    per_page = forms.ChoiceField(label=_("На странице"), choices=PAGE_CHOICES, initial=25, required=False)

    def __init__(self, *args, **kwargs):
        super(BurialSearchForm, self).__init__(*args, **kwargs)
        if not settings.DEADMAN_IDENT_NUMBER_ALLOW:
            del self.fields['ident_number_search']

        self.fields['source'].choices = EMPTY + Burial.SOURCE_TYPES
        self.fields['status'].choices = EMPTY + Burial.STATUS_CHOICES
        if not Org.objects.filter(type=Org.PROFILE_LORU).exists():
            del self.fields['loru_in_burials']

            for choice in self.fields['source'].choices:
                if choice[0] == Burial.SOURCE_FULL:
                    self.fields['source'].choices.remove(choice)
                    break

            extra_stata = []
            for status in self.fields['status'].choices:
                if status[0] not in (
                      '',
                      Burial.STATUS_DRAFT,
                      Burial.STATUS_APPROVED,
                      Burial.STATUS_CLOSED,
                      Burial.STATUS_EXHUMATED,
                   ):
                    extra_stata.append(status)
            for status in extra_stata:
                self.fields['status'].choices.remove(status)


class ResponsibleForm(AlivePersonForm):
    WHERE_FROM_PLACE = 'place'
    WHERE_FROM_APPLICANT = 'applicant'
    WHERE_NEW = 'new'
    WHERE_CHOICES = (
        (WHERE_FROM_PLACE, _('Существующий (из места)')),
        (WHERE_FROM_APPLICANT, _('Заявитель')),
        (WHERE_NEW, _('Новый')),
    )

    take_from = forms.ChoiceField(label=_("Где берем Ответственного?"), choices=WHERE_CHOICES,
                                  widget=forms.RadioSelect, required=True, initial=WHERE_NEW)
    place = forms.CharField(widget=forms.HiddenInput, required=False, )
    order = forms.CharField(widget=forms.HiddenInput, required=False, )
    login_phone_ = forms.DecimalField(label=AlivePerson._meta.get_field('login_phone').verbose_name,
                                      max_digits=AlivePerson._meta.get_field('login_phone').max_digits,
                                      decimal_places=AlivePerson._meta.get_field('login_phone').decimal_places,
                                      help_text=AlivePerson._meta.get_field('login_phone').help_text,
                                      validators=AlivePerson._meta.get_field('login_phone').validators,
                                      required=False)
    is_inbook_ = forms.BooleanField(label=AlivePerson._meta.get_field('is_inbook').verbose_name,
                                      help_text=AlivePerson._meta.get_field('is_inbook').help_text,
                                      required=False)

    def __init__(self, *args, **kwargs):
        self.place_ = None
        super(ResponsibleForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields['take_from']
            self.initial['login_phone_'] = self.instance.login_phone
        # funeral order
        elif self.instance.login_phone:
            self.initial['login_phone_'] = self.instance.login_phone
        else:
            self.fields = reorder_form_fields(self.fields, old_pos=-4, new_pos=0)
        if self.instance.pk:
            self.initial['is_inbook_'] = self.instance.is_inbook
        self.fields = reorder_form_fields(self.fields, old_pos=-1, new_pos=-3)

        self.initial.setdefault('take_from', self.WHERE_NEW)
        self.fields['login_phone_'].widget.input_type = 'text'

    def clean(self):
        if self.cleaned_data.get('take_from') == self.WHERE_FROM_PLACE:
            place_pk = self.cleaned_data.get('place')
            if not place_pk:
                raise forms.ValidationError(_('Нет места'))
            try:
                self.place_ = Place.objects.get(pk=place_pk)
            except Place.DoesNotExist:
                raise forms.ValidationError(_('Нет места'))
            if not self.place_.responsible:
                raise forms.ValidationError(_('Нет Ответственного у места'))
        return self.cleaned_data

    def save(self, *args, **kwargs):
        if 'login_phone_' in self.fields:
            self.instance.login_phone = self.cleaned_data['login_phone_']
            if self.cleaned_data.get('take_from') == self.WHERE_FROM_PLACE:
                if self.place_.responsible.login_phone != self.instance.login_phone:
                    self.place_.responsible.login_phone = self.instance.login_phone
                    self.place_.responsible.save()
                return self.place_.responsible
        if 'is_inbook_' in self.fields:
            self.instance.is_inbook = self.cleaned_data['is_inbook_']
        if self.instance.pk:
            return super(ResponsibleForm, self).save(*args, **kwargs)
        elif self.cleaned_data.get('take_from') == self.WHERE_FROM_PLACE:
            return self.place_.responsible
        else:
            return super(ResponsibleForm, self).save(*args, **kwargs)

    def is_valid_data(self):
        if self.is_valid():
            return self.cleaned_data.get('last_name') or self.cleaned_data.get('take_from') != self.WHERE_NEW
        else:
            return False

    def is_filled(self):
        # что-то заполнено в форме, когда предлагается заполнение
        # (новый ответственный или существующий)
        if self.is_valid():
            if self.fields.get('take_from') and self.cleaned_data.get('take_from') != self.WHERE_NEW:
                return False
            for f in ('last_name', 'first_name', 'middle_name', 'login_phone_', 'phones'):
                if self.cleaned_data.get(f):
                    return True
        return False

class BurialPublicListForm(forms.Form):
    """
    Форма поиска захоронений для ЛОРУ, не только среди своих заказов
    """

    PAGE_CHOICES = (
        (10, 10),
        (25, 25),
        (50, 50),
        (100, 100),
    )

    fio = forms.CharField(required=False, max_length=100, label=_("ФИО"))
    birth_date_from = forms.DateField(required=False, label=_("Дата рожд. с"))
    birth_date_to = forms.DateField(required=False, label=_("по"))
    death_date_from = forms.DateField(required=False, label=_("Дата смерти с"))
    death_date_to = forms.DateField(required=False, label=_("по"))
    burial_date_from = forms.DateField(required=False, label=_("Дата захор. с"))
    burial_date_to = forms.DateField(required=False, label=_("по"))
    account_number_from = forms.IntegerField(required=False, label=_("Рег. № с"))
    account_number_to = forms.IntegerField(required=False, label=_("по"))
    cemetery = forms.CharField(required=False, label=_("Кладбище"))
    area = forms.CharField(required=False, label=_("Участок"))
    row = forms.CharField(required=False, label=_("Ряд"))
    place = forms.CharField(required=False, label=_("Место"))
    annulated = forms.BooleanField(required=False, initial=False, label=_("Аннулировано"))
    per_page = forms.ChoiceField(label=_("На странице"), choices=PAGE_CHOICES, initial=25, required=False)

    # Так как ЛОРУ сейчас ищет только среди своих захоронений
    # - обязательность ФИО и кладбища не имеет смысла!
    # Проверка лишь закомментирована, а не удалена из кода,
    # чтоб не забыть про аннулированные
    #
    #def clean(self):
        #cd = self.cleaned_data
        #if not cd['annulated'] and (not cd['fio'] or not cd['cemetery']):
            #raise forms.ValidationError(_(u'Обязательные поля: ФИО и Кладбище'))
        #return cd

class BurialForm(PartialFormMixin, ChildrenJSONMixin, LoggingFormMixin, SafeDeleteMixin, StrippedStringsMixin, AppOrgFormMixin, forms.ModelForm):
    COFFIN = 'coffin'
    URN = 'urn'

    BURIAL_TYPES = (
        (Burial.BURIAL_NEW, _('Новое захоронение (новое место, новая могила)')),
        (Burial.BURIAL_ADD, _('Подзахоронение (существующее место, новая могила)')),
        (Burial.BURIAL_OVER, _('Захоронение в существующую (существующее место, существующая могила)')),
    )

    burial_container = forms.ChoiceField(label=_("Тип захоронения"), choices=Burial.BURIAL_CONTAINERS, widget=forms.RadioSelect,  required=False)
    burial_type = forms.ChoiceField(label=_("Вид захоронения"), choices=BURIAL_TYPES, widget=forms.RadioSelect,  required=False)
    opf = forms.ChoiceField(label='', choices=OPF_CHOICES, widget=forms.RadioSelect)
    loru = forms.CharField(required=False, label=_('Посредник'))

    class Meta:
        model = Burial
        exclude = ('place', 'deadman', 'responsible', 'applicant', 'annulated',
                  )

    def __init__(self, request, *args, **kwargs):
        super(BurialForm, self).__init__(*args, **kwargs)
        self.request = request
        self.init_app_org_label()
        self.fields['cemetery'].queryset = Cemetery.objects.filter(
            Q(ugh__isnull=True) |
            Q(ugh__loru_list__loru=self.request.user.profile.org) |
                Q(ugh=self.request.user.profile.org) & \
                Q(pk__in=[c.pk for c in Cemetery.editable_ugh_cemeteries(request.user)])
        ).distinct()
        if self.instance.cemetery and self.instance.cemetery.time_slots:
            choices = [('', '----------')] + self.instance.cemetery.get_time_choices(
                date=self.instance.plan_date,
                request=self.request,
            )
            self.fields['plan_time'].widget = forms.Select(choices=choices)
        if self.instance.plan_time:
            self.initial['plan_time'] = self.instance.plan_time.strftime('%H:%M')

        if not self.instance.plan_date and self.instance.status not in \
                        (Burial.STATUS_CLOSED, Burial.STATUS_EXHUMATED,):
            date_diff = settings.BURIAL_PLAN_DATE_DAYS_FROM_TODAY > 0 and settings.BURIAL_PLAN_DATE_DAYS_FROM_TODAY or 0
            if date_diff and datetime.date.today().weekday() == 5 and request.user.profile.is_ugh():
                date_diff += 1 # Saturday
            self.initial['plan_date'] = datetime.date.today() + datetime.timedelta(date_diff)

        self.archived_burial = self.instance.pk and self.instance.is_archive() or \
                              self.request.GET.get('archive') or \
                              self.request.POST.get('archive')

        self.order = None
        order_pk = self.request.GET.get('order') or self.request.POST.get('order')
        if self.request.user.profile.is_loru() and order_pk:
            try:
                self.order = Order.objects.get(pk=order_pk, loru=self.request.user.profile.org)
            except Order.DoesNotExist:
                pass

        self.funeral_order = self.funeral_deadman_address = self.funeral_applicant_address = None
        funeral_order_pk = self.request.GET.get('funeral_order') or self.request.POST.get('funeral_order')
        if self.request.user.profile.is_ugh() and funeral_order_pk and not self.instance.pk:
            try:
                funeral_order = Order.objects.get(pk=funeral_order_pk)
                self.funeral_order = funeral_order
                if self.instance.deadman:
                    try:
                        orderdeadperson = OrderDeadPerson.objects.get(order=funeral_order)
                        self.funeral_deadman_address = orderdeadperson and \
                                                        orderdeadperson.address and \
                                                        orderdeadperson.address.addr_str
                    except OrderDeadPerson.DoesNotExist:
                        pass
                if self.instance.applicant:
                    self.funeral_applicant_address = funeral_order.applicant and \
                                                    funeral_order.applicant.address and \
                                                    funeral_order.applicant.address.addr_str
            except Order.DoesNotExist:
                pass

        # Отсутствие выбора будет в выпадающем списке не "---", а ""
        self.fields['applicant_organization'].empty_label = ''
        
        places_count = 1
        if self.instance.place_number and self.instance.get_place():
            places_count = self.instance.get_place().get_graves_count()
        elif self.instance.area:
            places_count = self.instance.area.places_count
        # - Вдруг уменьшат параметры участка или места так, что номер могилы в захоронении
        #   окажется больше числа могил в участке для нового места
        # - Вдруг вообще не укажут кладбище или участок, но в записи захоронения
        #   уже не 1-е место. Нельзя его заменять на 1-е.
        post_places_count = request.POST and request.POST.get('grave_number') or 1
        post_places_count = int(post_places_count)
        places_count = max(places_count, self.instance.grave_number or 1, post_places_count)
        grave_choices = [(i,i) for i in range(1, places_count+1)]
        self.fields['grave_number'].widget = forms.Select(choices=grave_choices)

        max_grave_number = self.fields['cemetery'].queryset.aggregate(m=Max('area__places_count'))['m'] or 1
        max_grave_choices = [(i,i) for i in range(1, max_grave_number+1)]
        self.fields['desired_graves_count'].widget = forms.Select(choices=max_grave_choices)
        if self.request.user.profile.is_loru():
            self.fields['desired_graves_count'].label = _('Желаемое число могил в новом месте')
        
        self.fields['applicant_organization'].queryset = Org.objects.all()
        self.fields['applicant_organization'].inactive_queryset = \
            Org.objects.filter(Q(profile=None) | ~Q(profile__user__is_active=True)).distinct()
        self.fields['agent'].queryset = Profile.objects.filter(is_agent=True).select_related('user')
        self.fields['dover'].queryset = self.fields['dover'].queryset.select_related('agent', 'agent__user')

        self.fields = reorder_form_fields(self.fields, old_pos=-1, new_pos='applicant_organization')

        if self.instance.can_personal_data(self.request):
            if self.instance.pk:
                if self.instance.applicant:
                    self.initial['opf'] = Org.OPF_PERSON
                elif self.instance.applicant_organization:
                    self.initial['opf'] = Org.OPF_ORG
                else:
                    self.initial['opf'] = self.request.user.profile.org.opf_burial
            else:
                if self.funeral_order:
                    self.initial['opf'] = Org.OPF_PERSON
                else:
                    self.initial['opf'] = self.request.user.profile.org.opf_burial
        else:
            self.initial['opf'] = Org.OPF_ORG

        if self.request.user.profile.is_ugh() and \
           (self.archived_burial or self.instance.is_transferred()):
            del self.fields['plan_date']
            del self.fields['plan_time']
        elif not self.instance.is_finished():
            del self.fields['fact_date']
            if self.request.user.profile.org.numbers_algo != Org.NUM_MANUAL:
                if self.instance.account_number:
                    self.fields['account_number'].widget.attrs.update({'readonly':'True'})
                else:
                    del self.fields['account_number']

        if 'account_number' in self.fields and \
           self.request.user.profile.org.numbers_algo == Org.NUM_EMPTY and \
           not self.instance.account_number:
            del self.fields['account_number']
            
        if not self.request.user.profile.is_ugh():
            del self.fields['place_length']
            del self.fields['place_width']

        if not self.instance.pk:
            self.initial['burial_container'] = Burial.CONTAINER_COFFIN
            self.initial['burial_type'] = Burial.BURIAL_NEW

            place_id = self.request.GET.get('place_id')
            if place_id:
                # Вызов из карточки места
                self.initial['burial_type'] = Burial.BURIAL_ADD
                try:
                    place_ = Place.objects.get(pk=place_id)
                    if place_.is_columbarium():
                        self.initial['burial_type'] = Burial.BURIAL_OVER
                        self.initial['burial_container'] = Burial.CONTAINER_URN
                except Place.DoesNotExist:
                    pass
            else:
                if self.request.user.profile.cemetery and not self.initial.get('cemetery'):
                    self.initial['cemetery'] = self.request.user.profile.cemetery
                    if self.initial['cemetery'].is_columbarium():
                        self.initial['burial_container'] = Burial.CONTAINER_URN

                if self.request.user.profile.area and not self.initial.get('area'):
                    self.initial['area'] = self.request.user.profile.area
                    if self.initial['area'].is_columbarium():
                        self.initial['burial_container'] = Burial.CONTAINER_URN
                        self.initial['desired_graves_count'] = 1
                    else:
                        self.initial['desired_graves_count'] = self.initial['area'].places_count or 1

                if self.request.user.profile.is_ugh():
                    if not self.initial.get('area') or not self.initial['area'].is_columbarium():
                        desired_graves_count = self.initial.get('desired_graves_count') or 1
                        try:
                            place_size = PlaceSize.objects.get(org=self.request.user.profile.org,
                                                            graves_count=desired_graves_count)
                            self.initial['place_length'] = place_size.place_length
                            self.initial['place_width'] = place_size.place_width
                        except PlaceSize.DoesNotExist:
                            pass

        if self.request.user.profile.is_loru() or \
           self.archived_burial or \
           self.instance.pk and not self.instance.is_ugh_only():
            del self.fields['loru']
            del self.fields['loru_agent_director']
            del self.fields['loru_agent']
            del self.fields['loru_dover']
        else:
            self.initial['loru'] = self.instance.pk and self.instance.loru and self.instance.loru.name or ''

        if self.instance.is_finished() and self.instance.place:
            self.initial.update(
                cemetery=self.instance.place.cemetery,
                area=self.instance.place.area,
                row=self.instance.place.row,
                place_number=self.instance.place.place,
            )

        self.fields['area'].queryset = self.fields['area'].queryset.select_related('purpose')

        self.forms = self.construct_forms()

    def get_responsible_info(self, place):
        """
        Получить инфо для записи в журнал об ответственном за место
        """
        result = dict()
        for k in (
            ('fio', _('ФИО')),
            ('address', _('Адрес')),
            ('phones', _('Телефон(ы)')),
            ('login_phone', AlivePerson._meta.get_field('login_phone').verbose_name),
            ):
            result[k[0]] = dict(title=k[1], value='')

        if place and place.pk and place.responsible:
            result['fio']['value'] = place.responsible.full_human_name()
            result['address']['value'] = place.responsible.address and \
                                            place.responsible.address.address_(empty=True) or ''
            result['phones']['value'] = place.responsible.phones or ''
            result['login_phone']['value'] = str(place.responsible.login_phone or '')
        return result

    def compare_responsible_info(self, request, old_responsible_info, burial, is_new_burial):
        """
        Сравнить инфо об ответственном после закрытия зх. Изменения в журнал
        """
        place = burial and burial.place or None
        if place:
            responsible = place.responsible
            new_responsible_info = self.get_responsible_info(place)
            changes = []
            for k in old_responsible_info:
                if new_responsible_info[k]['value'] != old_responsible_info[k]['value']:
                    changes.append("%s: '%s' -> '%s'" % (
                        new_responsible_info[k]['title'],
                        old_responsible_info[k]['value'],
                        new_responsible_info[k]['value'],
                    ))
            if changes:
                if is_new_burial:
                    changes_title = _('Ответственный изменен при создании захоронения\n%s')
                else:
                    changes_title = _('Ответственный изменен при правке захоронения\n%s')
                changes_str = changes_title % '\n'.join(changes)
                write_log(request, place, changes_str)
                if is_new_burial:
                    write_log(self.request, burial, changes_str)

    def construct_forms(self):
        data = self.data or None
        deadman = self.instance and self.instance.deadman
        self.old_place = self.instance and self.instance.get_place()
        self.old_responsible_info = dict()
        if self.request.user.profile.is_ugh():
            self.old_responsible_info = self.get_responsible_info(self.old_place)

        if settings.DEADMAN_IDENT_NUMBER_ALLOW:
            self.deadman_old_last_name = self.deadman_old_first_name = self.deadman_old_ident_number = ''
            if self.instance:
                if self.instance.deadman:
                    self.deadman_old_last_name = self.instance.deadman.last_name
                    self.deadman_old_first_name = self.instance.deadman.first_name
                    self.deadman_old_ident_number = self.instance.deadman.ident_number
                self.old_grave_number = self.instance.grave_number or 1

        self.deadman_form = DeadPersonForm(request=self.request, data=data, prefix='deadman', instance=deadman)
        if self.funeral_deadman_address:
            deadman_addr = Location(addr_str=self.funeral_deadman_address)
        else:
            deadman_addr = deadman and deadman.address
        self.deadman_address_form = LocationForm(data=data, prefix='deadman-address', instance=deadman_addr)
        self.bfiles_form = BurialFilesForm(data=data, prefix='bfiles', files=self.request.FILES)
        try:
            dc = self.instance and self.instance.deadman and self.instance.deadman.deathcertificate
        except DeathCertificate.DoesNotExist:
            dc = None
        if not dc and deadman:
            dc = DeathCertificate(person=deadman)
        self.dc_form = DeathCertificateForm(self.request, data=data, prefix='deadman-dc', instance=dc)

        responsible = self.instance and self.instance.get_responsible()
        self.responsible_form = ResponsibleForm(data=data, prefix='responsible', instance=responsible)
        if 'login_phone_' in self.responsible_form.fields and \
           self.instance and (self.instance.is_closed() or self.instance.is_exhumated()):
            self.responsible_form.fields['login_phone_'].widget.attrs.update({'readonly':'True'})
        if self.funeral_applicant_address:
            resp_addr = Location(addr_str=self.funeral_applicant_address)
        else:
            resp_addr = responsible and responsible.address
        self.responsible_address_form = LocationForm(data=data, prefix='responsible-address', instance=resp_addr)
        applicant = self.instance and self.instance.applicant
        applicant_form_initial = {}
        applicant_address_form_initial = {}
        applicant_id_form_initial = {}
        if not self.instance.pk and self.order and self.order.applicant and self.instance.can_personal_data(self.request):
            self.initial['opf'] = Org.OPF_PERSON
            for f in list(AlivePersonForm.base_fields.keys()):
                applicant_form_initial[f] = getattr(self.order.applicant, f)
            cust_address = self.order.applicant.address
            if cust_address:
                if cust_address.country:
                    applicant_address_form_initial['country_name'] = cust_address.country.name
                if cust_address.region:
                    applicant_address_form_initial['region_name'] = cust_address.region.name
                if cust_address.city:
                    applicant_address_form_initial['city_name'] = cust_address.city.name
                if cust_address.street:
                    applicant_address_form_initial['street_name'] = cust_address.street.name
                for f in ('post_index', 'house', 'block', 'building', 'flat', 'info', ):
                    applicant_address_form_initial[f] = getattr(cust_address, f)
            try:
                cust_personid = self.order.applicant.personid
            except PersonID.DoesNotExist:
                cust_personid = None
            if cust_personid:
                for f in list(PersonIDForm.base_fields.keys()):
                    try:
                        applicant_id_form_initial[f] = getattr(cust_personid, f)
                    except AttributeError:
                        # Мало ли какие поля будут в форме в добавление к тем,
                        # что из модели, на которой форма основана:
                        pass
        applicant_id_form_initial['flag_no_applicant_doc_required'] = True
        if self.instance.pk:
            if self.instance.applicant and \
               self.instance.can_personal_data(self.request):
                applicant_id_form_initial['flag_no_applicant_doc_required'] = \
                    self.instance.flag_no_applicant_doc_required
            elif self.instance.is_archive():
                applicant_id_form_initial['flag_no_applicant_doc_required'] = False

        self.applicant_form = AlivePersonForm(data=data, prefix='applicant',
                                              instance=applicant,
                                              initial=applicant_form_initial,
                                             )
        if self.funeral_applicant_address:
            applicant_addr = Location(addr_str=self.funeral_applicant_address)
        else:
            applicant_addr = applicant and applicant.address
        self.applicant_address_form =  LocationForm(data=data, prefix='applicant-address',
                                                    instance=applicant_addr,
                                                    initial=applicant_address_form_initial,
                                                   )
        try:
            applicant_id = self.instance and self.instance.applicant and self.instance.applicant.personid
        except PersonID.DoesNotExist:
            applicant_id = None
        self.applicant_id_form = PersonIDForm(data=data, prefix='applicant-pid',
                                              instance=applicant_id,
                                              initial=applicant_id_form_initial
                                             )

        self.comment_form = CommentForm(data=data, prefix='comment')
        
        forms = [self.deadman_form, self.deadman_address_form, self.dc_form,
                self.responsible_form, self.responsible_address_form,
                self.applicant_form, self.applicant_address_form, self.applicant_id_form,
                self.bfiles_form, self.comment_form, ]
        return forms

    def is_valid(self):
        return self.opf_valid(BurialForm)

    def clean_plan_time(self):
        return self.cleaned_data['plan_time'] or None

    def clean_loru(self):
        loru = None
        loru_str = self.cleaned_data.get('loru').strip()
        if loru_str:
            try:
                loru = Org.objects.filter(name=loru_str, type=Org.PROFILE_LORU)[0]
            except IndexError:
                raise forms.ValidationError(_('Нет такого ЛОРУ'))
        return loru

    def clean(self):
        
        StrippedStringsMixin.clean(self)
        
        # Все эти ошибки невозможны при правильной работе javascript- проверок,
        # но пусть будет дополнительная страховка
        #
        if self.cleaned_data.get('cemetery') and self.cleaned_data.get('area'):
            if self.cleaned_data['cemetery'] != self.cleaned_data['area'].cemetery:
                raise forms.ValidationError(_('Участок не от этого кладбища'))

        if self.responsible_form.is_valid():
            if self.responsible_form.cleaned_data.get('take_from') == ResponsibleForm.WHERE_FROM_APPLICANT:
                if self.cleaned_data.get('opf') != Org.OPF_PERSON:
                    raise forms.ValidationError(_("Невозможно указать Заявителя - Ответственного. Заявитель не ФЛ."))

        return self.cleaned_data

    def cemetery_placing_json(self):
        parents = {}
        if self.fields.get('cemetery'):
            for c in self.fields['cemetery'].queryset:
                parents[c.pk] = c.places_algo
        return mark_safe(json.dumps(parents))

    def get_prefix(self, form):
        prefix = ''
        m_deadman = _("Усопший")
        if form is self.deadman_form:
            prefix = m_deadman + " "
        if form is self.deadman_address_form:
            prefix = m_deadman + ", " + str(_("адрес")) + " "
        if form is self.dc_form:
            prefix = m_deadman + ", " + str(_("СоС")) + " "
        if form in [self.responsible_form, self.responsible_address_form]:
            prefix = _("Ответственный ")
        if form in [self.applicant_form, self.applicant_address_form, self.applicant_id_form]:
            prefix = _("Заявитель ")
        return prefix

    @transaction.atomic
    def save(self, commit=True, **kwargs):
        request = self.request
        self.collect_log_data()

        self.instance = super(BurialForm, self).save(commit=False)
        is_new_burial = not bool(self.instance.pk)

        # Изменились ли поля, которые существенны в регистре
        #
        update_for_register = False

        if self.cleaned_data.get('agent_director'):
            self.instance.agent = None
            self.instance.dover = None

        if self.cleaned_data.get('loru_agent_director'):
            self.instance.loru_agent = None
            self.instance.loru_dover = None
        if 'loru' in self.fields and not self.cleaned_data.get('loru'):
            self.instance.loru_agent_director = False
            self.instance.loru_agent = None
            self.instance.loru_dover = None

        self.instance.changed_by = request.user

        if not self.instance.ugh:
            if request.user.profile.is_ugh():
                self.instance.ugh = request.user.profile.org
            elif self.instance.cemetery:
                self.instance.ugh = self.instance.cemetery.ugh

        if not self.instance.loru and request.user.profile.is_loru():
            self.instance.loru = request.user.profile.org

        if is_new_burial:
            if self.request.user.profile.is_loru():
                self.instance.source_type = Burial.SOURCE_FULL
            elif self.request.user.profile.is_ugh():
                if self.archived_burial:
                    self.instance.source_type = Burial.SOURCE_ARCHIVE
                else:
                    self.instance.source_type = Burial.SOURCE_UGH

        if self.deadman_form.is_valid() and self.instance.burial_container != Burial.CONTAINER_BIO:

            deadman = self.deadman_form.save(commit=False)
            if settings.DEADMAN_IDENT_NUMBER_ALLOW and \
               self.deadman_form.cleaned_data.get("ident_number"):
                deadman.ident_number = rus_to_lat(deadman.ident_number.strip().upper())

            if self.deadman_address_form.is_valid_data():
                # Хотя бы одно поле из адреса заполнено
                deadman.address = self.deadman_address_form.save()
            else:
                self.safe_delete('address', deadman)
            deadman.save()

            if self.dc_form.is_valid():
                self.dc_form.save(deadPerson=deadman)
            self.instance.deadman = deadman
        else:
            self.safe_delete('deadman', self.instance)

        if self.cleaned_data.get('opf') == Org.OPF_PERSON:
            self.instance.applicant_organization = None
            self.instance.agent_director = False
            self.instance.agent = None
            self.instance.dover = None
            if self.applicant_form.is_valid():
                old_address = self.applicant_address_form.instance
                applicant = self.applicant_form.save(commit=False)
                if old_address and old_address.pk:
                    applicant_address_valid = self.applicant_address_form.is_valid()
                else:
                    applicant_address_valid = self.applicant_address_form.is_valid_data()
                if applicant_address_valid:
                    applicant.address = self.applicant_address_form.save()
                applicant.save()
                if not applicant.address and old_address and old_address.pk:
                    try:
                        old_address.delete()
                    except ProtectedError:
                        pass
                self.instance.applicant = applicant
                if self.applicant_id_form.is_valid():
                    self.instance.flag_no_applicant_doc_required = \
                        self.applicant_id_form.cleaned_data.get('flag_no_applicant_doc_required')
                if self.applicant_id_form.is_valid_data():
                    pid = self.applicant_id_form.save(commit=False)
                    pid.person = applicant
                    pid.save()
        else:
            self.safe_delete('applicant', self.instance)
            self.instance.flag_no_applicant_doc_required = False

        remove_responsible = False
        if self.responsible_form.cleaned_data.get('take_from') == ResponsibleForm.WHERE_FROM_PLACE:
            self.instance.responsible = self.responsible_form.save()
        elif self.responsible_form.cleaned_data.get('take_from') == ResponsibleForm.WHERE_FROM_APPLICANT and \
           self.instance.applicant:
            # Заявитель-ФЛ при этом формируется новый и без login_phone, но это может измениться
            applicant_login_phone = self.instance.applicant.login_phone
            self.instance.applicant.login_phone = self.responsible_form.cleaned_data.get('login_phone_')
            self.instance.responsible = self.instance.applicant.deep_copy()
            self.instance.applicant.login_phone = applicant_login_phone
        elif self.responsible_form.is_valid():
            old_address = self.responsible_address_form.instance
            if old_address and old_address.pk:
                responsible_address_valid = self.responsible_address_form.is_valid()
            else:
                responsible_address_valid = self.responsible_address_form.is_valid_data()
            if self.responsible_form.cleaned_data.get('last_name').strip() or \
               self.responsible_form.cleaned_data.get('first_name').strip() or \
               self.responsible_form.cleaned_data.get('middle_name').strip() or \
               self.responsible_form.cleaned_data.get('phones', '').strip() or \
               self.responsible_form.cleaned_data.get('login_phone_') or \
               responsible_address_valid:
                responsible = self.responsible_form.save(commit=False)
                if responsible_address_valid:
                    responsible.address = self.responsible_address_form.save()
                responsible.save()
                if not responsible.address and old_address and old_address.pk:
                    try:
                        old_address.delete()
                    except ProtectedError:
                        pass
                self.instance.responsible = responsible
            else:
                remove_responsible = True
        else:
            remove_responsible = True
        if remove_responsible:
            self.safe_delete('responsible', self.instance)

        if self.instance.is_closed() and self.old_place:
            if self.cleaned_data['cemetery'] != self.old_place.cemetery or \
               self.cleaned_data['area'] != self.old_place.area or \
               self.cleaned_data['row'] != self.old_place.row or \
               self.cleaned_data['place_number'] != self.old_place.place:
                place, created = Place.objects.get_or_create(cemetery=self.cleaned_data['cemetery'],
                                                            area=self.cleaned_data['area'],
                                                            row=self.cleaned_data['row'],
                                                            place=self.cleaned_data['place_number'],
                                            defaults = { 'place_length': self.cleaned_data['place_length'],
                                                        'place_width': self.cleaned_data['place_width'],
                                                        }
                                )
                self.instance.place=place
                if created:
                    desired_graves_count = self.cleaned_data.get('desired_graves_count') or 1
                    grave_number = self.cleaned_data.get('grave_number') or 1
                    if self.cleaned_data['area'].is_columbarium():
                        desired_graves_count = 1
                        grave_number = 1
                    self.grave = place.create_graves(max(desired_graves_count,
                                                        grave_number,
                                                        ),
                                                    grave_number,
                    )
                else:
                    # Пока не привязываем здесь могилу к захоронению, если место существует.
                    # Это будет сделано ниже в self.instance.close(....)

                    # В старое место может быть записан заданный в форме
                    # ответственный
                    #
                    self.old_responsible_info = self.get_responsible_info(place)

                if settings.DEADMAN_IDENT_NUMBER_ALLOW:
                    update_for_register = True
            if settings.DEADMAN_IDENT_NUMBER_ALLOW and \
               not update_for_register and \
               not self.cleaned_data['area'].is_columbarium() and \
               self.old_grave_number != self.cleaned_data['grave_number']:
                update_for_register = True

        if settings.DEADMAN_IDENT_NUMBER_ALLOW and \
           not update_for_register and \
           self.instance.is_closed() and \
           self.instance.deadman and \
           (
                self.instance.deadman.last_name != self.deadman_old_last_name or \
                self.instance.deadman.first_name != self.deadman_old_first_name or \
                self.instance.deadman.ident_number != self.deadman_old_ident_number \
           ):
           update_for_register = True

        if self.cleaned_data.get('area') and self.cleaned_data['area'].is_columbarium():
            self.instance.grave_number = 1
            self.desired_graves_count = 1

        self.instance.save()

        if self.comment_form.is_valid():
            comment = self.comment_form.cleaned_data.get('comment', '').strip()
            if comment:
                write_log(request, self.instance, _('Комментарий: %s') % comment)
                BurialComment.objects.create(
                    creator=request.user,
                    burial=self.instance,
                    comment=comment,
                )

        if self.order:
            self.order.burial = self.instance
            self.order.save()

        if self.funeral_order:
            self.funeral_order.burial = self.instance
            self.funeral_order.save()
            write_log(self.request, self.instance, _('Захоронение прикреплено к заказу %s') % self.funeral_order.pk)
            write_log(self.request, self.funeral_order, _('Заказ: прикреплено захоронение %s') % self.instance.pk)

        if self.bfiles_form.is_valid() and self.request.FILES.get('bfiles-bfile'):
            saved_file = self.bfiles_form.save(burial=self.instance, user=self.request.user)
            if is_new_burial:
                write_log(request, self.instance,
                        _('Добавлен файл'), "%s, %s" % (saved_file.comment, saved_file.original_name,)
                )

        if self.instance.is_closed():
            self.instance.close(
                request=self.request,
                old_place=self.old_place,
                update_for_register=update_for_register,
            )
            self.compare_responsible_info(
                request=self.request,
                old_responsible_info=self.old_responsible_info,
                burial=self.instance,
                is_new_burial=False,
            )

        self.put_log_data()

        order_parm = '?order=%s' % self.order.pk if self.order else ''
        url = 'view_burial' if request.user.profile.is_ugh() else 'edit_burial'
        msg = _("<a href='%(burial_url)s'>Захоронение %(pk)s</a> сохранено") % dict(
            burial_url=reverse(url, args=[self.instance.pk]) + order_parm,
            pk=self.instance.pk,
        )
        messages.success(self.request, msg)

        return self.instance

class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        exclude = ['responsible', ]

class BurialFilesForm(CustomUploadModelForm):
    class Meta:
        model = BurialFiles
        exclude = ['burial', ]

    # MAX_UPLOAD_SIZE_MB = 2, так установлено в CustomUploadModelForm,
    # это устраивает, не будем менять в __init__()

    def clean_comment(self):
        self.cleaned_data['comment'] = self.cleaned_data['comment'].strip()
        return self.cleaned_data['comment']

    def clean(self):
        cleaned_data = super(BurialFilesForm, self).clean()
        comment = cleaned_data.get('comment')
        bfile = cleaned_data.get('bfile')
        if comment and not bfile or not comment and bfile:
            raise forms.ValidationError(_('Надо задавать и файл, и описание; или ни файл, ни описание'))
        return cleaned_data

    def save(self, burial=None, user=None, commit=True, *args, **kwargs):
        burial_file_rec = super(BurialFilesForm, self).save(commit=False, *args, **kwargs)
        burial_file_rec.burial = burial
        burial_file_rec.creator = user
        if commit:
            burial_file_rec.save()
        return burial_file_rec

class BurialfileCommentEditForm(forms.ModelForm):
    class Meta:
        model = BurialFiles
        fields = ['comment', ]

    def clean_comment(self):
        self.cleaned_data['comment'] = self.cleaned_data['comment'].strip()
        if not self.cleaned_data['comment']:
            raise forms.ValidationError(_('Описание не может быть пустым'))
        return self.cleaned_data['comment']

class BurialCommitForm(BurialForm):
    def __init__(self, *args, **kwargs):
        super(BurialCommitForm, self).__init__(*args, **kwargs)

        self.mock_data()
        self.forms = self.construct_forms()

        self.setup_required()

    def form_to_data(self, form):
        data = {}
        for f in form.fields:
            k = form.prefix and '%s-%s' % (form.prefix, f) or f
            v = form.initial.get(f) or None
            if isinstance(v, models.Model):
                v = v.pk
            data.update({k:v})
        return data

    def setup_required(self):
        for f in self.fields:
            if f == 'cemetery':
                self.fields[f].required = True
            elif f =='plan_date':
                self.fields[f].required = \
                    self.instance.status not in \
                        (Burial.STATUS_CLOSED, Burial.STATUS_EXHUMATED,)
            elif f == 'plan_time':
                self.fields[f].required = \
                    (self.instance.status not in \
                        (Burial.STATUS_CLOSED, Burial.STATUS_EXHUMATED,)) and \
                    self.request.user.profile.org.plan_time_required
        if self.request.user.profile.is_ugh():
            self.fields['area'].required = True

        if self.data.get('cemetery'):
            cemetery = self.data.get('cemetery')
            if not isinstance(cemetery, Cemetery):
                cemetery = Cemetery.objects.get(pk=cemetery)
        else:
            cemetery = self.instance.cemetery or None

        if self.fields.get('fact_date'):
            if self.instance.is_transferred():
                self.fields['fact_date'].required = False
            elif self.archived_burial and \
               cemetery and not cemetery.archive_burial_fact_date_required:
                self.fields['fact_date'].required = False
            else:
                # Во всех остальных случаях, когда на форме есть факт. дата,
                # например в закрытом зх:
                self.fields['fact_date'].required = True

        if self.instance.is_finished():
            if cemetery and cemetery.places_algo == Cemetery.PLACE_MANUAL:
                self.fields['place_number'].required = True

        if self.instance.is_ugh() and self.instance.applicant_organization:
            if not self.instance.is_archive():
                for f in ['applicant_organization', 'agent', 'dover']:
                    self.fields[f].required = True

            if self.instance.agent_director or self.data.get('agent_director'):
                self.fields['dover'].required = False
                self.fields['agent'].required = False

        self.setup_required_deadman()
        self.setup_required_deadman_address()
        self.setup_required_deadman_dc()
        self.setup_required_responsible()
        self.setup_required_responsible_address()
        self.setup_required_applicant()
        self.setup_required_applicant_address()
        self.setup_required_applicant_id()

    def setup_required_deadman(self):
        pass

    def setup_required_deadman_address(self):
        pass

    def setup_required_deadman_dc(self):
        pass

    def setup_required_responsible(self):
        pass

    def setup_required_responsible_address(self):
        pass

    def setup_required_applicant(self):
        pass

    def setup_required_applicant_address(self):
        pass

    def setup_required_applicant_id(self):
        if self.data.get('opf') == Org.OPF_PERSON and not self.data.get('applicant-pid-flag_no_applicant_doc_required') and \
           not self.archived_burial:
            for f in self.applicant_id_form.fields:
                if f in ['id_type', 'series', 'number',]:
                    self.applicant_id_form.fields[f].required = True

    def clean(self):

        StrippedStringsMixin.clean(self)

        cemetery = self.cleaned_data.get('cemetery')
        if self.request.user.profile.is_ugh():
            can_personal_data = self.request.user.profile.org.can_personal_data()
        else:
            can_personal_data = self.instance.can_personal_data(self.request) if self.instance.pk else \
                                cemetery and cemetery.ugh and cemetery.ugh.can_personal_data()

        if not self.archived_burial and not self.instance.is_transferred():
            if can_personal_data and not self.cleaned_data.get('applicant_organization') and not self.applicant_form.is_valid_data():
                raise forms.ValidationError(_("Нужно указать либо Заявителя-ЮЛ, либо Заявителя-ФЛ"))

            if can_personal_data and self.cleaned_data.get('opf') == Org.OPF_PERSON:
                if not self.applicant_form.is_valid_data():
                    raise forms.ValidationError(_("Если выбран заявитель-ФЛ, то надо его (ее) указать"))

            if self.cleaned_data.get('opf') == Org.OPF_ORG:
                applicant_organization = self.cleaned_data.get('applicant_organization')
                if not applicant_organization and can_personal_data:
                    raise forms.ValidationError(_("Если выбран заявитель-ЮЛ, то надо его указать"))
                if applicant_organization and not self.cleaned_data.get('agent_director'):
                    if not self.cleaned_data.get('agent') or not self.cleaned_data.get('dover'):
                        msg = _("Нужно указать Агента и Доверенность или указать, что Агент - Директор")
                        raise forms.ValidationError(msg)
                    if not self.instance.is_closed():
                        if self.cleaned_data.get('dover'):
                            dover_begin_date = self.cleaned_data.get('dover').begin
                            dover_end_date = self.cleaned_data.get('dover').end
                            today = datetime.datetime.today()
                            if dover_begin_date > today.date():
                                msg = _("Дата выдачи доверенности не может быть позже текущей даты")
                                raise forms.ValidationError(msg)
                            if dover_end_date < today.date() :
                                msg = _("Срок действия доверенности не может быть меньше текущей даты")
                                raise forms.ValidationError(msg)

        if self.cleaned_data.get('loru'):
            if not self.cleaned_data.get('loru_agent_director'):
                if not self.cleaned_data.get('loru_agent') and not self.cleaned_data.get('loru_dover'):
                    msg = _("Посредник: нужно указать Агента и Доверенность или указать, что Агент - Директор")
                    raise forms.ValidationError(msg)
                if not self.instance.is_closed():
                    dover_begin_date = self.cleaned_data.get('loru_dover').begin
                    dover_end_date = self.cleaned_data.get('loru_dover').end
                    today = datetime.datetime.today()
                    if dover_begin_date > today.date():
                        msg = _("Посредник: дата выдачи доверенности не может быть позже текущей даты")
                        raise forms.ValidationError(msg)
                    if dover_end_date < today.date() :
                        msg = _("Посредник: срок действия доверенности не может быть меньше текущей даты")
                        raise forms.ValidationError(msg)

        is_ugh = False
        if self.instance and self.instance.is_ugh():
            is_ugh = True
        if (not self.instance or not self.instance.pk) and self.request.user.profile.is_ugh():
            is_ugh = True

        msg_complete = _('закрывать')
        if is_ugh and self.request.POST.get('approve'):
            msg_complete = _('согласовывать')
        elif self.request.user.profile.is_loru() and self.request.POST.get('ready'):
            msg_complete = _('отправлять на согласование')

        area = self.cleaned_data.get('area')
        row = self.cleaned_data.get('row')
        place_number = self.cleaned_data.get('place_number') or ''
        burial_type = self.cleaned_data.get('burial_type')
        for k, v in Burial.BURIAL_TYPES:
            if k == burial_type:
                burial_type_str = v
                break
        else:
            burial_type_str = burial_type

        burial_container = self.cleaned_data.get('burial_container')
        if area and area.is_columbarium():
            if burial_container == Burial.CONTAINER_COFFIN:
                msg = _("Гроб нельзя положить в колумбарном участке")
                raise forms.ValidationError(msg)
            elif burial_container == Burial.CONTAINER_BIO:
                msg = _("Биоотходы не захораниваются в колумбарном участке")
                raise forms.ValidationError(msg)
            if burial_type == Burial.BURIAL_ADD:
                msg = _("Подзахоронение (т.е в новую могилу) немыслимо для колумбарного участка")
                raise forms.ValidationError(msg)

        fact_date  = self.cleaned_data.get('fact_date')
        if is_ugh:
            acc_number = self.cleaned_data.get('account_number') or ''
            if acc_number and fact_date:
                if self.request.user.profile.org.numbers_algo in (Org.NUM_YEAR_UGH, Org.NUM_YEAR_CEMETERY, ):
                    msg = _("Номер в книге учета должен быть ГГГГнннн (год факт. даты, номер). "
                            "ГГГГ может быть прошлым годом, если факт. дата до %s января"
                           )  % settings.YEAR_OVER_DAYS
                    if len(acc_number) < 4:
                        raise forms.ValidationError(msg)
                    try:
                        acc_year = int(acc_number[:4])
                        if acc_year != fact_date.year and \
                           not (fact_date.year - acc_year == 1 and \
                                fact_date.diff(datetime.date(acc_year, 1, 1)).days < settings.YEAR_OVER_DAYS
                                ):
                            raise forms.ValidationError(msg)
                    except ValueError:
                        raise forms.ValidationError(msg)
                if self.request.user.profile.org.numbers_algo in (Org.NUM_YEAR_MONTH_UGH, Org.NUM_YEAR_MONTH_CEMETERY, ):
                    msg = _("Номер в книге учета должен быть: ГГГГММннн (год, месяц фактической даты, номер)")
                    if not fact_date.month or not (1 <= fact_date.month <= 12):
                        raise forms.ValidationError(msg)
                    try:
                        if len(acc_number) < 6 or \
                           int(acc_number[:4]) != fact_date.year or \
                           int(acc_number[4:6]) != fact_date.month:
                            raise forms.ValidationError(msg)
                    except ValueError:
                        raise forms.ValidationError(msg)

            if self.archived_burial:
                if not acc_number.strip():
                    if not cemetery or cemetery.archive_burial_account_number_required:
                        msg = _("Нельзя %s архивное захоронение без указания его номера в книге учета для этого кладбища") % msg_complete
                        raise forms.ValidationError(msg)
                    if not place_number.strip() and \
                        cemetery and \
                        cemetery.places_algo_archive == Cemetery.PLACE_ARCHIVE_BURIAL_ACCOUNT_NUMBER:
                        msg = _("Номер места, если не задан, для этого кладбища формируется из учетного номера захоронения, а он пустой")
                        raise forms.ValidationError(msg)
            elif not place_number.strip() and \
                cemetery and \
                cemetery.places_algo == Cemetery.PLACE_MANUAL:
                msg = _("Номер места не может быть пуст при его задании вручную")
                raise forms.ValidationError(msg)

        if not place_number.strip() and \
           self.archived_burial and \
           cemetery and cemetery.places_algo_archive == Cemetery.PLACE_ARCHIVE_MANUAL:
            msg = _("Нельзя %s архивное захоронение без указания номера места для этого кладбища") % msg_complete
            raise forms.ValidationError(msg)
        elif not place_number.strip() and \
           (burial_type in (Burial.BURIAL_ADD, Burial.BURIAL_OVER,)) and \
           cemetery and cemetery.places_algo_archive == Cemetery.PLACE_ARCHIVE_MANUAL and is_ugh:
            msg = _("Нельзя %(msg_complete)s %(burial_type)s "
                    "без указания номера места для этого кладбища") % dict(
                        msg_complete=msg_complete, burial_type=burial_type_str.lower(),
                    )
            raise forms.ValidationError(msg)
        elif not place_number.strip() and area and area.availability == Area.AVAILABILITY_CLOSED:
            msg = _("Не указано место для закрытого участка. Нельзя %s захоронение") % msg_complete
            raise forms.ValidationError(msg)
        elif not place_number.strip() and \
             cemetery and \
             cemetery.ugh.numbers_algo == Org.NUM_EMPTY and \
             (
              (cemetery.places_algo == Cemetery.PLACE_BURIAL_ACCOUNT_NUMBER and \
               burial_type in (Burial.BURIAL_NEW,)
              ) or \
              (cemetery.places_algo_archive == Cemetery.PLACE_ARCHIVE_BURIAL_ACCOUNT_NUMBER and \
               burial_type in (Burial.BURIAL_ADD, Burial.BURIAL_OVER,)
              )
             ):
            # Такого не может быть, ибо проверяется в свойствах организации-угх,
            # чтобы не оказалось: номер зх оставить пустым, а есть кладбища
            # с расстановкой мест по номеру зх. Но fool-proof не помешает...
            if is_ugh or self.request.POST.get('ready'):
                msg = _("Номер места, если не задан, для этого кладбища формируется из учетного номера захоронения, а он пустой)")
                raise forms.ValidationError(msg)
        elif (row.strip() or place_number.strip()) and not area:
            msg = _("Указан ряд и/или место, но не указан участок")
            raise forms.ValidationError(msg)

        grave_number = self.cleaned_data.get('grave_number') or 1
        place = None
        if cemetery and area and place_number:
            try:
                place = Place.objects.get(cemetery=cemetery, area=area, row=row, place=place_number)
            except Place.DoesNotExist:
                pass
        if place and not place.is_columbarium():
            place_graves_count = place.get_graves_count()
            if place_graves_count < grave_number:
                if place_graves_count == 0 and grave_number == 1:
                    # учитываем случай, когда место создано без могил,
                    # и вводится захоронение в новую могилу, с номером 1
                    pass
                else:
                    msg = _("Номер могилы превышает количество могил в существующем месте")
                    raise forms.ValidationError(msg)
        elif not area or not area.is_columbarium():
            desired_graves_count = self.cleaned_data.get('desired_graves_count')
            if grave_number > desired_graves_count:
                msg = _("Номер могилы превышает запрошенное количество могил в новом месте")
                raise forms.ValidationError(msg)
            if self.request.user.profile.is_loru() and cemetery and cemetery.ugh:
                max_grave_number_this_ugh = \
                    Area.objects.filter(Q(cemetery__ugh=cemetery.ugh) & \
                                        Q(availability=Area.AVAILABILITY_OPEN)). \
                        aggregate(m=Max('places_count'))['m'] or 1
                if desired_graves_count > max_grave_number_this_ugh:
                    msg = _("Запрошенное число могил (%(desired_graves_count)s) в новом месте "
                            "превышает максимум (%(max_grave_number)s) по кладбищам этой организации" % dict(
                                desired_graves_count=desired_graves_count,
                                max_grave_number=max_grave_number_this_ugh
                           ))
                    raise forms.ValidationError(msg) 
            if self.request.user.profile.is_ugh() and \
               (self.cleaned_data.get('place_width') and not self.cleaned_data.get('place_length') or \
                not self.cleaned_data.get('place_width') and self.cleaned_data.get('place_length')
               ):
                raise forms.ValidationError(_("Надо указывать и длину, и ширину нового места"))

        if self.instance.is_closed() and not place_number.strip():
            raise forms.ValidationError(_("Не указан номер места закрытого захоронения"))

        if cemetery and area and cemetery.places_algo == Cemetery.PLACE_ROW and not row.strip():
            raise forms.ValidationError(_("На кладбище с нумерацией мест по ряду не указан номер ряда"))

        today = datetime.date.today()
        
        plan_date = self.cleaned_data.get('plan_date')
        if plan_date and \
           not self.archived_burial and \
           not self.instance.is_finished():
            if self.request.user.profile.is_ugh():
                days_before = self.request.user.profile.org.plan_date_days_before
            elif self.request.user.profile.is_loru() and cemetery and cemetery.ugh:
                days_before = cemetery.ugh.plan_date_days_before
            else:
                days_before = 0
            days_before = datetime.timedelta(days=days_before)
            if today > plan_date + days_before:
                if days_before:
                    msg = _("Плановая дата захоронения не может быть раньше "
                            "%(days_before)s %(days)s до текущей даты") % dict(
                                days_before=days_before.days,
                                days=_('дня') if days_before.days == 1 else _('дней'),
                            )
                else:
                    msg = _("Плановая дата захоронения не может быть раньше текущей даты")
                raise forms.ValidationError(msg)

        if is_ugh and cemetery and cemetery.places_algo == Cemetery.PLACE_CEM_YEAR and \
           not self.archived_burial and not self.instance.is_transferred():
                place_number = self.cleaned_data.get('place_number')
                if place_number:
                    if not re.match(r'^\d{4}.+',place_number) or int(place_number[:4]) > today.year or not int(place_number[:4]):
                        raise forms.ValidationError(_("Номер места должен быть: ГГГГмм...м (год не больше текущего, место)"))

        deadman_birth_date = None
        deadman_death_date = None

        if self.deadman_form.is_valid():
            deadman_birth_date = self.deadman_form.cleaned_data.get("birth_date")
            deadman_death_date = self.deadman_form.cleaned_data.get("death_date")
            if deadman_birth_date and deadman_death_date:
                if deadman_birth_date > deadman_death_date:
                    msg = _("Дата смерти не может быть раньше даты рождения")
                    raise forms.ValidationError(msg)
                lifetime = deadman_death_date.diff(deadman_birth_date).years
                if lifetime >= 260:
                    msg = _("Нереальное время жизни усопшего: %(lifetime)s лет "
                            "(%(birth_date)s -- %(death_date)s)") % dict(
                                lifetime=lifetime,
                                birth_date=deadman_birth_date,
                                death_date=deadman_death_date,
                    )
                    raise forms.ValidationError(msg)

            if deadman_death_date and deadman_death_date > today:
                msg = _("Дата смерти не может быть позже сегодняшней")
                raise forms.ValidationError(msg)
            if not self.instance.is_archive() and not self.instance.is_transferred():
                if plan_date and deadman_birth_date and \
                   deadman_birth_date > plan_date:
                    msg = _("Дата рождения не может быть позже плановой даты захоронения")
                    raise forms.ValidationError(msg)
                if plan_date and deadman_death_date and \
                   deadman_death_date > plan_date:
                    msg = _("Дата смерти не может быть позже плановой даты захоронения")
                    raise forms.ValidationError(msg)
            if fact_date and deadman_death_date and \
               deadman_death_date > fact_date:
                msg = _("Фактическая дата захоронения не может быть раньше даты смерти")
                raise forms.ValidationError(msg)

            #if settings.DEADMAN_IDENT_NUMBER_ALLOW and \
                #not self.archived_burial and \
                #not self.instance.is_transferred() and \
                #self.deadman_form.cleaned_data.get("last_name") and \
                #not (burial_container == Burial.CONTAINER_BIO) and \
                #not self.deadman_form.cleaned_data.get("ident_number"):
                #msg = _(u"Нет идентификационного номера для усопшего")
                 #raise forms.ValidationError(msg)

            if settings.DEADMAN_IDENT_NUMBER_ALLOW and \
                self.deadman_form.cleaned_data.get("ident_number"):
                ident_number = rus_to_lat(self.deadman_form.cleaned_data["ident_number"].strip())
                if ident_number and \
                   not re.search(r'^[A-Za-z0-9]{10,}$', ident_number):
                    msg = _("Идентификационный номер усопшего: не менее 10 цифр и латинских символов")
                    raise forms.ValidationError(msg)

        if self.dc_form.is_valid():
            death_certificate_release_date = self.dc_form.cleaned_data.get('release_date')
            death_certificate_release_date_msg = _("Не указана дата документа о смерти")
            death_certificate_s_number = self.dc_form.cleaned_data.get("s_number", "").strip()
            death_certificate_zags = self.dc_form.cleaned_data.get("zags")
            death_certificate_zags_msg = _("Не указан ЗАГС/мед. учреждение, выдавшее документ о смерти")

            if not (not settings.DEATH_CERTIFICATE_REQUIRED or \
                    self.archived_burial or \
                    self.instance.is_transferred() or \
                    self.request.user.profile.is_loru() or \
                    burial_container == Burial.CONTAINER_BIO or \
                    not can_personal_data
               ):
                if not death_certificate_s_number:
                    raise forms.ValidationError(_("Не заполнен номер свидетельства о смерти"))
                if not death_certificate_release_date:
                    raise forms.ValidationError(death_certificate_release_date_msg)
                if not death_certificate_zags:
                    raise forms.ValidationError(death_certificate_zags_msg)

            if death_certificate_s_number:
                have_s_number = _("Указан номер документа о смерти")
                if not death_certificate_release_date:
                    raise forms.ValidationError("%s. %s" % (have_s_number, death_certificate_release_date_msg,))
                if not death_certificate_zags:
                    raise forms.ValidationError("%s. %s" % (have_s_number, death_certificate_zags_msg,))
                
            if death_certificate_release_date:
                if deadman_birth_date:
                    if deadman_birth_date > death_certificate_release_date:
                        msg = _("Дата выдачи документа о смерти не может быть раньше даты рождения")
                        raise forms.ValidationError(msg)
                if deadman_death_date:
                    if deadman_death_date> death_certificate_release_date:
                        msg = _("Дата выдачи документа о смерти не может быть раньше даты смерти")
                        raise forms.ValidationError(msg)

        if self.responsible_form.is_valid() and \
           self.responsible_form.cleaned_data.get('take_from') == ResponsibleForm.WHERE_NEW:
            r_last_name = self.responsible_form.cleaned_data.get('last_name').strip()
            r_first_name = self.responsible_form.cleaned_data.get('first_name').strip()
            r_middle_name = self.responsible_form.cleaned_data.get('middle_name').strip()
            r_phones = self.responsible_form.cleaned_data.get('phones', '').strip()
            r_login_phone = self.responsible_form.cleaned_data.get('login_phone_')
            r_address = self.responsible_address_form.is_valid_data()
            msg = ''
            if r_last_name:
                # Ф (+) И (-) О (-) : OK
                # Ф (+) И (-) О (+) : Bad :
                if not r_first_name and r_middle_name:
                    msg = _("Ответственный: не указано имя при указанном отчестве")
                # Ф (+) И (+) О (-) : OK
                # Ф (+) И (+) О (+) : OK
            else:
                # Ф (-) И (-) О (-) : OK
                # Ф (-) И (-) О (+) : Bad :
                if not r_first_name and r_middle_name:
                    msg = _("Ответственный: не указаны фамилия и имя при указанном отчестве")
                # Ф (-) И (+) О (-) : Bad
                elif r_first_name and not r_middle_name:
                    msg = _("Ответственный: не указана фамилия при указанном имени")
                # Ф (-) И (+) О (+) : Bad
                elif r_first_name and r_middle_name:
                    msg = _("Ответственный: не указана фамилия при указанных имени и отчестве")
                elif r_login_phone:
                    msg = _("Ответственный: не указана фамилия при указанном мобильном телефоне для входа в кабинет")
                elif r_address:
                    msg = _("Ответственный: не указана фамилия при указанном адресе (полностью или частично)")
                elif r_phones:
                    msg = _("Ответственный: не указана фамилия при указанных телефоне (телефонах)")
            if msg:
                raise forms.ValidationError(msg)

            if self.request.POST.get('ready') and self.dc_form.is_valid() and self.deadman_form.is_valid():
                death_date = self.deadman_form.cleaned_data.get('death_date')
                last_name = self.deadman_form.cleaned_data.get('last_name').strip()
                s_number = self.dc_form.cleaned_data.get('s_number').strip()
                if death_date and last_name and s_number:
                    first_name = self.deadman_form.cleaned_data.get('first_name').strip()
                    middle_name = self.deadman_form.cleaned_data.get('middle_name').strip()
                    query = Burial.objects.filter(
                                Q(ugh__loru_list__loru=self.request.user.profile.org) & \
                                Q(annulated=False) & \
                                Q(status__in = (Burial.STATUS_CLOSED, Burial.STATUS_APPROVED,))
                            )
                    query = query.filter(
                                deadman__last_name=last_name,
                                deadman__first_name=first_name,
                                deadman__middle_name=middle_name,
                                deadman__deathcertificate__s_number=s_number,
                                deadman__death_date__year=death_date.year,
                                deadman__death_date__month=death_date.month,
                                deadman__death_date__day=death_date.day,
                            )
                    if self.instance.pk:
                        query = query.exclude(pk=self.instance.pk)
                    if query:
                        raise forms.ValidationError(
                                _("Такой усопший уже есть (ФИО, дата смерти, свидетельство). Нельзя согласовывать")
                              )
                
        return self.cleaned_data

    def mock_data(self):
        if not self.data:
            self.data = {}
            self.data.update(self.form_to_data(self))
            for f in self.forms:
                self.data.update(self.form_to_data(f))

class BurialApproveCloseForm(ChildrenJSONMixin, LoggingFormMixin, forms.ModelForm):
    """
    Формируется при одобрении или закрытии электронного захоронения
    """
    class Meta:
        model = Burial
        fields = ['cemetery', 'area', 'row', 'place_number',
                  'desired_graves_count', 'place_length', 'place_width',
                  'fact_date', ]

    def __init__(self, request, *args, **kwargs):
        super(BurialApproveCloseForm, self).__init__(*args, **kwargs)
        self.forms = []
        self.request = request
        self.dc_form = None
        self.forms =[]
        cemetery_qs = Q(pk__in=[c.pk for c in Cemetery.editable_ugh_cemeteries(request.user)])
        
        if self.data.get('cemetery'):
            cemetery = Cemetery.objects.get(pk=self.data.get('cemetery'))
        else:
            cemetery = self.instance.cemetery

        if request.user.profile.is_ugh():
            max_grave_number = \
                Area.objects.filter(Q(cemetery__ugh=request.user.profile.org) & \
                                    Q(availability=Area.AVAILABILITY_OPEN)). \
                    aggregate(m=Max('places_count'))['m'] or 1
            place = self.instance.get_place()
            if place:
                place_graves_count = place.get_graves_count()
                max_grave_number = max(max_grave_number, place_graves_count)
            max_grave_choices = [(i,i) for i in range(1, max_grave_number+1)]
            self.fields['place_length'].label = _('Длина нового места')
            self.fields['place_width'].label = _('Ширина нового места')

        if request.user.profile.is_ugh() and self.instance.can_finish():
            # Закрытие
            if not self.instance.fact_date:
                self.initial['fact_date'] = self.instance.plan_date
            if self.request.POST.get('complete'):
                for f in self.fields:
                    if f not in ['row', 'place_number']:
                        self.fields[f].required = True
            self.fields['cemetery'].queryset = Cemetery.objects.filter(cemetery_qs)
            self.fields['desired_graves_count'].widget = forms.Select(choices=max_grave_choices)
            if place:
                if place.is_columbarium():
                    self.initial['desired_graves_count'] = 1
                else:
                    self.initial['desired_graves_count'] = place_graves_count
                self.initial['place_length'] = place.place_length
                self.initial['place_width'] = place.place_width

        elif self.instance.can_approve():
            # отправленное на согласование или после этого отправленное на обследование в угх
            # * может не быть задан участок, тогда в форме будет кладбище и участок
            if request.user.profile.is_ugh():
                self.instance.area = Burial.objects.get(pk=self.instance.pk).area
                if self.instance.area:
                    for f in ('cemetery', 'area', 'row', 'place_number', 'fact_date', ):
                        del self.fields[f]
                    if self.instance.get_place():
                        del self.fields['desired_graves_count']
                        del self.fields['place_length']
                        del self.fields['place_width']
                else:
                    for f in ('row', 'place_number', 'fact_date', ):
                        del self.fields[f]
                    if self.request.POST.get('approve'):
                        for f in self.fields:
                            if f in ('cemetery', 'area', ):
                                self.fields[f].required = True
                    self.fields['cemetery'].queryset = \
                        Cemetery.objects.filter(cemetery_qs & Q(area__availability=Area.AVAILABILITY_OPEN)).distinct()
                if 'desired_graves_count' in self.fields:
                    self.fields['desired_graves_count'].widget = forms.Select(choices=max_grave_choices)

            elif request.user.profile.is_loru():
                # лору в отправленном на согласовании или в место-обследуемом зх
                # ничего править не может, кроме СоС, но это отдельная форма
                # внутри этой формы
                self.fields.clear()

            # и лору, и угх в отправленном на согласовании или в место-обследуемом зх
            # могут править СоС
            if not self.instance.is_bio() and self.instance.can_personal_data(self.request):
                try:
                    dc = self.instance and self.instance.deadman and self.instance.deadman.deathcertificate
                except DeathCertificate.DoesNotExist:
                    dc = None
                if not dc and deadman:
                    dc = DeathCertificate(person=deadman)
                self.dc_form = DeathCertificateForm(request, data=self.request.POST or None, instance=dc, prefix='deadman-dc')
                self.forms.append(self.dc_form)

                # - если угх нажмет "Согласовать" или если лору/угх нажмет "сохранить" (СоС),
                #   то там должны быть заполнены необходимые поля
                # - если угх нажмет "Отправить на обследование" или "Одобрить обследование",
                #   то СоС должно сохраниться, даже если там не всё заполнено
                if settings.DEATH_CERTIFICATE_REQUIRED and \
                   not request.POST.get('inspect') and \
                   not request.POST.get('approve-inspect'):
                    for f in self.dc_form.fields:
                        if f in ('s_number', 'release_date', 'zags',) :
                            self.dc_form.fields[f].required = True
                            
        if 'place_length' in self.fields:
            self.fields['place_length'].required = False
            self.fields['place_width'].required = False
            if (not self.instance.place_length or not self.instance.place_width) and \
               (not self.instance.area or not self.instance.area.is_columbarium):
                try:
                    place_size = PlaceSize.objects.get(org=request.user.profile.org,
                                                       graves_count=self.instance.desired_graves_count)
                    if not self.instance.place_length:
                        self.initial['place_length'] = place_size.place_length
                    if not self.instance.place_width:
                        self.initial['place_width'] = place_size.place_width
                except PlaceSize.DoesNotExist:
                    pass

        if request.POST.get('disapprove') and request.user.profile.is_ugh() and \
           self.instance.can_disapprove_ugh():
            for f in self.fields:
                self.fields[f].required = False

        if request.POST.get('approve') and request.user.profile.is_ugh() and \
           self.instance.can_approve_ugh():
            for f in ('place_number', 'fact_date', ):
                self.fields[f].required = False

    def clean(self):
        if self.is_valid() and \
           not self.request.POST.get('disapprove') and \
           'row' in self.fields and \
           self.cleaned_data['cemetery'].places_algo == Cemetery.PLACE_ROW and \
           not self.cleaned_data['row'].strip():
            raise forms.ValidationError(_("На кладбище с нумерацией мест по ряду не указан номер ряда"))
        return self.cleaned_data

    def clean_place_number(self):
        place_number = self.cleaned_data.get('place_number', '')
        if not self.request.POST.get('disapprove'):
            cemetery = self.cleaned_data.get('cemetery')
            if self.request.user.profile.is_ugh() and self.instance.can_finish() and cemetery and \
               not place_number.strip() and \
               (
                    (self.instance.burial_type in (Burial.BURIAL_NEW,) and \
                    cemetery.places_algo == Cemetery.PLACE_MANUAL) \
                or \
                    (self.instance.burial_type in (Burial.BURIAL_ADD, Burial.BURIAL_OVER,) and \
                    cemetery.places_algo_archive == Cemetery.PLACE_ARCHIVE_MANUAL)
               ):
                raise forms.ValidationError(_('Номер места обязателен для кладбища с ручной нумерацией мест'))
        return place_number

    def clean_area(self):
        """
        Проверка одобрения захоронения только в открытый участок.
        """
        if not self.request.POST.get('disapprove'):
            if self.instance.is_ready() and self.cleaned_data['area'].availability != Area.AVAILABILITY_OPEN:
                raise forms.ValidationError(_('Можно предлагать лишь открытый участок кладбища'))
        return self.cleaned_data['area']

    def clean_desired_graves_count(self):
        desired_graves_count = self.cleaned_data['desired_graves_count']
        if not self.request.POST.get('disapprove'):
            b_temp = Burial(cemetery = self.instance.cemetery,
                            area = self.instance.area,
                            row = self.instance.row,
                            place_number = self.instance.place_number
                        )
            if self.instance.area and self.instance.area.is_columbarium():
                desired_graves_count = 1
            else:
                if not b_temp.get_place() and self.instance.grave_number > desired_graves_count:
                    raise forms.ValidationError(_("Номер могилы превышает запрошенное количество могил в новом месте"))
        return desired_graves_count

    def clean_fact_date(self):
        fact_date = self.cleaned_data.get('fact_date')
        if not self.request.POST.get('disapprove'):
            deadman_death_date = self.instance.deadman and self.instance.deadman.death_date
            if fact_date and deadman_death_date and \
            deadman_death_date > fact_date:
                msg = _("Фактическая дата захоронения не может быть раньше даты смерти")
                raise forms.ValidationError(msg)
        return fact_date

    def is_valid(self):
        is_valid = super(BurialApproveCloseForm, self).is_valid() and all([f.is_valid() for f in self.forms])
        if not is_valid:
            messages.error(self.request, _('Обнаружены ошибки, их необходимо исправить'))
        return is_valid

    def get_prefix(self, form):
        prefix = ''
        if form is self.dc_form:
            prefix = _("Усопший, СоС, ")
        return prefix

    def save(self, commit=False, **kwargs):
        self.collect_log_data()
        commit = bool(self.fields) or commit
        self.instance = super(BurialApproveCloseForm, self).save(commit=commit, **kwargs)
        if self.dc_form:
            self.dc_form.save()
        self.put_log_data()
        return self.instance

class AddAgentForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['user_last_name','user_first_name', 'user_middle_name', ]

    def random_string(self):
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for x in range(10))

    def clean(self):
        cleaned_data = super(AddAgentForm, self).clean()
        if not cleaned_data['user_last_name'].strip():
            msg = _("Не заполнена фамилия")
            raise forms.ValidationError(msg)

        if cleaned_data['user_middle_name'].strip() and \
           not cleaned_data['user_first_name'].strip():
            msg = _("Не заполнено имя при имеющемся отчестве")
            raise forms.ValidationError(msg)
        return cleaned_data

    def save(self, commit=True, *args, **kwargs):
        org = kwargs.pop('org')
        profile = super(AddAgentForm, self).save(commit=False, *args, **kwargs)
        profile.org = org
        profile.is_agent=True
        user = User()
        user.is_active = False
        user.email = None
        user.username = org.email or ''
        user.last_name = profile.user_last_name
        user.first_name = profile.user_first_name
        if profile.user_middle_name:
            user.first_name = user.first_name + ' ' + profile.user_middle_name
        while not user.username or User.objects.filter(username=user.username).exists():
            user.username = self.random_string()
        if commit:
            user.save() 
            profile.user = user 
            profile.save()
        return profile

class AddDoverForm(StrippedStringsMixin, forms.ModelForm):
    class Meta:
        model = Dover
        exclude = ['agent', 'document', ]

    def clean(self):
        StrippedStringsMixin.clean(self)
        
        # Всплывающая форма. Если какое-то из обязательных полей не задано, то не будет,
        # как в "обычной" форме у поля сообщения "Обязательное поле". Просто не будет
        # никакой реакции. И имя незаполненного или неверно заполненного поля не будет в
        # cleaned_data.
        errors = []
        for field in ('begin', 'end', 'number', ):
            if not self.cleaned_data.get(field):
                errors.append("%s : обязательное поле или неверно задано" % str(self.fields[field].label))
        if errors:
            raise forms.ValidationError("\n".join(errors))

        begin_date = self.cleaned_data['begin']
        end_date  = self.cleaned_data['end']
        number = self.cleaned_data['number']
        if begin_date > end_date:
            msg = _("Дата начала доверенности не может быть раньше даты окончания доверенности")
            raise forms.ValidationError(msg)

        return self.cleaned_data

class SpravkaForm(forms.Form):

    # Все текстовые (!) поля формы начинаются со spravka_. Javascript увеличит их ширину
    #
    spravka0_relative = forms.BooleanField(required=False, initial=True, label=_("Справка родственнику?"))
    spravka_applicant = forms.CharField(required=False, max_length=100, label=_("Кому выдается"))
    spravka_applicant_address = forms.CharField(required=False, max_length=100, label=_("Кому выдается, адрес"))
    spravka_issuer_title = forms.CharField(required=False, max_length=100, label=_("Кто выдал, должность"))
    spravka_issuer = forms.CharField(required=False, max_length=100, label=_("Кто выдал, фамилия и.о."))

class AddOrgForm(StrippedStringsMixin, BaseOrgForm):
    class Meta:
        model = Org
        fields = ('type', 'name', 'full_name', 'inn',
                  'phones', 'fax', 'email',
        )
    
    def __init__(self, request, *args, **kwargs):
        super(AddOrgForm, self).__init__(request, *args, **kwargs)
        self.required_fields = []
        for field in ('name', 'full_name', 'inn', ):
            if self.fields[field].required:
                self.required_fields.append(field)
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super(AddOrgForm, self).clean()
        errors = []
        for field in self.required_fields:
            # Нюанс django: Если clean_FIELD raises an exception,
            # то FIELD не будет в cleaned_data, а здесь вызывается
            # clean_inn родительского класса (OrgForm)
            if field in cleaned_data and not cleaned_data[field].strip():
                errors.append("%s : обязательное поле" % str(self.fields[field].label))
        if errors:
            raise forms.ValidationError("\n".join(errors))
        return cleaned_data

    def save(self, commit=True):
        self.collect_log_data()
        org = super(AddOrgForm, self).save(commit=False)
        if commit:
            try:
                org.save()
                if org.type == Org.PROFILE_LORU:
                    org.create_wallet_rate()
                self.put_log_data(msg=_('Добавлена организация'))
            except IntegrityError:
                # Случай, который не удалось воспроизвести: duplicate auto-slug field
                org = None
        return org

class AddDocTypeForm(forms.ModelForm):
    class Meta:
        model = IDDocumentType
        fields = '__all__'

class ExhumationForm(ChildrenJSONMixin, SafeDeleteMixin, AppOrgFormMixin, forms.ModelForm):
    opf = forms.ChoiceField(label='', choices=OPF_CHOICES, widget=forms.RadioSelect, initial=Org.OPF_PERSON)

    class Meta:
        model = ExhumationRequest
        exclude = ['plan_date', 'plan_time']

    def __init__(self, request, burial, *args, **kwargs):
        super(ExhumationForm, self).__init__(*args, **kwargs)
        self.request = request
        self.burial = burial
        self.init_app_org_label()

        reorder_form_fields(self.fields, old_pos=-1, new_pos=0)

        if self.instance.applicant:
            self.initial['opf'] = Org.OPF_PERSON
        else:
            self.initial['opf'] = Org.OPF_ORG

        if burial.cemetery and burial.cemetery.time_slots and self.fields.get('plan_time'):
            choices = [('', '----------')] + burial.cemetery.get_time_choices(
                date=burial.plan_date,
                request=self.request,
            )
            self.fields['plan_time'].widget = forms.Select(choices=choices)
        if self.instance.plan_time:
            self.initial['plan_time'] = self.instance.plan_time.strftime('%H:%M')

        # Отсутствие выбора будет в выпадающем списке не "---", а ""
        self.fields['applicant_organization'].empty_label = ''
        self.fields['applicant_organization'].inactive_queryset = \
            Org.objects.filter(Q(profile=None) | ~Q(profile__user__is_active=True)).distinct()

        self.forms = self.construct_forms()

    def is_valid(self):
        return self.opf_valid(ExhumationForm)

    def construct_forms(self):
        data = self.data or None
        applicant = self.instance and self.instance.applicant
        self.applicant_form = AlivePersonForm(data=data, prefix='applicant', instance=applicant)
        applicant_addr = applicant and applicant.address
        self.applicant_address_form = LocationForm(data=data, prefix='applicant-address', instance=applicant_addr)
        try:
            applicant_id = self.instance and self.instance.applicant and self.instance.applicant.personid
        except PersonID.DoesNotExist:
            applicant_id = None
        self.applicant_id_form = PersonIDForm(data=data, prefix='applicant-pid', instance=applicant_id)

        return [self.applicant_form, self.applicant_address_form, self.applicant_id_form]

    def clean(self):
        if self.is_valid():
            exhumation_date = self.cleaned_data.get('fact_date')
            burial_date = self.burial.fact_date
            if burial_date and exhumation_date:
                if burial_date.d > exhumation_date:
                    raise forms.ValidationError(_("Дата эксгумации не может быть раньше даты захоронения"))
            if self.cleaned_data.get('opf') == Org.OPF_ORG:
                if not (self.cleaned_data.get('agent_director') or \
                        self.cleaned_data.get('agent') and self.cleaned_data.get('dover')):
                    raise forms.ValidationError(_('Нет данных об агенте и/или доверенности для заявителя-ЮЛ. Изменения не сохранены'))
            else:
                if not self.applicant_form.is_valid_data():
                    raise forms.ValidationError(_("Нужно указать Заявителя-ФЛ"))
        return self.cleaned_data

    def save(self, commit=True, *args, **kwargs):
        self.instance = super(ExhumationForm, self).save(commit=False, *args, **kwargs)

        self.instance.burial = self.burial
        self.instance.place = self.burial.place

        if self.cleaned_data.get('agent_director'):
            self.instance.agent = None
            self.instance.dover = None

        if self.cleaned_data.get('opf') == Org.OPF_PERSON and self.applicant_form.is_valid_data():
            applicant = self.applicant_form.save(commit=False)
            if self.applicant_address_form.is_valid_data():
                applicant.address = self.applicant_address_form.save()
            applicant.save()

            if self.applicant_id_form.is_valid_data():
                pid = self.applicant_id_form.save(commit=False)
                pid.person = applicant
                pid.save()
            self.instance.applicant = applicant
            self.instance.applicant_organization = None
            self.instance.agent_director = False
            self.instance.agent = None
            self.instance.dover = None

        else:
            self.safe_delete('applicant', self.instance)

        self.instance.save()

        return self.instance

class BurialCommentEditForm(forms.ModelForm):

    class Meta:
        model = BurialComment
        fields = ('comment',)

class BaseBurialCommentEditFormSet(BaseInlineFormSet):
    def __init__(self, request, *args, **kwargs):
        super(BaseBurialCommentEditFormSet, self).__init__(*args, **kwargs)
        self.own_cemetery = not self.instance.cemetery or \
                            self.instance.cemetery in Cemetery.editable_ugh_cemeteries(request.user)
        is_role_cemetery_manager_in_system = Role.objects.filter(name=Role.ROLE_CEMETERY_MANAGER).exists()
        if is_role_cemetery_manager_in_system:
            is_cemetery_manager = self.own_cemetery and request.user.profile.is_cemetery_manager()

        for f in self.forms:
            f.formset = self
            f.fields['comment'].required = False
            f.owner_ = False
            f.can_edit_ = False
            f.owner_retired_ = False
            f.own_cemetery = self.own_cemetery
            if not self.own_cemetery:
                f.fields['comment'].widget.attrs.update({'readonly':'True'})
            if f.instance.pk:
                owner = f.instance.owner()
                if owner == request.user:
                    f.owner_ = True
                    f.can_edit_ = self.own_cemetery

                # Комментарий захоронения без кладбища может править только
                # создатель комментария

                elif self.instance.cemetery:

                #   Если текущий пользователь - не владелец комментария. Два варианта.
                #   1. Есть роль заведующего кладбищем в системе.
                #       Тогда править чужой комментарий
                #       может только заведующий кладбищем, даже если владелец комментария
                #       еще имеет права на кладбище.
                #       ! Есть вариант, когда роли регистратора или смотрителя в системе нет,
                #         а все смотрители имеют роль заведующего. Тогда роль заведущего
                #         будет правильно обозвать Регистратор или смотритель, а роль смотрителя
                #         удалить из системы.
                #   2. Нет роли заведующего кладбищем в системе.
                #       Тогда любой пользователь из тех, кто имеет права на кладбище,
                #       может редактировать/удалять комментарий, если владелец комментария
                #       уже не имеет прав на кладбище (уволен, ушел на другое кладбище,
                #       потерял роль регистратора/смотрителя)
                #

                    if is_role_cemetery_manager_in_system:
                        if is_cemetery_manager:
                            f.owner_retired_ = self.instance.cemetery not in Cemetery.editable_ugh_cemeteries(user=owner)
                            f.can_edit_ = True
                    else:
                        if self.own_cemetery:
                            f.owner_retired_ = self.instance.cemetery not in Cemetery.editable_ugh_cemeteries(user=owner)
                            f.can_edit_ = f.owner_retired_
                if not f.can_edit_:
                    f.fields['comment'].widget.attrs.update({'readonly':'True'})
            f.fields['comment'].widget.attrs.update({'rows':'4'})

BurialCommentEditFormSet = inlineformset_factory(
    Burial,
    BurialComment,
    form=BurialCommentEditForm,
    formset=BaseBurialCommentEditFormSet,
    extra=1
)

class AddGravesForm(forms.Form):
    place_grave_choice = forms.IntegerField(
        required=True,
        label=_("Установите число могил в месте:"),
    )

    def __init__(self, *args, **kwargs):
        super(AddGravesForm, self).__init__(*args, **kwargs)
        self.fields['place_grave_choice'].widget = forms.Select(choices=((1,1),))

class RegistryForm(forms.ModelForm):

    date_from = forms.DateField(required=True, label=_("С"))
    date_to = forms.DateField(required=True, label=_("по"))

    class Meta:
        model = Profile
        fields = ('date_from', 'date_to', 'cemeteries',)

    def clean_date_from(self):
        d = self.cleaned_data['date_from']
        if d > datetime.date.today():
            raise forms.ValidationError(_("Дата больше текущей"))
        return d

    def clean_date_to(self):
        d = self.cleaned_data['date_to']
        if d > datetime.date.today():
            raise forms.ValidationError(_("Дата больше текущей"))
        return d

    def clean_cemeteries(self):
        cemeteries = self.cleaned_data['cemeteries']
        if len(cemeteries) == 0:
            raise forms.ValidationError(_("Не заданы кладбища"))
        return cemeteries

    def clean(self):
        cleaned_data = super(RegistryForm, self).clean()
        if self.is_valid():
            date_from = self.cleaned_data['date_from']
            date_to = self.cleaned_data['date_to']
            if date_from > date_to:
                raise forms.ValidationError(_("Начальная дата больше конечной"))
            if (date_to - date_from).days > 30:
                raise forms.ValidationError(_("Интервал между датами не дложен быть больше 30 дней"))
        return cleaned_data
