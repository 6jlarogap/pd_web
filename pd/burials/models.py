# coding=utf-8
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

from persons.models import DeadPerson
from users.models import Org, Profile, Dover
from logs.models import Log


class Cemetery(models.Model):
    name = models.CharField(_(u"Название"), max_length=255)
    time_begin = models.TimeField(_(u"Начало работы"))
    time_end = models.TimeField(_(u"Окончание работы"))
    time_slots = models.TextField(_(u"Время для захоронения"), default='',
                                  help_text=_(u'В формате ЧЧ:ММ, по одному на строку'))

    creator = models.ForeignKey('auth.User', verbose_name=_(u"Владелец"), editable=False, null=True,
                                on_delete=models.PROTECT)
    created = models.DateTimeField(_(u"Создано"), auto_now_add=True)
    ugh = models.ForeignKey(Org, verbose_name=_(u"УГХ"), null=True, limit_choices_to={'type': Org.PROFILE_UGH},
                            on_delete=models.PROTECT)

    class Meta:
        verbose_name = _(u"Кладбище")
        verbose_name_plural = _(u"Кладбища")

    def __unicode__(self):
        return self.name

    def get_time_choices(self, date, burial, request):
        others = Burial.objects.none()
        others_loru = Burial.objects.none()
        if date:
            others = Burial.objects.filter(cemetery=self, plan_date=date)
            others_loru = Burial.objects.filter(loru=request.user.profile.org, plan_date=date)
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
    name = models.CharField(_(u"Название"), max_length=255)
    availability = models.CharField(_(u"Открытость"), max_length=32, choices=AVAILABILITY_CHOICES, null=True)
    purpose = models.ForeignKey(AreaPurpose, verbose_name=_(u"Назначение"), null=True, on_delete=models.PROTECT)
    places_count = models.PositiveIntegerField(_(u"Кол-во могил"), default=1)

    class Meta:
        verbose_name = _(u"Участок")
        verbose_name_plural = _(u"Участки")

    def __unicode__(self):
        return _(u'%s (%s, %s, %s могил)') % (
            self.name,
            self.get_availability_display() or _(u"откр.неизв"), self.purpose or _(u"назн. неизв"),
            self.places_count
        )

class Place(models.Model):
    cemetery = models.ForeignKey(Cemetery, verbose_name=_(u"Кладбище"), on_delete=models.PROTECT)
    area = models.ForeignKey(Area, verbose_name=_(u"Участок"), blank=True, null=True)
    row = models.CharField(_(u"Ряд"), max_length=255, blank=True, null=True)
    place = models.CharField(_(u"Место"), max_length=255, blank=True, null=True)
    responsible = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Ответственный"), blank=True, null=True,
                                    on_delete=models.PROTECT)

    class Meta:
        verbose_name = _(u"Место")
        verbose_name_plural = _(u"Место")

    def __unicode__(self):
        return _(u'Кл. %s, уч. %s, ряд %s, место %s') % (self.cemetery, self.area and self.area.name or '', self.row, self.place)

    def save(self, *args, **kwargs):
        if not self.place:
            other_places = Place.objects.filter(cemetery=self.cemetery, area=self.area, row=self.row)
            try:
                self.place = int(other_places.order_by('-place')[0].place) + 1
            except (ValueError, IndexError):
                self.place = 1
        return super(Place, self).save(*args, **kwargs)

