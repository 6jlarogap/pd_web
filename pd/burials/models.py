# coding=utf-8
import datetime
import re
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db import models, connection
from django.db.models import Count, Avg
from django.db.models.deletion import ProtectedError
from django.utils.translation import ugettext_lazy as _
from django.db.models.query_utils import Q
from django.conf import settings
from pd.models import UnclearDateModelField, BaseModel, Files, GetLogsMixin, validate_gt0, SafeDeleteMixin
from pd.views import get_front_end_url

from persons.models import DeadPerson, DeathCertificate, CustomPlace
from reports.models import Report
from users.models import Org, Profile, Dover, ProfileLORU, CustomerProfile, PhonesMixin, \
                         is_ugh_user, is_cabinet_user
from logs.models import Log
from geo.models import GeoPointModel, CoordinatesModel

from geo.models import GeoPointModel

from logs.models import write_log

from managers import PlaceManager

from sms_service.utils import send_sms

class Cemetery(GetLogsMixin, BaseModel, PhonesMixin):
    PLACE_AREA = 'area'
    PLACE_ROW = 'row'
    PLACE_CEM_YEAR = 'cem_year'
    PLACE_BURIAL_ACCOUNT_NUMBER = 'burial_account_number'
    PLACE_MANUAL = 'manual'
    PLACE_TYPES = (
        (PLACE_AREA, _(u'По участку')),
        (PLACE_ROW, _(u'По ряду')),
        (PLACE_CEM_YEAR, _(u'Кладбище + год')),
        (PLACE_BURIAL_ACCOUNT_NUMBER, _(u'По рег. номеру захоронения')),
        (PLACE_MANUAL, _(u'Вручную')),
    )

    PLACE_ARCHIVE_MANUAL = 'manual'
    PLACE_ARCHIVE_PREFIX_AREA = '-area'
    PLACE_ARCHIVE_BURIAL_ACCOUNT_NUMBER = 'burial_account_number'
    PLACE_ARCHIVE_TYPES = (
        (PLACE_ARCHIVE_MANUAL, _(u'Вручную')),
        (PLACE_ARCHIVE_PREFIX_AREA, _(u'По порядку в пределах участка (-0001 -0002...)')),
        (PLACE_ARCHIVE_BURIAL_ACCOUNT_NUMBER, _(u'По рег. номеру захоронения')),
    )

    name = models.CharField(_(u"Название"), max_length=255)
    time_begin = models.TimeField(_(u"Начало работы"), null=True, blank=True)
    time_end = models.TimeField(_(u"Окончание работы"), null=True, blank=True)
    places_algo = models.CharField(_(u"Расстановка номеров мест новых ручных и электронных захоронений"),
                                max_length=255, choices=PLACE_TYPES, default=PLACE_AREA)
    # - все архивные захоронения (новые, подзахоронения, захоронения в существующиую)
    # - ручные и электронные подзахоронения и захоронения в существующиую
    places_algo_archive = models.CharField(_(u"Расстановка номеров существующих, но неучтенных мест"),
                                max_length=255, choices=PLACE_ARCHIVE_TYPES, default=PLACE_ARCHIVE_MANUAL)
    time_slots = models.TextField(_(u"Время для захоронения"), default='', blank=True,
                                  help_text=_(u'В формате ЧЧ:ММ, по одному на строку'))

    creator = models.ForeignKey('auth.User', verbose_name=_(u"Владелец"),
                                on_delete=models.PROTECT)
    ugh = models.ForeignKey(Org, verbose_name=_(u"УГХ"), null=True, limit_choices_to={'type': Org.PROFILE_UGH},
                            on_delete=models.PROTECT)
    address = models.ForeignKey('geo.Location', editable=False, null=True)
    archive_burial_fact_date_required = models.BooleanField(_(u"Дата архивного захоронения обязательна"), default=True)
    archive_burial_account_number_required = models.BooleanField(_(u"Номер архивного захоронения обязателен"), default=True)
    square = models.FloatField(_(u"Площадь"), null=True, editable=False)

    class Meta:
        verbose_name = _(u"Кладбище")
        verbose_name_plural = _(u"Кладбища")
        ordering = ['name']
        unique_together = ('ugh', 'name',)

    def __unicode__(self):
        return self.name

    def unique_error_message(self, model_class, unique_check):
        if len(unique_check) == 1:
            return super(Cemetery, self).unique_error_message(model_class, unique_check)
        # unique_together
        else:
            return _(u"Кладбище с таким названием уже существует")

    def get_time_choices(self, date, request):
        others = Burial.objects.none()
        others_loru = Burial.objects.none()
        if date:
            others = Burial.objects.filter(cemetery=self, plan_date=date)
            others_loru = Burial.objects.filter(applicant_organization=request.user.profile.org, plan_date=date)
        result = []

        for s in self.time_slots.split('\n'):
            if s.strip():
                planned = filter(lambda b: b.is_ready() and b.plan_time.strftime('%H:%M') == s, others)
                approved = filter(lambda b: b.is_approved() and b.plan_time.strftime('%H:%M') == s, others)
                if request.user.profile.is_loru():
                    planned_others = filter(lambda b: b.is_ready() and b.plan_time.strftime('%H:%M') == s, others_loru)
                    approved_others = filter(lambda b: b.is_approved() and b.plan_time.strftime('%H:%M') == s, others_loru)
                    v = u'%s (резерв кладб. %s, лору%s)' % (s, len(planned)+len(approved), len(planned_others)+len(approved_others))
                else:
                    v = u'%s (резерв кладб. %s)' % (s, len(planned)+len(approved))
                result.append((s, v))
        return result
    
    @property
    def area_cnt(self):
        # TODO: replace with field, updated trought signals 
        return self.area_set.count()

    @property
    def work_time(self):
        return "%s-%s" % (self.time_begin or u'00:00:00', self.time_end or u'00:00:00')



class CemeteryCoordinates(CoordinatesModel):
    #TODO:
    # Перевести эту модель к PointsModel
    cemetery = models.ForeignKey(Cemetery, verbose_name=_(u"Кладбище"), on_delete=models.PROTECT, related_name='coordinates')

    class Meta:
        unique_together = ('cemetery', 'angle_number',)

