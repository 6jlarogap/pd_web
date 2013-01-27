# coding=utf-8
from django.db import models

class Cemetery(models.Model):
    name = models.CharField(u"Название", max_length=255)
    time_begin = models.TimeField(u"Начало работы")
    time_end = models.TimeField(u"Окончание работы")
    time_period = models.PositiveSmallIntegerField(u"Длительность захоронения", default=15)

    creator = models.ForeignKey('auth.User', verbose_name=u"Владелец", editable=False, null=True)
    created = models.DateTimeField(u"Создано", auto_now_add=True)

    class Meta:
        verbose_name = u"Кладбище"
        verbose_name_plural = u"Кладбища"

    def __unicode__(self):
        return self.name

class BurialRequest(models.Model):
    number = models.CharField(u"Номер", max_length=255)
    plan_date = models.DateField(u"План. дата")
    plan_time = models.TimeField(u"План. время")

    cemetery = models.ForeignKey(Cemetery, verbose_name=u"Кладбище")
    place_number = models.CharField(u"Номер места", max_length=255, null=True, blank=True)

    creator = models.ForeignKey('auth.User', verbose_name=u"Владелец", editable=False, null=True)
    created = models.DateTimeField(u"Создано", auto_now_add=True)

    approved_ugh = models.DateTimeField(u"Согласовано УГХ", editable=False, null=True)
    processed_loru = models.DateTimeField(u"Выполнено ЛОРУ", editable=False, null=True)
    completed_ugh = models.DateTimeField(u"Закрыто УГХ", editable=False, null=True)

    class Meta:
        verbose_name = u"Заявка на захоронение"
        verbose_name_plural = u"Заявки на захоронение"



