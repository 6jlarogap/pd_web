# coding=utf-8
import datetime
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.deletion import ProtectedError
from django.utils.translation import ugettext_lazy as _
from django.db.models.query_utils import Q
from pd.models import UnclearDateModelField

import os
import pytils

from persons.models import DeadPerson
from reports.models import Report
from users.models import Org, Profile, Dover
from logs.models import Log


class Cemetery(models.Model):
    PLACE_CEMETERY = 'cemetery'
    PLACE_AREA = 'area'
    PLACE_ROW = 'row'
    PLACE_CEM_YEAR = 'cem_year'
    PLACE_BURIAL_ACCOUNT_NUMBER = 'burial_account_number'
    PLACE_MANUAL = 'manual'
    PLACE_TYPES = (
        (PLACE_CEMETERY, _(u'По кладбищу')),
        (PLACE_AREA, _(u'По участку')),
        (PLACE_ROW, _(u'По ряду')),
        (PLACE_CEM_YEAR, _(u'Кладбище + год')),
        (PLACE_BURIAL_ACCOUNT_NUMBER, _(u'По рег. номеру захоронения')),
        (PLACE_MANUAL, _(u'Ручное')),
    )

    name = models.CharField(_(u"Название"), max_length=255)
    time_begin = models.TimeField(_(u"Начало работы"))
    time_end = models.TimeField(_(u"Окончание работы"))
    places_algo = models.CharField(_(u"Расстановка номеров мест"), max_length=255, choices=PLACE_TYPES, default=PLACE_MANUAL)
    time_slots = models.TextField(_(u"Время для захоронения"), default='', blank=True,
                                  help_text=_(u'В формате ЧЧ:ММ, по одному на строку'))

    creator = models.ForeignKey('auth.User', verbose_name=_(u"Владелец"), editable=False, null=True,
                                on_delete=models.PROTECT)
    created = models.DateTimeField(_(u"Создано"), auto_now_add=True)
    ugh = models.ForeignKey(Org, verbose_name=_(u"УГХ"), null=True, limit_choices_to={'type': Org.PROFILE_UGH},
                            on_delete=models.PROTECT)

    address = models.ForeignKey('geo.Location', editable=False, null=True)

    class Meta:
        verbose_name = _(u"Кладбище")
        verbose_name_plural = _(u"Кладбища")
        ordering = ['name']

    def __unicode__(self):
        return self.name

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

class AreaPurpose(models.Model):
    name = models.CharField(_(u"Название"), max_length=255)

    class Meta:
        verbose_name = _(u"Назначение участков")
        verbose_name_plural = _(u"Назначение участков")

    def __unicode__(self):
        return self.name

class Area(models.Model):
    AVAILABILITY_OPEN = 'open'
    AVAILABILITY_OLD = 'old_only'
    AVAILABILITY_CLOSED = 'closed'

    AVAILABILITY_CHOICES = (
        (AVAILABILITY_OPEN, _(u'Открыт')),
        (AVAILABILITY_OLD, _(u'Только подзахоронения')),
        (AVAILABILITY_CLOSED, _(u'Закрыт')),
    )

    cemetery = models.ForeignKey(Cemetery, verbose_name=_(u"Кладбище"), on_delete=models.PROTECT)
    name = models.CharField(_(u"Название"), max_length=255, blank=True)
    availability = models.CharField(_(u"Открытость"), max_length=32, choices=AVAILABILITY_CHOICES, null=True)
    purpose = models.ForeignKey(AreaPurpose, verbose_name=_(u"Назначение"), null=True, on_delete=models.PROTECT)
    places_count = models.PositiveIntegerField(_(u"Кол-во могил в месте"), default=1)

    class Meta:
        verbose_name = _(u"Участок")
        verbose_name_plural = _(u"Участки")
        ordering = ['name']

    def __unicode__(self):
        return _(u'%s (%s, %s, %s могил)') % (
            self.name,
            self.get_availability_display() or _(u"откр.неизв"), self.purpose or _(u"назн. неизв"),
            self.places_count
        )

    def save(self, *args, **kwargs):
        if not self.name.strip():
            self.name=''
        return super(Area, self).save(*args, **kwargs)

