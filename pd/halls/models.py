import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

class Hall(models.Model):

    HALL_INTERVAL_CHOICES = (
        (10, "10",),
        (15, "15",),
        (20, "20",),
        (30, "30",),
        (60, "60",),
    )

    org = models.ForeignKey('users.Org', verbose_name=_("Организация"), on_delete=models.CASCADE)
    title =  models.CharField(_("Название зала"), max_length=255, blank=True)
    
    # Здесь для времен просто символьные поля. Будет проверять их вручную,
    # чтоб можно было игнорировать удаляемые объекты с неверно заданным,
    # например, пустым временем. Аналогично blank=true. Сами будем проверять.
    #
    time_start = models.CharField(_("Начало работы"), max_length=255, blank=True)
    time_end = models.CharField(_("Окончание работы"), max_length=255, blank=True)

    interval = models.PositiveIntegerField(_("Минимальное время, минуты"), choices=HALL_INTERVAL_CHOICES, default=30)
    is_active = models.BooleanField(_("Действующий"), default=True)

    class Meta:
        verbose_name = _('Зал')
        verbose_name_plural = _('Залы')
        unique_together = ('org', 'title', )
        ordering = ('org', 'title', )

    def __str__(self):
        return self.title

class HallTimeTable(models.Model):
    hall = models.ForeignKey(Hall, verbose_name=_("Зал"), on_delete=models.CASCADE)
    dt_start = models.DateTimeField(_("Время начала"))
    dt_end = models.DateTimeField(_("Время окончания"))
    creator = models.ForeignKey('auth.User', verbose_name=_("Сотрудник"), on_delete=models.CASCADE)
    details =  models.TextField(_("Примечания"), blank=True)
    dt_created = models.DateTimeField(_("Дата/время создания"), auto_now_add=True)

    class Meta:
        verbose_name = _('Назначенное время в зале')
        verbose_name_plural = _('Расписание залов')
        unique_together = ('hall', 'dt_start', 'dt_end', )

    def __str__(self):
        return "%s, %s, %s - %s" % (
            datetime.datetime.strftime(self.dt_start, "%d.%m.%y"),
            self.hall,
            datetime.datetime.strftime(self.dt_start, "%H:%M"),
            datetime.datetime.strftime(self.dt_end, "%H:%M"),
        )