class AreaPurpose(models.Model):
    name = models.CharField(_(u"Название"), max_length=255)

    class Meta:
        verbose_name = _(u"Назначение участков")
        verbose_name_plural = _(u"Назначение участков")

    def __unicode__(self):
        return self.name


class Area(BaseModel):
    AVAILABILITY_OPEN = 'open'
    AVAILABILITY_OLD = 'old_only'
    AVAILABILITY_CLOSED = 'closed'

    AVAILABILITY_CHOICES = (
        (AVAILABILITY_OPEN, _(u'Открыт')),
        (AVAILABILITY_OLD, _(u'Только подзахоронения')),
        (AVAILABILITY_CLOSED, _(u'Закрыт')),
    )

    cemetery = models.ForeignKey(Cemetery, verbose_name=_(u"Кладбище"), on_delete=models.PROTECT)
    name = models.CharField(_(u"Название"), max_length=255)
    availability = models.CharField(_(u"Открытость"), max_length=32, choices=AVAILABILITY_CHOICES, null=True)
    purpose = models.ForeignKey(AreaPurpose, verbose_name=_(u"Назначение"), null=True, on_delete=models.PROTECT)
    places_count = models.PositiveIntegerField(_(u"Макс. кол-во могил в месте"), default=1)
    square = models.FloatField(_(u"Площадь"), null=True, editable=False)

    class Meta:
        verbose_name = _(u"Участок")
        verbose_name_plural = _(u"Участки")
        ordering = ['name']
        unique_together = ('cemetery', 'name',)

    def __unicode__(self):
        return _(u'%s (%s, %s, %s могил)') % (
            self.name,
            self.get_availability_display() or _(u"откр.неизв"), self.purpose or _(u"назн. неизв"),
            self.places_count
        )

    def unique_error_message(self, model_class, unique_check):
        if len(unique_check) == 1:
            return super(Area, self).unique_error_message(model_class, unique_check)
        # unique_together
        else:
            return _(u"Участок с таким названием уже существует")

    def save(self, *args, **kwargs):
        if not self.name.strip():
            self.name=''
        return super(Area, self).save(*args, **kwargs)

class AreaCoordinates(CoordinatesModel):
    area = models.ForeignKey(Area, verbose_name=_(u"Участок"), on_delete=models.PROTECT, related_name='coordinates')

    class Meta:
        unique_together = ('area', 'angle_number',)