class Place(models.Model):
    cemetery = models.ForeignKey(Cemetery, verbose_name=_(u"Кладбище"), on_delete=models.PROTECT)
    area = models.ForeignKey(Area, verbose_name=_(u"Участок"), blank=True, null=True)
    row = models.CharField(_(u"Ряд"), max_length=255, blank=True, null=True)
    place = models.CharField(_(u"Место"), max_length=255, blank=True, null=True)
    places_count = models.PositiveIntegerField(_(u"Кол-во могил"), null=True)
    responsible = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Ответственный"), blank=True, null=True,
                                    on_delete=models.PROTECT)

    class Meta:
        verbose_name = _(u"Место")
        verbose_name_plural = _(u"Место")
        unique_together = ('cemetery', 'area', 'row', 'place',)

    def __unicode__(self):
        return _(u'Кл. %s, уч. %s, ряд %s, место %s') % (self.cemetery, self.area and self.area.name or '', self.row, self.place)

    def burials_available(self):
        q_ex = Q(status=Burial.STATUS_EXHUMATED) | Q(annulated=True)
        return self.burial_set.exclude(q_ex)

    def burial_count(self):
        return self.burials_available().distinct('grave_number').count()

    def get_places_count(self):
        if self.places_count is not None:
            return self.places_count
        elif self.area and self.area.places_count is not None:
            return self.area.places_count
        else:
            return 1

    def get_available_count(self):
        return max(0, self.get_places_count() - self.burial_count())

    def set_next_number(self, **params):
        other_places = Place.objects.filter(**params)
        try:
            self.place = int(other_places.order_by('-place')[0].place) + 1
        except (ValueError, IndexError, TypeError):
            self.place = 1

    def set_next_number_for_year(self, **params):
        year = str(datetime.datetime.now().year)
        other_places = Place.objects.filter(**params)
        other_places = other_places.filter(place__startswith=year)
        try:
            last_num = other_places.order_by('-place')[0].place
            if not last_num.startswith(year):
                last_num = None
            self.place = int(last_num) + 1
        except (ValueError, IndexError, TypeError):
            self.place = year + '0001'

    def remove_responsible(self):
        self.responsible = None
        self.save()

    def get_logs(self):
        ct = ContentType.objects.get_for_model(self)
        return Log.objects.filter(ct=ct, obj_id=self.pk).order_by('-pk')

    def bio_only(self):
        """
        В месте только биоотходы
        """
        burials_available = self.burials_available()
        return burials_available and all([ b.is_bio() for b in burials_available ])

    def save(self, *args, **kwargs):
        if self.cemetery and not self.place:
            if self.cemetery.places_algo == Cemetery.PLACE_MANUAL:
                pass
            elif self.cemetery.places_algo == Cemetery.PLACE_BURIAL_ACCOUNT_NUMBER:
                pass
            elif self.cemetery.places_algo == Cemetery.PLACE_ROW:
                self.set_next_number(cemetery=self.cemetery, area=self.area, row=self.row)
            elif self.cemetery.places_algo == Cemetery.PLACE_AREA:
                self.set_next_number(cemetery=self.cemetery, area=self.area)
            elif self.cemetery.places_algo == Cemetery.PLACE_CEMETERY:
                self.set_next_number(cemetery=self.cemetery)
            elif self.cemetery.places_algo == Cemetery.PLACE_CEM_YEAR:
                self.set_next_number_for_year(cemetery=self.cemetery)
        return super(Place, self).save(*args, **kwargs)