class Burial(models.Model):
    STATUS_BACKED = 'backed'
    STATUS_DECLINED = 'declined'
    STATUS_DRAFT = 'draft'
    STATUS_READY = 'ready'
    STATUS_APPROVED = 'approved'
    STATUS_CLOSED = 'closed'
    STATUS_ANNULATED = 'annulated'
    STATUS_CHOICES = (
        (STATUS_BACKED, _(u"Отозвана")),
        (STATUS_DECLINED, _(u"Отклонена")),
        (STATUS_DRAFT, _(u"Черновик")),
        (STATUS_READY, _(u"На согласовании")),
        (STATUS_APPROVED, _(u"Согласована")),
        (STATUS_CLOSED, _(u"Закрыта")),
        (STATUS_ANNULATED, _(u"Аннулирована")),
    )

    BURIAL_TYPES = (
        ('common', _(u'Захоронение')),
        ('additional', _(u'Подзахоронение')),
        ('overlap', _(u'Захоронение в существующую')),
        ('urn', _(u'Урна')),
    )

    NEW_BURIAL_TYPES = ['common', 'urn']

    SOURCE_FULL = 'full'
    SOURCE_UGH = 'ugh'
    SOURCE_ARCHIVE = 'archive'
    SOURCE_TYPES = (
        (SOURCE_FULL, _(u"Полная")),
        (SOURCE_UGH, _(u"Только УГХ")),
        (SOURCE_ARCHIVE, _(u"Архивное")),
    )

    burial_type = models.CharField(_(u"Тип захоронения"), max_length=255, null=True, blank=True, choices=BURIAL_TYPES)
    source_type = models.CharField(_(u"Источник"), max_length=255, null=True, editable=False, choices=SOURCE_TYPES)

    place = models.ForeignKey(Place, verbose_name=_(u"Место"), null=True, blank=True, on_delete=models.PROTECT)
    cemetery = models.ForeignKey(Cemetery, verbose_name=_(u"Кладбище"), null=True, blank=True, on_delete=models.PROTECT)
    area = models.ForeignKey(Area, verbose_name=_(u"Участок"), blank=True, null=True)
    row = models.CharField(_(u"Ряд"), max_length=255, blank=True, null=True)
    place_number = models.CharField(_(u"Номер места"), max_length=255, null=True, blank=True)
    places_type = models.CharField(_(u"Алгоритм заполнения мест"), max_length=255,
                                   choices=Profile.PLACE_TYPES, default=Profile.PLACE_MANUAL)
    responsible = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Ответственный"), blank=True, null=True,
                                    related_name='responsible_burials')

    plan_date = models.DateField(_(u"План. дата"), null=True, blank=True)
    plan_time = models.TimeField(_(u"План. время"), null=True, blank=True)
    fact_date = models.DateField(_(u"Факт. дата"), null=True, blank=True)

    deadman = models.ForeignKey(DeadPerson, verbose_name=_(u"Усопший"), null=True, editable=False)

    applicant = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Заявитель"), blank=True, null=True,
                                  related_name='applied_burials')
    ugh = models.ForeignKey(Org, verbose_name=_(u"ЛОРУ"), null=True, editable=False, related_name='ugh_created',
                            limit_choices_to={'type': Org.PROFILE_UGH}, on_delete=models.PROTECT)
    loru = models.ForeignKey(Org, verbose_name=_(u"ЛОРУ"), null=True, blank=True, related_name='loru_created',
                             limit_choices_to={'type': Org.PROFILE_LORU}, on_delete=models.PROTECT)
    agent = models.ForeignKey(Profile, verbose_name=_(u"Агент"), null=True, blank=True,
                              limit_choices_to={'is_agent': True}, on_delete=models.PROTECT)
    agent_director = models.BooleanField(_(u"Агент-директор"), default=False, blank=True)
    dover = models.ForeignKey(Dover, verbose_name=_(u"Доверенность"), null=True, blank=True, on_delete=models.PROTECT)

    status = models.CharField(_(u"Статус"), max_length=255, choices=STATUS_CHOICES, default=STATUS_DRAFT, editable=False)
    changed = models.DateTimeField(_(u"Изменено"), editable=False, null=True)
    changed_by = models.ForeignKey('auth.User', editable=False, null=True, related_name='changed_requests',
                                   on_delete=models.PROTECT)

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
        return self.status == self.STATUS_ANNULATED

    def is_finished(self):
        return self.is_closed() or self.is_annulated()

    def is_ugh_only(self):
        return self.source_type == self.SOURCE_UGH

    def is_full(self):
        return self.source_type == self.SOURCE_FULL

    def is_archive(self):
        return self.source_type == self.SOURCE_ARCHIVE

    def is_ugh(self):
        return self.is_ugh_only() or self.is_archive()

    def can_approve(self):
        if self.is_archive():
            return False
        elif self.is_full():
            return self.is_ready()
        else:
            return self.is_draft()

    def can_finish(self):
        if self.is_archive():
            return self.is_draft()
        else:
            return self.is_approved()

    def can_annulate(self):
        return self.can_finish() and not self.is_archive()

    def can_back(self):
        return self.is_full() and not self.is_edit() and not self.is_finished()

    def can_decline(self):
        return self.is_full() and self.is_ready()

    @property
    def status_str(self):
        return self.get_status_display()

    @property
    def status_dt(self):
        return self.changed

    def ugh_name(self):
        return self.cemetery and self.cemetery.ugh and self.cemetery.ugh.name or ''

    def loru_name(self):
        return self.loru and self.loru.name or ''

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

    def close(self):
        place = self.get_place() or Place(
            cemetery=self.cemetery,
            area=self.area,
            row=self.row,
            place=self.place_number,
        )
        place.responsible = self.get_responsible()
        place.save()
        self.place = place
        self.save()
        return self

    def __unicode__(self):
        return u'%s' % self.pk

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