class Place(SafeDeleteMixin, GeoPointModel):
    STATUS_LIST = ('dt_wrong_fio', 'dt_military', 'dt_size_violated', 'dt_unowned', 'dt_unindentified', )

    cemetery = models.ForeignKey(Cemetery, verbose_name=_(u"Кладбище"), on_delete=models.PROTECT)
    area = models.ForeignKey(Area, verbose_name=_(u"Участок"), blank=True, null=True,
                             on_delete=models.PROTECT)
    row = models.CharField(_(u"Ряд"), max_length=255, blank=True, null=True)
    oldplace = models.CharField(_(u"Старое место"), max_length=255, blank=True, null=True)
    place = models.CharField(_(u"Место"), max_length=255, blank=True, null=True)
    available_count = models.PositiveSmallIntegerField(_(u"Число свободных мест"), default=0)
    responsible = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Ответственный"), blank=True, null=True,
                                    on_delete=models.PROTECT)
    place_length = models.DecimalField(_(u"Длина, м."), max_digits=5, decimal_places=2,
                                       null=True, blank=True, validators=[validate_gt0])
    place_width = models.DecimalField(_(u"Ширина, м."), max_digits=5, decimal_places=2,
                                        null=True, blank=True, validators=[validate_gt0])

    # Следующие поля DateTimeField будут содержать дату установки
    # соответствующего признака, но служат еще и как BooleanField:
    # если поле установлено в какую-то дату, то это True; если NULL, то False
    dt_wrong_fio = models.DateTimeField(_(u"Неверное ФИО /дата установки признака/"), null=True, editable=False)
    dt_military = models.DateTimeField(_(u"Воинское /дата установки признака/"), null=True, editable=False)
    dt_size_violated = models.DateTimeField(_(u"Нарушение размеров /дата установки признака/"), null=True, editable=False)
    dt_unowned = models.DateTimeField(_(u"Заброшенное /дата установки признака/"), null=True, editable=False)
    dt_unindentified = models.DateTimeField(_(u"Неопознанное /дата установки признака/"), null=True, editable=False)

    objects = PlaceManager()

    class Meta:
        verbose_name = _(u"Место")
        verbose_name_plural = _(u"Место")
        unique_together = ('cemetery', 'area', 'row', 'place',)
        ordering = ['row', 'place']

    def __unicode__(self):
        return _(u'Кл. %s, уч. %s, ряд %s, место %s') % (self.cemetery, self.area and self.area.name or '', self.row, self.place)

    def full_name(self):
        result = _(u'Кладбище: %s') % self.cemetery.name
        if self.area:
            result = _(u"%s, участок: %s") % (result, self.area.name, )
        if self.row:
            result = _(u"%s, ряд: %s") % (result, self.row, )
        if self.place:
            result = _(u"%s, место: %s") % (result, self.place)
        return result

    def unique_error_message(self, model_class, unique_check):
        if len(unique_check) == 1:
            return super(Place, self).unique_error_message(model_class, unique_check)
        # unique_together
        else:
            return _(u"Место с таким номером уже существует")


    def burials_available(self):
        q_ex = Q(status=Burial.STATUS_EXHUMATED) | Q(annulated=True)
        return self.burial_set.exclude(q_ex)

    def burial_count(self):
        return self.burials_available().distinct('grave').count()

    def get_graves_count(self):
        return self.grave_set.count()

    def get_available_count(self):
        """
        Deprecated func
        please use 'self.available_count' which is updated via signals
        """
        return self.available_count
        #return max(0, self.get_graves_count() - self.burial_count())

    def set_next_number(self, new_place_for_archive=False):
        if new_place_for_archive:
            assert self.cemetery and \
                self.cemetery.places_algo_archive in (Cemetery.PLACE_ARCHIVE_PREFIX_AREA, ), \
                u'Empty place number for a new archive burial and no appropriate algorythm'
        elif self.cemetery.places_algo in (Cemetery.PLACE_MANUAL,
                                           Cemetery.PLACE_BURIAL_ACCOUNT_NUMBER,
                                          ):
            return

        filter = 'cemetery_id=%s' % (self.cemetery.pk, )
        if new_place_for_archive:
            # self.cemetery.places_algo_archive == Cemetery.PLACE_ARCHIVE_PREFIX_AREA:
            # пока это едиственный выбор для заполнения пустого места архивного зх
            prefix = '-'
            num_template = '%05d'
            filter += ' and area_id=%s' % (self.area.pk, )
        else:
            prefix = ''
            num_template = '%d'
            if self.cemetery.places_algo == Cemetery.PLACE_ROW:
                filter += " and area_id=%s and row='%s'" % (self.area.pk, self.row, )
            elif self.cemetery.places_algo == Cemetery.PLACE_AREA:
                filter += ' and area_id=%s' % (self.area.pk, )
            elif self.cemetery.places_algo == Cemetery.PLACE_CEM_YEAR:
                prefix = str(datetime.datetime.now().year)
                num_template = '%04d'
            else:
                return

        p_regex = r"E'^%s\\d+$'" % (re.escape(prefix), )
        query = ("select max(substring(place from %s)::integer) from burials_place "
                "where place ~ %s and %s"
                ) % (len(prefix)+1, p_regex, filter, );

        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        num = result and result[0] or 0
        self.place = prefix + num_template % (num + 1, )

    def remove_responsible(self):
        self.safe_delete('responsible', self)

    def bio_only(self):
        """
        В месте только биоотходы
        """
        burials_available = self.burials_available()
        return burials_available and all([ b.is_bio() for b in burials_available ])

    def save(self, new_place_for_archive=False, *args, **kwargs):
        if self.cemetery and self.area and not self.place:
            # Новое место для архивного зх формируется по другим правилам,
            # нежели для остальных зх
            self.set_next_number(new_place_for_archive)
        return super(Place, self).save(*args, **kwargs)

    def create_graves(self, graves_count, grave_number):
        """
        Создать place_count могил для только что созданного place
        
        Возвращаем указатель на могилу c номером grave_number
        """
        result = None
        for n in range(1, graves_count + 1):
            grave = Grave.objects.create(place=self, grave_number=n,)
            if n == grave_number:
                result = grave
        return result

    def get_or_create_graves(self, grave_number):
        """
        Создать могилы, если надо
        
        Применяется для аннулированного зх при его де-аннулировании.
        Возвращаем указатель на могилу
        """
        result = None
        for n in range(grave_number, 0, -1):
            grave, created = Grave.objects.get_or_create(place=self, grave_number=n,)
            if n == grave_number:
                result = grave
            if not created:
                break
        return result

    def get_photo_gallery(self, request):
        """
        Получить все фото, относящиеся к месту.
        """
        gallery = []
        for pph in PlacePhoto.objects.filter(place=self).order_by('-date_of_creation'):
            if pph.bfile:
                gallery.append(
                    {
                        'photo': request.build_absolute_uri(pph.bfile.url),
                        'addedAt': pph.date_of_creation,
                    }
                )
        return gallery
        
    def status_list(self):
        """
        Вернуть список статусов, например ['dt_wrong_fio', 'dt_unindentified', ]
        """
        result  = []
        for f in Place.STATUS_LIST:
            value = getattr(self,f)
            if value:
                result.append(f)
        return result

    @classmethod
    def log_login_phone_change(cls, request, old_login_phone):
        """
        Записать в журнал по всем местам и захоронениям изменение login_phone
        """
        for place in cls.objects.filter(responsible__user=request.user):
            message = _(u"Ответственный изменил телефон входа в систему c %s на %s") % (
                old_login_phone,
                place.responsible.login_phone,
            )
            write_log(request, place, message)
            for burial in place.burial_set.all():
                write_log(request, burial, message)

    def address(self):
        result = _(u'Кладбище %s, участок %s') % (self.cemetery.name, self.area.name, )
        if self.row:
            result += _(u', ряд %s') % self.row
        result += _(u', место %s') % self.place
        cemetery_address = self.cemetery.address and self.cemetery.address.__unicode__() or ''
        if cemetery_address:
            result += _(u', %s') % cemetery_address
        return result

    def graves_list(self):
        graves = []
        for g in Grave.objects.filter(place=self).order_by('grave_number'):
            grave = {'graveNumber': g.grave_number}
            grave['burials'] = []
            for b in g.burial_set.exclude(burial_container=Burial.CONTAINER_BIO).exclude(annulated=True):
                grave['burials'].append(
                    {
                        'id': b.pk,
                        'fio': b.deadman and b.deadman.full_name_complete() or _(u"Неизвестный"),
                        'lastName': b.deadman and b.deadman.last_name,
                        'firstName': b.deadman and b.deadman.first_name,
                        'middleName': b.deadman and b.deadman.middle_name,
                        'photo': None,
                        'birthDate': b.deadman and b.deadman.birth_date and b.deadman.birth_date.str_safe() or None,
                        'deathDate': b.deadman and b.deadman.death_date and b.deadman.death_date.str_safe() or None,
                    }
                )
            graves.append(grave)
        return graves

class PlaceSize(models.Model):
    org = models.ForeignKey(Org, verbose_name=_(u"Организация"), editable=False, on_delete=models.PROTECT) 
    graves_count = models.PositiveSmallIntegerField(_(u"Число могил"), )
    place_length = models.DecimalField(_(u"Длина, м."), max_digits=5, decimal_places=2, validators=[validate_gt0])
    place_width = models.DecimalField(_(u"Ширина, м."), max_digits=5, decimal_places=2, validators=[validate_gt0])

    class Meta:
        verbose_name = _(u"Размер места")
        verbose_name_plural = _(u"Размеры мест")
        unique_together = ('org', 'graves_count', )
        ordering = ('graves_count', )