class Burial(models.Model):
    STATUS_BACKED = 'backed'
    STATUS_DECLINED = 'declined'
    STATUS_DRAFT = 'draft'
    STATUS_READY = 'ready'
    STATUS_APPROVED = 'approved'
    STATUS_CLOSED = 'closed'
    STATUS_EXHUMATED = 'exhumated'
    STATUS_CHOICES = (
        (STATUS_BACKED, _(u"Отозвано")),
        (STATUS_DECLINED, _(u"Отклонено")),
        (STATUS_DRAFT, _(u"Черновик")),
        (STATUS_READY, _(u"На согласовании")),
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
    area = models.ForeignKey(Area, verbose_name=_(u"Участок"), blank=True, null=True)
    row = models.CharField(_(u"Ряд"), max_length=255, blank=True, null=True)
    place_number = models.CharField(_(u"Номер места"), max_length=255, null=True, blank=True,
                                    help_text=_(u"Если пусто - номер будет сгенерирован автоматически"))
    grave_number = models.PositiveSmallIntegerField(_(u"Могила"), max_length=255, default=1)
    responsible = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Ответственный"), blank=True, null=True,
                                    related_name='responsible_burials')

    plan_date = models.DateField(_(u"План. дата"), null=True, blank=True)
    plan_time = models.TimeField(_(u"План. время"), null=True, blank=True)
    fact_date = UnclearDateModelField(_(u"Факт. дата"), null=True, blank=True)

    deadman = models.ForeignKey(DeadPerson, verbose_name=_(u"Усопший"), null=True, editable=False)

    applicant = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Заявитель"), blank=True, null=True,
                                  related_name='applied_burials')
    ugh = models.ForeignKey(Org, verbose_name=_(u"УГХ"), null=True, editable=False, related_name='ugh_created',
                            limit_choices_to={'type': Org.PROFILE_UGH}, on_delete=models.PROTECT)
    applicant_organization = models.ForeignKey(Org, verbose_name=_(u"Заявитель-ЮЛ"), null=True, blank=True,
                                               related_name='loru_created', on_delete=models.PROTECT)
    agent_director = models.BooleanField(_(u"Директор-Агент"), default=False, blank=True)
    agent = models.ForeignKey(Profile, verbose_name=_(u"Агент"), null=True, blank=True,
                              limit_choices_to={'is_agent': True}, on_delete=models.PROTECT)
    dover = models.ForeignKey(Dover, verbose_name=_(u"Доверенность"), null=True, blank=True, on_delete=models.PROTECT)

    order = models.OneToOneField('orders.Order', editable=False, null=True)

    status = models.CharField(_(u"Статус"), max_length=255, choices=STATUS_CHOICES, default=STATUS_DRAFT, editable=False)
    changed = models.DateTimeField(_(u"Изменено"), editable=False, null=True)
    changed_by = models.ForeignKey('auth.User', editable=False, null=True, related_name='changed_requests',
                                   on_delete=models.PROTECT)
    annulated = models.BooleanField(_(u"Аннулировано"), default=False, blank=True)

    class Meta:
        verbose_name = _(u"Захоронение")
        verbose_name_plural = _(u"Захоронение")

    def is_edit(self):
        return self.is_draft() or self.is_backed() or self.is_declined()

    def is_draft(self):
        return self.status == self.STATUS_DRAFT

    def is_ready(self):
        return self.status == self.STATUS_READY

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

    def is_bio(self):
        return self.burial_container == self.CONTAINER_BIO

    def can_approve(self):
        if self.is_ugh():
            return False
        elif self.is_full():
            return self.is_ready()
        return False

    def can_finish(self):
        if self.is_full():
            return self.is_approved()
        else:
            return self.is_draft()

    def can_ugh_annulate(self):
        if self.annulated:
            return False
        if self.is_full():
            return self.is_closed() or self.is_exhumated()
        if self.is_ugh_only():
            return self.is_closed() or self.is_draft() or self.is_exhumated()
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
        return self.is_full() and not self.is_edit() and not self.is_finished()

    def can_decline(self):
        return self.is_full() and (self.is_ready() or self.is_approved())

    # условия печати уведомлений для ugh.
    def can_print_notification(self):
        return self.is_approved() or self.is_closed()

    # условия печати уведомлений для loru.
    def can_loru_print_notification(self):
        return self.is_approved()

    # условия печати справок, справки может выдавать лишь УГХ
    def can_print_reference(self):
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
        return self.changed

    def ugh_name(self):
        return self.cemetery and self.cemetery.ugh and self.cemetery.ugh.name or ''

    def loru_name(self):
        return self.applicant_organization and self.applicant_organization.name or ''

    def set_account_number(self, user):
        ugh = self.ugh or user.profile.org
        algo = user.profile.numbers_algo
        cemetery = self.cemetery
        year = str(datetime.datetime.now().year)
        if algo in [Profile.NUM_YEAR_UGH, Profile.NUM_YEAR_CEMETERY]:
            others = Burial.objects.none()
            if algo == Profile.NUM_YEAR_UGH and ugh:
                others = Burial.objects.filter(ugh=ugh)
            elif algo == Profile.NUM_YEAR_CEMETERY and cemetery:
                others = Burial.objects.filter(cemetery=cemetery)

            if self.pk:
                others = others.exclude(pk=self.pk)

            others = others.exclude(account_number__isnull=True).order_by('-account_number')
            try:
                num = others[0].account_number
                if not num.startswith(year):
                    num = None
                self.account_number = int(num) + 1
            except (IndexError, ValueError, TypeError):
                self.account_number = year + '0001'

    def approve(self, user):
        if not self.account_number and not self.is_archive():
            self.set_account_number(user)
            self.save()

    def get_place(self):
        if self.place:
            return self.place

        params = {'cemetery': self.cemetery}
        if self.area:
            params.update({'area': self.area})
        if self.row:
            params.update({'row': self.row})
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

    def get_logs(self):
        ct = ContentType.objects.get_for_model(self)
        return Log.objects.filter(ct=ct, obj_id=self.pk).order_by('-pk')

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
        return self.changed

    def close(self, old_place=None):
        if not self.account_number:
            self.set_account_number(user=self.changed_by)

        if self.cemetery and self.cemetery.places_algo == Cemetery.PLACE_BURIAL_ACCOUNT_NUMBER and not self.place_number:
           self.place_number = self.account_number

        place = self.get_place() or Place(
            places_count=self.area and self.area.places_count or 1,
        )
        if place != old_place:
            if not place.pk or not place.burial_count(): # move TO new
                if old_place and (not old_place.pk or not old_place.burial_count()): # and FROM new
                    place = old_place # edit OLD
                else: # from OLD and POPULATED (or non-existing at all)
                    pass
                place.responsible = self.get_responsible() # update responsible
            else: # move TO existing
                if not old_place or not old_place.pk or not old_place.burial_count(): # and FROM old and populated
                    pass # do not touch anything
                else: # from new
                    # TODO: ответить на вопрос? А сработает ли это когда-нибудь? Без ProtectedError ?
                    #       если в месте есть захоронения, то на него есть ссылки из таблицы Burial.
                    #       Всегда будет ProtectedError.
                    try:
                        old_place.delete() # deleting old
                    except (AttributeError, ProtectedError):
                        pass
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
                # Только так удалишь:
                #    поле Place.responsible: on_delete=models.PROTECT
                responsible = place.responsible
                place.responsible = None
                place.save()
                try:
                    responsible.delete()
                except (AttributeError, ProtectedError):
                    pass
                try:
                    responsible.address.delete()
                except (AttributeError, ProtectedError):
                    pass

        place.cemetery = self.cemetery
        place.area = self.area
        place.row = self.row
        place.place = self.place_number
        place.save()

        if not self.fact_date:
            self.fact_date = self.plan_date

        self.responsible = None
        self.place = place
        self.place_number = place.place
        self.save()
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
    
