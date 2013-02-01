# coding=utf-8
from django.db import models
from django.utils.translation import ugettext_lazy as _
from users.models import Org


class Cemetery(models.Model):
    name = models.CharField(_(u"Название"), max_length=255)
    time_begin = models.TimeField(_(u"Начало работы"))
    time_end = models.TimeField(_(u"Окончание работы"))
    period = models.PositiveSmallIntegerField(_(u"Длительность захоронения"), default=15)

    creator = models.ForeignKey('auth.User', verbose_name=_(u"Владелец"), editable=False, null=True)
    created = models.DateTimeField(_(u"Создано"), auto_now_add=True)
    ugh = models.ForeignKey(Org, verbose_name=_(u"УГХ"), null=True, limit_choices_to={'type': Org.PROFILE_UGH})

    class Meta:
        verbose_name = _(u"Кладбище")
        verbose_name_plural = _(u"Кладбища")

    def __unicode__(self):
        return self.name

class BurialRequest(models.Model):
    STATUS_DICT = {
        0: _(u"Черновик"),
        1: _(u"На согласовании"),
        2: _(u"Одобрена"),
        3: _(u"Выполнена"),
        4: _(u"Закрыта"),
    }

    plan_date = models.DateField(_(u"План. дата"), null=True, blank=True)
    plan_time = models.TimeField(_(u"План. время"), null=True, blank=True)

    cemetery = models.ForeignKey(Cemetery, verbose_name=_(u"Кладбище"), null=True)
    place_number = models.CharField(_(u"Номер места"), max_length=255, null=True, blank=True)

    creator = models.ForeignKey('auth.User', verbose_name=_(u"Владелец"), editable=False, null=True)
    created = models.DateTimeField(_(u"Создано"), auto_now_add=True)
    loru = models.ForeignKey(Org, verbose_name=_(u"ЛОРУ"), null=True, limit_choices_to={'type': Org.PROFILE_LORU})

    ready_loru = models.DateTimeField(_(u"Готово к согласованию"), editable=False, null=True)
    approved_ugh = models.DateTimeField(_(u"Согласовано УГХ"), editable=False, null=True)
    processed_loru = models.DateTimeField(_(u"Выполнено ЛОРУ"), editable=False, null=True)
    completed_ugh = models.DateTimeField(_(u"Закрыто УГХ"), editable=False, null=True)

    class Meta:
        verbose_name = _(u"Заявка на захоронение")
        verbose_name_plural = _(u"Заявки на захоронение")

    @property
    def status(self):
        flags = [self.ready_loru, self.approved_ugh, self.processed_loru, self.completed_ugh]
        cnt = len(filter(lambda f: f, flags))
        return self.STATUS_DICT[cnt]

    def ugh_names(self):
        return self.cemetery.ugh and self.cemetery.ugh.name or ''

    def loru_name(self):
        return self.loru and self.loru.name or ''

    def __unicode__(self):
        return u'%s' % self.pk