class PlaceStatus(BaseModel):
    PS_ACTUAL = 'actual'
    PS_FOUND_UNOWNED = 'found-unowned'
    PS_SIGNED = 'signed'
    PS_RESPONSIBLE_REJECTED = 'responsible-rejected'
    PS_ACCEPTED_UNOWNED = 'accepted-unowned'
    PS_RECOVERING = 'recovering'
    PS_RECOVERED = 'recovered'
    PS_OTHER = 'other'
    PS_TYPES = (
        (PS_ACTUAL, _(u'Действующее место')),
        (PS_FOUND_UNOWNED, _(u'Обнаружено бесхозяйным')),
        (PS_SIGNED, _(u'Установлена табличка')),
        (PS_RESPONSIBLE_REJECTED, _(u'Отказ ответственного от места')),
        (PS_ACCEPTED_UNOWNED, _(u'Признано бесхозяйным')),
        (PS_RECOVERING, _(u'Готовится к повторному использованию')),
        (PS_RECOVERED, _(u'Готово к повторному использованию')),
        (PS_OTHER, _(u'Другой статус места')),
    )
    place = models.ForeignKey(Place, verbose_name=_(u"Место"))
    status = models.CharField(_(u"Статус"), max_length=40, choices=PS_TYPES, default=PS_ACTUAL)
    comment = models.TextField(verbose_name=_(u"Примечание"), blank=True, null=True)
    creator = models.ForeignKey('auth.User', verbose_name=_(u"Создатель"), editable=False,
                                on_delete=models.PROTECT)


class Grave(GeoPointModel):
    place = models.ForeignKey(Place, verbose_name=_(u"Место"))
    grave_number = models.PositiveSmallIntegerField(_(u"Номер"), default=1)
    is_wrong_fio = models.BooleanField(_(u"Неверное ФИО"), default=False)
    is_military = models.BooleanField(_(u"Воинская могила"), default=False)

    class Meta:
        unique_together = ('place', 'grave_number',)
        ordering = ['grave_number']

    def __unicode__(self):
        return _(u'Могила. место: %s номер:%d') % (self.place, self.grave_number)

    def delete(self, using=None, request=None):
        super(Grave, self).delete(using=using)
        if request:
            arr = [_(u'Могила №%d удалена') % self.grave_number,]
            # Reorder grave numbers
            i = 1
            relocated = False
            for row in self.place.grave_set.order_by('grave_number').all():
                if row.grave_number != i: 
                    if not relocated:
                        relocated = i
                    row.grave_number = i
                    row.save()
                i += 1
            if relocated > 0:
                if relocated < i-1:
                    arr.append( _(u'Могилы %d-%d перенумерованы') % (relocated+1, i))
                else:
                    arr.append( _(u'Могила %d перенумерована') % (relocated+1))
            write_log(request, self.place, u"<br/>".join(arr))
        else:
            raise Exception('Warning: Grave::delete - "request" param is undefined')

    def full_name(self):
        return _(u"%s, могила %s") % (self.place.full_name(), self.grave_number)

class PlacePhoto(Files, GeoPointModel):
    place = models.ForeignKey(Place)

    def is_accessible_anonymous(self):
        """
        Доступно ли анонимному пользователю
        """
        return bool(self.place.dt_unowned)

    def is_accessible(self, user):
        """
        Доступность фото места:
        
        * ОМС, чье кладбище, где место
        * Пользователь кабинета, если это его место
        * Анонимный пользователь, если место бесхозное
        """
        result = False
        if self.is_accessible_anonymous():
            result = True
        elif is_ugh_user(user):
            result = self.place.cemetery.ugh == user.profile.org
        elif is_cabinet_user(user):
            result = self.place.responsible and \
                     self.place.responsible.login_phone and \
                     self.place.responsible.login_phone == user.customerprofile.login_phone
        return result
        

class AreaPhoto(Files, GeoPointModel):
    area = models.ForeignKey(Area)