def burial_file(instance, filename):
    fname = u'.'.join(map(pytils.translit.slugify, filename.rsplit('.', 1)))
    return os.path.join('bfiles', str(instance.burial.pk), fname)

class BurialFiles(models.Model):
    """
    Файлы, связанные с захоронением
    """
    burial = models.ForeignKey(Burial)
    bfile = models.FileField(u"Файл", upload_to=burial_file, blank=True)
    comment = models.CharField(u"Описание", max_length=96, blank=True)
    original_name = models.CharField(max_length=255, editable=False)
    creator = models.ForeignKey('auth.User', verbose_name=_(u"Создатель"), editable=False, null=True,
                                on_delete=models.PROTECT)
    date_of_creation = models.DateTimeField(auto_now_add=True)

    def delete(self):
        if self.bfile != "":
            if os.path.exists(self.bfile.path):
                os.remove(self.bfile.path)
            self.bfile = ""
        super(BurialFiles, self).delete()

class Reason(models.Model):
    TYPE_BACK = 'back'
    TYPE_DECLINE = 'decline'
    TYPE_ANNULATE = 'annulate'
    TYPE_CHOICES = (
        (TYPE_BACK, _(u'Отзыв ЛОРУ')),
        (TYPE_DECLINE, _(u'Отказ УГХ')),
        (TYPE_ANNULATE, _(u'Аннулирование УГХ')),
    )
    name = models.CharField(_(u'Название'), max_length=255)
    reason_type = models.CharField(_(u'Тип'), max_length=255, choices=TYPE_CHOICES)
    text = models.TextField(_(u'Текст'), default='', blank=True)

    class Meta:
        verbose_name = _(u"Причина отказа")
        verbose_name_plural = _(u"Причина отказа")

    def save(self, *args, **kwargs):
        if not self.text.strip():
            self.text = self.name
        return super(Reason, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % self.pk

class ExhumationRequest(models.Model):
    burial = models.OneToOneField(Burial, editable=False)
    place = models.ForeignKey(Place, editable=False, null=True)
    plan_date = models.DateField(_(u"План. дата"), null=True, blank=True)
    plan_time = models.TimeField(_(u"План. время"), null=True, blank=True)
    fact_date = models.DateField(_(u"Факт. дата"), null=True)
    applicant = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Заказчик-ФЛ"), null=True, blank=True)
    applicant_organization = models.ForeignKey(Org, verbose_name=_(u"Заказчик-ЮЛ"), null=True, blank=True)
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
        return super(ExhumationRequest, self).delete(using=using)

def apply_exhumation(instance, created, **kwargs):
    if created:
        instance.apply()

models.signals.post_save.connect(apply_exhumation, sender=ExhumationRequest)