class Burial(SafeDeleteMixin, GetLogsMixin, BaseModel):
    STATUS_BACKED = 'backed'
    STATUS_DECLINED = 'declined'
    STATUS_DRAFT = 'draft'
    STATUS_READY = 'ready'
    STATUS_INSPECTING = 'inspecting'
    STATUS_APPROVED = 'approved'
    STATUS_CLOSED = 'closed'
    STATUS_EXHUMATED = 'exhumated'
    STATUS_CHOICES = (
        (STATUS_BACKED, _(u"Отозвано")),
        (STATUS_DECLINED, _(u"Отклонено")),
        (STATUS_DRAFT, _(u"Черновик")),
        (STATUS_READY, _(u"На согласовании")),
        (STATUS_INSPECTING, _(u"На обследовании")),
        (STATUS_APPROVED, _(u"Согласовано")),
        (STATUS_CLOSED, _(u"Закрыто")),
        (STATUS_EXHUMATED, _(u"Эксгумировано")),
    )

    BURIAL_NEW = 'common'
    BURIAL_ADD = 'additional'
    BURIAL_OVER = 'overlap'

    BURIAL_TYPES = (
        (BURIAL_NEW, _(u'Новое захоронение')),
        (BURIAL_ADD, _(u'Подзахоронение')),
        (BURIAL_OVER, _(u'Захоронение в существующую')),
    )

    NEW_BURIAL_TYPES = ['common', 'urn']

    SOURCE_FULL = 'full'
    SOURCE_UGH = 'ugh'
    SOURCE_ARCHIVE = 'archive'
    SOURCE_TRANSFERRED = 'transferred'
    SOURCE_TYPES = (
        (SOURCE_FULL, _(u"Электронное")),
        (SOURCE_UGH, _(u"Ручное")),
        (SOURCE_ARCHIVE, _(u"Архивное")),
        (SOURCE_TRANSFERRED, _(u"Перенесенное")),
    )
    CONTAINER_COFFIN = 'container_coffin'
    CONTAINER_URN = 'container_urn'
    CONTAINER_ASH = 'container_ash'
    CONTAINER_BIO = 'container_bio'

    BURIAL_CONTAINERS = (
        (CONTAINER_COFFIN, _(u"Гроб")),
        (CONTAINER_URN, _(u"Урна")),
        (CONTAINER_ASH, _(u"Прах")),
        (CONTAINER_BIO, _(u"Биоотходы")),
    )

    burial_type = models.CharField(_(u"Вид захоронения"), max_length=255, null=True, blank=True, choices=BURIAL_TYPES, default=BURIAL_NEW)
    burial_container = models.CharField(_(u"Тип захоронения"), max_length=255, null=True, blank=True, choices=BURIAL_CONTAINERS, default=CONTAINER_COFFIN)
    source_type = models.CharField(_(u"Источник"), max_length=255, null=True, editable=False, choices=SOURCE_TYPES)
    account_number = models.CharField(_(u"№ в книге учета"), max_length=255, null=True, blank=True)

    place = models.ForeignKey(Place, verbose_name=_(u"Место"), null=True, blank=True, on_delete=models.PROTECT)
    cemetery = models.ForeignKey(Cemetery, verbose_name=_(u"Кладбище"), null=True, blank=True, on_delete=models.PROTECT)
    area = models.ForeignKey(Area, verbose_name=_(u"Участок"), blank=True, null=True,
                                                  on_delete=models.PROTECT)
    row = models.CharField(_(u"Ряд"), max_length=255, blank=True, null=True)
    place_number = models.CharField(_(u"Номер места"), max_length=255, null=True, blank=True,
                                    help_text=_(u"Если пусто - номер будет сгенерирован автоматически"))
    grave = models.ForeignKey(Grave, verbose_name=_(u"Могила"),
                              null=True, blank=True, editable=False, on_delete=models.PROTECT)
    grave_number = models.PositiveSmallIntegerField(_(u"Могила"), default=1)
    desired_graves_count = models.PositiveSmallIntegerField(_(u"Число могил в новом месте"), default=1)
    place_length = models.DecimalField(_(u"Длина, м."), max_digits=5, decimal_places=2,
                                        null=True, blank=True, validators=[validate_gt0])
    place_width = models.DecimalField(_(u"Ширина, м."), max_digits=5, decimal_places=2,
                                        null=True, blank=True, validators=[validate_gt0])
    responsible = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Ответственный"), blank=True, null=True,
                                    related_name='responsible_burials', on_delete=models.PROTECT)

    plan_date = models.DateField(_(u"План. дата"), null=True, blank=True)
    plan_time = models.TimeField(_(u"План. время"), null=True, blank=True)
    fact_date = UnclearDateModelField(_(u"Факт. дата"), null=True, blank=True)

    deadman = models.ForeignKey(DeadPerson, verbose_name=_(u"Усопший"), null=True, editable=False,
                                on_delete=models.PROTECT)

    applicant = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Заявитель"), blank=True, null=True,
                                  related_name='applied_burials', on_delete=models.PROTECT)
    ugh = models.ForeignKey(Org, verbose_name=_(u"УГХ"), null=True, editable=False, related_name='ugh_created',
                            limit_choices_to={'type': Org.PROFILE_UGH}, on_delete=models.PROTECT)
    loru = models.ForeignKey(Org, verbose_name=_(u"Посредник"), null=True, 
                             limit_choices_to={'type': Org.PROFILE_LORU}, on_delete=models.PROTECT)
    loru_agent_director = models.BooleanField(_(u"Директор-Агент"), default=False, blank=True)
    loru_agent = models.ForeignKey(Profile, verbose_name=_(u"Агент"), null=True, blank=True,
                              limit_choices_to={'is_agent': True}, on_delete=models.PROTECT,
                              related_name='agent_burials',)
    loru_dover = models.ForeignKey(Dover, verbose_name=_(u"Доверенность"), null=True, blank=True,
                              related_name='dover_burials', on_delete=models.PROTECT)
    applicant_organization = models.ForeignKey(Org, verbose_name=_(u"Заявитель-ЮЛ"), null=True, blank=True,
                                               related_name='loru_created', on_delete=models.PROTECT)
    agent_director = models.BooleanField(_(u"Директор-Агент"), default=False, blank=True)
    agent = models.ForeignKey(Profile, verbose_name=_(u"Агент"), null=True, blank=True,
                              limit_choices_to={'is_agent': True}, on_delete=models.PROTECT)
    dover = models.ForeignKey(Dover, verbose_name=_(u"Доверенность"), null=True, blank=True, on_delete=models.PROTECT)

    status = models.CharField(_(u"Статус"), max_length=255, choices=STATUS_CHOICES, default=STATUS_DRAFT, editable=False)
    changed_by = models.ForeignKey('auth.User', editable=False, null=True, related_name='changed_requests',
                                   on_delete=models.PROTECT)
    annulated = models.BooleanField(_(u"Аннулировано"), default=False, blank=True)
    flag_no_applicant_doc_required = models.BooleanField(_(u"Документ заявителя-ФЛ не требуется"),
                                   editable=False, default=False)

    class Meta:
        verbose_name = _(u"Захоронение")
        verbose_name_plural = _(u"Захоронение")

    def is_edit(self):
        return self.is_draft() or self.is_backed() or self.is_declined()

    def is_draft(self):
        return self.status == self.STATUS_DRAFT

    def is_ready(self):
        return self.status == self.STATUS_READY

    def is_inspecting(self):
        return self.status == self.STATUS_INSPECTING

    def is_approved(self):
        return self.status == self.STATUS_APPROVED

    def is_closed(self):
        return self.status == self.STATUS_CLOSED

    def is_backed(self):
        return self.status == self.STATUS_BACKED

    def is_declined(self):
        return self.status == self.STATUS_DECLINED

    def is_annulated(self):
        return self.annulated

    def is_finished(self):
        return self.is_closed() or self.is_annulated()

    def is_exhumated(self):
        return self.status == self.STATUS_EXHUMATED

    def is_ugh_only(self):
        return self.source_type == self.SOURCE_UGH

    def is_full(self):
        return self.source_type == self.SOURCE_FULL

    def is_transferred(self):
        return self.source_type == self.SOURCE_TRANSFERRED

    def is_full_or_transferred(self):
        return self.is_full() or self.is_transferred()

    def is_archive(self):
        return self.source_type == self.SOURCE_ARCHIVE

    def is_ugh(self):
        return self.is_ugh_only() or self.is_archive()

    def is_new(self):
        return self.burial_type == self.BURIAL_NEW

    def is_add(self):
        return self.burial_type == self.BURIAL_ADD

    def is_over(self):
        return self.burial_type == self.BURIAL_OVER

    def is_bio(self):
        return self.burial_container == self.CONTAINER_BIO

    def can_approve(self):
        return self.is_full() and (self.is_ready() or self.is_inspecting())

    def can_inspect(self):
        return self.is_full() and \
               self.is_ready() and \
               self.cemetery and self.area and self.place_number

    def can_approve_inspect(self):
        # одобрение обследования означает перевод захоронения
        # из статуса "Отправлено на обследование"
        # в статус "На согласовании"
        return self.is_full() and self.is_inspecting()

    def dc_filled(self):
        """
        В захоронении заполнено свидетельство о смерти
        """
        
        # ВНИМАНИЕ! СоС не надо заполнять для биоотходов, но для них
        #           эта функция вернёт False.
        try:
            dc = self.deadman.deathcertificate
            return dc.s_number and dc.release_date and dc.zags
        except (AttributeError, DeathCertificate.DoesNotExist, ):
            pass
        return False

    def can_finish(self):
        """
        Условия закрытия захоронения
        """
        if self.is_annulated():
            return False
        elif self.is_full():
            return self.is_approved()
        else:
            return self.is_draft() or self.is_approved()

    def can_approve_ugh(self):
        """
        Условия возможности согласование ручного черновика
        """
        return self.is_ugh() and self.is_draft()

    def can_disapprove_ugh(self):
        """
        Условия отзыва угх ручного или архивного согласованного захоронения
        """
        return self.is_ugh() and self.is_approved()

    def can_ugh_annulate(self):
        if self.annulated:
            return False
        if self.is_full():
            return self.is_closed() or self.is_exhumated()
        if self.is_ugh_only():
            return self.is_closed() or self.is_draft() or self.is_approved() or self.is_exhumated()
        if self.is_transferred() or self.is_archive():
            return True
        return False

    def can_loru_annulate(self):
        return not self.annulated and self.is_full() and self.is_edit()

    # УГХ может де-аннулировать всё аннулированное, кроме того что может
    # аннулировать лишь ЛОРУ
    #
    def can_ugh_deannulate(self):
        return self.annulated and not (self.is_full() and self.is_edit())

    def can_loru_deannulate(self):
        return self.annulated and self.is_full() and self.is_edit()

    def can_back(self):
        return self.is_full() and not self.is_annulated() and \
               (self.is_ready() or self.is_approved() or self.is_inspecting())

    can_decline = can_back
        # УГХ может отклонить зх при тех же условиях, что ЛОРУ может отозвать

    # условия печати уведомлений для ugh.
    def can_ugh_print_notification(self):
        return self.is_approved() or self.is_closed()

    # условия печати уведомлений для loru.
    def can_loru_print_notification(self):
        return self.is_approved()

    # условия печати справок, справки может выдавать лишь УГХ
    def can_ugh_print_reference(self):
        return self.is_closed()

    @property
    def exhumated(self):
        try:
            return self.exhumationrequest
        except ExhumationRequest.DoesNotExist:
            return

    @property
    def status_str(self):
        return self.get_status_display()

    @property
    def status_dt(self):
        return self.dt_modified

    def get_orders(self, loru):
        return self.burial_orders.filter(loru=loru)

    def ugh_name(self):
        return self.cemetery and self.cemetery.ugh and self.cemetery.ugh.name or ''

    def loru_name(self):
        return self.applicant_organization and self.applicant_organization.name or ''

    def set_account_number(self, user):
        ugh = self.ugh or user.profile.org
        cemetery = self.cemetery
        if user.profile.is_ugh():
            algo = ugh.numbers_algo
        else:
            algo = Org.NUM_EMPTY
        
        if algo in (Org.NUM_YEAR_UGH, Org.NUM_YEAR_CEMETERY,
                    Org.NUM_YEAR_MONTH_UGH, Org.NUM_YEAR_MONTH_CEMETERY, ):
            others = Burial.objects.none()
            now = datetime.datetime.now()
            year = str(now.year)
            month = "%02d" % now.month if algo in (Org.NUM_YEAR_MONTH_UGH, Org.NUM_YEAR_MONTH_CEMETERY, ) \
                                       else ''
            an_regex = r"E'^%s%s\\d+$'" % (year, month, )
                
            # Мы должны использовать числовое сравнение dddd, например,
            # в 2013dddd. При символьном сравнении всех 2013dddd,
            # после номера '20139' следующий всегда будет
            # 20134 = int('20139') +1
            #
            query = ("select max(substring(account_number from %s)::integer) from burials_burial "
                    "where account_number ~ %s"
                    ) % (7 if month else 5, an_regex, );
            if algo in (Org.NUM_YEAR_UGH, Org.NUM_YEAR_MONTH_UGH, ) and ugh:
                query += ' and ugh_id=%s' % ugh.id
            elif algo in (Org.NUM_YEAR_CEMETERY, Org.NUM_YEAR_MONTH_CEMETERY, ) and cemetery:
                query += ' and cemetery_id=%s' % cemetery.id

            if self.pk:
                query += ' and id!=%s' % self.pk
                
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            num = result and result[0] or 0
            self.account_number = year + month + ('%03d' if month else '%04d') % (num + 1, )

    def approve(self, user):
        if not self.account_number and not self.is_archive():
            self.set_account_number(user)
            self.save()

    def get_place(self):
        if self.place:
            return self.place

        params = {
            'cemetery': self.cemetery,
            'area': self.area,
            'row': self.row,
        }
        if self.place_number:
            params.update({'place': self.place_number})
        else:
            return None
        try:
            return Place.objects.get(**params)
        except Place.DoesNotExist:
            return None

    def get_responsible(self):
        return self.responsible or (self.get_place() and self.get_place().responsible) or None

    def get_last_decline_reason(self):
        """
        Получить причину последнего отказа в захоронении, если в этом захоронении отказано
        
        Если причина не указана, возвращаем None
        """
        if not self.is_declined():
            return None
        ct = ContentType.objects.get_for_model(self)
        msg_declined = u"Захоронение отклонено"
        try:
            logrec = Log.objects.filter(ct=ct, obj_id=self.pk, msg__startswith=msg_declined).order_by('-pk')[0]
        except IndexError:
            return None
        reason = logrec.msg[len(msg_declined):]
        if reason and reason[0] == ":":
            reason = reason[1:]
        reason = reason.strip()
        return reason if reason else None

    def get_documents(self):
        ct = ContentType.objects.get_for_model(self)
        return Report.objects.filter(content_type=ct, object_id=self.pk).order_by('-pk')

    def approved_dt(self):
        return self.dt_modified

    def close(self, request, old_place=None):
        if not self.account_number:
            self.set_account_number(user=self.changed_by)

        if not self.place_number and \
           self.cemetery and \
           (
                self.is_archive() and \
                self.cemetery.places_algo_archive == Cemetery.PLACE_ARCHIVE_BURIAL_ACCOUNT_NUMBER \
            or \
                not self.is_archive() and \
                self.cemetery.places_algo == Cemetery.PLACE_BURIAL_ACCOUNT_NUMBER \
           ):
            self.place_number = self.account_number

        place = self.get_place() or Place()
        if place != old_place:
            if not place.pk or not place.burial_count(): # move TO new
                place.responsible = self.get_responsible() # update responsible
            else: # move TO existing
                if not old_place or not old_place.pk or not old_place.burial_count(): # and FROM old and populated
                    # Первое закрытие. Загоняем в существуюшее место
                    # Если ничего не ввели в ответственном, то оставляем прежнего в месте
                    # Иначе заменяем
                    if self.responsible:
                        place.responsible = self.responsible
        else:
            if not place.responsible:
                place.responsible = self.get_responsible() # just update responsible
            # Здесь учитываем ситуацию:
            # * Правится закрытое соединение, в неизменившемся (!) месте
            #   которого был ответственный, ибо:
            #      сформирован place, а он формируется только в закрытом зх.
            #      Тем более мы здесь в уже закрытом зх, что у place 
            #      (и у old_place == place) есть ответственный
            # * В этом неизменившемся месте угх затирает ответственного
            #   уже ранее закрытого захоронения:
            #      self.responsible становится None средствами формы, 
            #      self.get_responsible() вернет ответственного из места,
            #      а там он может быть не пустой, в итоге ответственный
            #      неизменившегося места не затрется, как хочет угх, если
            #      не сделать:
            elif not self.responsible:
                self.safe_delete('responsible', place)

        place.cemetery = self.cemetery
        place.area = self.area
        place.row = self.row
        place.place = self.place_number
        new_place = not place.pk
        if new_place:
            place.place_length = self.place_length
            place.place_width = self.place_width
        place.save(new_place_for_archive=self.is_archive() or self.is_over() or self.is_add())
        if new_place:
            graves_count = self.desired_graves_count or 1
            # fool-proof, чтоб не пропустили могилу с номером,
            # бОльшим чем заложено для участка. Это должно проверяться
            # в форме правки захоронения, но мало ли...
            #
            graves_count = max(graves_count, self.grave_number)
            self.grave = place.create_graves(graves_count, self.grave_number)
        elif not self.is_annulated():
            self.grave = Grave.objects.get(place=place, grave_number=self.grave_number)
        if self.is_annulated():
            self.grave = None
            
        if not self.fact_date:
            self.fact_date = self.plan_date

        self.responsible = None
        self.place = place
        self.place_number = place.place
        old_status = self.status
        self.status = self.STATUS_CLOSED
        self.save()

        if old_status != self.STATUS_CLOSED:
            write_log(request, self, _(u'Захоронение закрыто'))
        
        if place.responsible and \
           place.responsible.login_phone and \
           request and \
           old_status != self.STATUS_CLOSED:
            try:
                customerprofile = CustomerProfile.objects.get(login_phone=place.responsible.login_phone)
                user = customerprofile.user
                text = _(u'Место %s прикреплено. pohoronnoedelo.ru') % place.pk
                email_error_text = _(u"Пользователь %s (телефон %s) не смог получить СМС после прикрепления места %s" % \
                                    (customerprofile.user.username, place.responsible.login_phone, place.pk,))
            except CustomerProfile.DoesNotExist:
                # create_cabinet() создаст user, customerprofile с login_phone,
                # а также занесет в place.responsible нового user
                user, password = CustomerProfile.create_cabinet(place.responsible)
                text = _(u'%s login: %s parol: %s') % (
                    get_front_end_url(request).rstrip('/'),
                    place.responsible.login_phone,
                    password,
                )
                email_error_text = _(u"Пользователь %s не смог получить пароль после закрытия захоронения" % \
                                    (place.responsible.login_phone,))
                if request and settings.DEBUG:
                    messages.warning(
                        request,
                        _(u"Создан пользователь кабинета %s, пароль %s") % (place.responsible.login_phone, password, ),
                    )
            CustomPlace.objects.get_or_create(user=user, place=place)
            if not settings.DEBUG:
                sent, message = send_sms(
                    phone_number=place.responsible.login_phone,
                    text=text,
                    email_error_text=email_error_text,
                    user=request.user,
                )

        # Очистим "пустышку" свидетельства о смерти, где
        # не все обязательные поля заполнены
        #
        if self.is_full():
            try:
                dc = self.deadman.deathcertificate
                if not (dc.s_number and dc.release_date and dc.zags):
                    dc.delete()
            except (AttributeError, DeathCertificate.DoesNotExist, ProtectedError):
                pass

        return self

    def deadman_or_bio(self):
        """
        Для печати: во многих местах надо отражать или ФИО, или 'биоотходы'
        """
        if self.is_bio():
            return _(u'биоотходы')
        if not self.deadman:
            return _(u'Неизвестный')
        return self.deadman

    def __unicode__(self):
        return u'%s' % self.pk

    def combined_date(self):
        if self.fact_date:
            return self.fact_date.strftime('%d.%m.%Y')
        elif self.plan_date or self.plan_time:
            pd = self.plan_date and self.plan_date.strftime('%d.%m.%Y') or ''
            pt = self.plan_time and self.plan_time.strftime('%H:%M') or ''
            return u'%s %s' % (pd, pt)
        else:
            return ''

    def order_applicant(self):
        result = None
        if self.order:
            if self.order.applicant_organization:
                result = self.order.applicant_organization
            elif self.order.applicant:
                result = self.order.applicant
        return result

    def place_number_guess(self):
        """
        Номер места, если еще не записан
        
        Когда захоронение согласовано, для кладбищ с авто нумерацией мест
        номер места еще может быть не сформирован. Но если это кладбище
        имеет алгоритм авто расстановки мест "По рег. номеру захоронения",
        то будущий номер места известен: номер захоронения,
        что и просит указать заказчик в уведомлении о захоронении.
        """
        result = self.place_number
        if not result and \
            self.cemetery and \
            self.cemetery.places_algo == Cemetery.PLACE_BURIAL_ACCOUNT_NUMBER and \
            self.account_number:
           result = self.account_number
        return result

    def can_bind_to_order(self, org):
        """
        Может ли лору из организации org прикрепить это захоронение к заказу
        """
        result = False
        if self.is_full() and self.loru == org and not self.is_annulated():
            result = True
        #elif (self.is_closed() or self.is_exhumated() or self.is_approved()) and \
                #not self.is_bio() and \
                #not self.is_annulated() and \
                #self.ugh and \
                #ProfileLORU.objects.filter(ugh=self.ugh,loru=org).exists():
            #result = True
        return result

    def is_editable(self, user):
        """
        Захоронение может правится организацией этого пользователя
        
        Например, используется, чтоб определить, имеет ли пользователь право
        на удаление файла или редактирование его комментария
        """
        result = False
        try:
            if user.profile.is_loru():
                return self.loru and \
                       self.is_full() and \
                       self.is_edit() and \
                       self.loru == user.profile.org
            elif user.profile.is_ugh():
                return self.ugh and \
                       (self.is_full() and self.is_closed() or \
                        self.is_ugh() or self.is_transferred()
                       ) and \
                       self.ugh == user.profile.org
        except AttributeError:
            # пользователь без профиля.
            pass
        return result
        
    def is_accessible(self, user):
        """
        Захоронение доступно организации этого пользователя
        
        Например, используется, чтоб определить, имеет ли пользователь право
        на просмотр файла, прикрепленного к захоронению
        """
        result = False
        try:
            if user.profile.is_loru():
                return self.loru and \
                       self.is_full() and \
                       self.loru == user.profile.org
            elif user.profile.is_ugh():
                return self.ugh and \
                       (self.is_full() and not self.is_draft() or \
                        self.is_ugh() or self.is_transferred()
                       ) and \
                       self.ugh == user.profile.org
        except AttributeError:
            # пользователь без профиля.
            pass
        return result
        
class BurialFiles(Files):
    """
    Файлы, связанные с захоронением
    """
    burial = models.ForeignKey(Burial)

class PlaceStatusFiles(Files):
    """
    Файлы, связанные со статусом места
    """
    placestatus = models.ForeignKey(PlaceStatus)

class Reason(models.Model):
    TYPE_BACK = 'back'
    TYPE_DECLINE = 'decline'
    TYPE_ANNULATE = 'annulate'
    TYPE_DISAPPROVE = 'disapprove'
    TYPE_CHOICES = (
        (TYPE_BACK, _(u'ЛОРУ отзывает захоронение')),
        (TYPE_DECLINE, _(u'ОМС отказывает в захоронении')),
        (TYPE_ANNULATE, _(u'Аннулирование захоронения')),
        (TYPE_DISAPPROVE, _(u'ОМС отзывает согласование ручного захоронения')),
    )
    # ЛОРУ и УГХ имеют разные списки отказов и др. действий
    #
    TYPES_UGH = (TYPE_DECLINE, TYPE_ANNULATE, TYPE_DISAPPROVE, )
    # ЛОРУ аннулирует лишь свои черновики, отказванные, отозванные,
    # т.е. по сути свои черновики, так что незачем ему указывать причину
    # аннулирования
    TYPES_LORU = (TYPE_BACK, )
    
    org = models.ForeignKey(Org, verbose_name=_(u"Организация"), editable=False, on_delete=models.PROTECT) 
    reason_type = models.CharField(_(u'Действие'), max_length=255, choices=TYPE_CHOICES)
    name = models.CharField(_(u'Причина'), max_length=255)
    text = models.TextField(_(u'Текст причины'), default='', editable=False)

    class Meta:
        verbose_name = _(u"Причина")
        verbose_name_plural = _(u"Причины")
        ordering = ('reason_type', 'name', )
        unique_together = ('org', 'reason_type', 'name')

    def save(self, *args, **kwargs):
        if not self.text.strip():
            self.text = self.name
        return super(Reason, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.pk

class ExhumationRequest(SafeDeleteMixin, models.Model):
    burial = models.OneToOneField(Burial, editable=False)
    place = models.ForeignKey(Place, editable=False, null=True)
    plan_date = models.DateField(_(u"План. дата"), null=True, blank=True)
    plan_time = models.TimeField(_(u"План. время"), null=True, blank=True)
    fact_date = models.DateField(_(u"Факт. дата"), null=True)
    applicant = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Заказчик-ФЛ"), null=True, blank=True,
                                  on_delete=models.PROTECT)
    applicant_organization = models.ForeignKey(Org, verbose_name=_(u"Заказчик-ЮЛ"), null=True, blank=True,
                                  on_delete=models.PROTECT)
    agent_director = models.BooleanField(_(u"Директор-Агент"), default=False, blank=True)
    agent = models.ForeignKey('users.Profile', verbose_name=_(u"Агент"), null=True, blank=True,
                              limit_choices_to={'is_agent': True}, on_delete=models.PROTECT)
    dover = models.ForeignKey('users.Dover', verbose_name=_(u"Доверенность"), null=True, blank=True,
                              on_delete=models.PROTECT)

    class Meta:
        verbose_name = _(u"Запрос на эксгумацию")
        verbose_name_plural = _(u"Запросы на эксгумацию")

    def __unicode__(self):
        return u'%s' % self.pk

    def apply(self):
        self.place = self.burial.place
        self.save()

        self.burial.place = None
        self.burial.status = Burial.STATUS_EXHUMATED
        self.burial.save()

    def delete(self, using=None):
        self.burial.status = Burial.STATUS_CLOSED
        self.burial.place = self.place
        self.burial.save()
        self.safe_delete('applicant', self)
        return super(ExhumationRequest, self).delete(using=using)

def apply_exhumation(instance, created, **kwargs):
    if created:
        instance.apply()

models.signals.post_save.connect(apply_exhumation, sender=ExhumationRequest)


def calculate_free_burial_count(sender, instance, **kwargs):
    if instance.place:
        instance.place.available_count = max(0, instance.place.get_graves_count() - instance.place.burial_count())
        instance.place.save()

models.signals.post_save.connect(calculate_free_burial_count, sender=Grave)
models.signals.post_save.connect(calculate_free_burial_count, sender=Burial)
models.signals.post_delete.connect(calculate_free_burial_count, sender=Grave)
models.signals.post_delete.connect(calculate_free_burial_count, sender=Burial)
