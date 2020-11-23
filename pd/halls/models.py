import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from logs.models import Log

class Hall(models.Model):

    org = models.ForeignKey('users.Org', verbose_name=_("Организация"), on_delete=models.CASCADE)
    title =  models.CharField(_("Название зала"), max_length=255, blank=True)
    
    is_active = models.BooleanField(_("Действующий"), default=True)

    class Meta:
        verbose_name = _('Зал')
        verbose_name_plural = _('Залы')
        unique_together = ('org', 'title', )
        ordering = ('org', 'title', )

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        self.halltimetable_set.all().delete()
        self.hallweekly_set.all().delete()
        ct = ContentType.objects.get_for_model(self)
        Log.objects.filter(ct=ct, obj_id=self.pk).delete()
        super(Hall, self).delete(*args, **kwargs)

    def time_schedule(self):
        "Расписание зала типа: Пн: 09-16/30; Вт: 09-16/30 ..."
        
        result = ''
        if self.pk:
            # Все ли времена одинаковы
            count = 7
            is_equal = True
            is_first = True
            for hw in self.hallweekly_set.all().order_by('dow'):
                if is_first:
                    time_start = hw.time_start
                    time_end = hw.time_end
                    interval = hw.interval
                    is_dayoff = hw.is_dayoff
                    is_first = False
                count -= 1
                if is_equal:
                    if time_start != hw.time_start or time_end != hw.time_end or \
                       interval != hw.interval     or is_dayoff != hw.is_dayoff:
                        is_equal = False
                if hw.is_dayoff:
                    result += _("%s: не работает; ") % (
                        HallWeekly.HALL_DAYS_OF_WEEK_SHORT_DICT[hw.dow],
                    )
                else:
                    result += '%s: %s-%s/%s; ' % (
                        HallWeekly.HALL_DAYS_OF_WEEK_SHORT_DICT[hw.dow],
                        hw.time_start,
                        hw.time_end,
                        hw.interval,
                    )
            if is_equal and count != 0:
                is_equal = False
            if is_equal:
                if is_dayoff:
                    result = _("Всю неделю: не работает")
                else:
                    result = _("Всю неделю: : %(time_start)s - %(time_end)s / %(interval)s") % dict(
                        time_start=time_start,
                        time_end=time_end,
                        interval=interval,
                    )
            result = result.rstrip()
            result = result.rstrip(';')
        else:
            result = ("Всю неделю: : %(time_start)s - %(time_end)s / %(interval)s") % dict(
                time_start=HallWeekly.HALL_DEFAULT_TIME_START,
                time_end=HallWeekly.HALL_DEFAULT_TIME_END,
                interval=HallWeekly.HALL_DEFAULT_INTERVAL,
            )
        return result

class HallWeekly(models.Model):

    HALL_INTERVAL_CHOICES = (
        (10,  _("10 мин."),),
        (15,  _("15 мин."),),
        (20,  _("20 мин."),),
        (30,  _("30 мин."),),
        (40,  _("40 мин."),),
        (60,  _("час"),    ),
        (120, _("2 часа"), ),
    )

    HALL_DAYS_OF_WEEK_LONG_CHOICES = (
        (1, _("Понедельник"),),
        (2, _("Вторник"),),
        (3, _("Среда"),),
        (4, _("Четверг"),),
        (5, _("Пятница"),),
        (6, _("Суббота"),),
        (7, _("Воскресенье"),),
    )

    HALL_DAYS_OF_WEEK_SHORT_CHOICES = (
        (1, _("Пн"),),
        (2, _("Вт"),),
        (3, _("Ср"),),
        (4, _("Чт"),),
        (5, _("Пт"),),
        (6, _("Сб"),),
        (7, _("Вс"),),
    )

    HALL_DAYS_OF_WEEK_SHORT_DICT = {
        1: _("Пн"),
        2: _("Вт"),
        3: _("Ср"),
        4: _("Чт"),
        5: _("Пт"),
        6: _("Сб"),
        7: _("Вс"),
    }

    HALL_DEFAULT_TIME_START = '08:00'
    HALL_DEFAULT_TIME_END   = '17:00'
    HALL_DEFAULT_INTERVAL   = 60

    hall = models.ForeignKey(Hall, verbose_name=_("Зал"), on_delete=models.CASCADE)
    dow = models.PositiveIntegerField(_("День"), choices=HALL_DAYS_OF_WEEK_LONG_CHOICES, default=1)

    # Здесь для времен просто символьные поля. Будет проверять их вручную,
    # чтоб можно было игнорировать удаляемые объекты с неверно заданным,
    # например, пустым временем. Аналогично blank=true. Сами будем проверять.
    # Кроме того, возможно время 24:00.
    #
    time_start = models.CharField(_("Начало"), max_length=255, blank=True)
    time_end = models.CharField(_("Окончание"), max_length=255, blank=True)

    interval = models.PositiveIntegerField(_("Время"), choices=HALL_INTERVAL_CHOICES, default=30)
    is_dayoff = models.BooleanField(_("Выходной"), default=False)

    class Meta:
        verbose_name = _('День недели в зале')
        verbose_name_plural = _('Дни недели в залах')
        unique_together = ('hall', 'dow', )
        ordering = ('hall', 'dow', )

    def __str__(self):
        if self.is_dayoff:
            return _("%(hall)s, %(dow)s, выходной") % dict(
                hall=self.hall.title,
                dow=self.HALL_DAYS_OF_WEEK_SHORT_DICT[self.dow],
            )
        else:
            return "%s, %s, %s-%s/%s" % (
                self.hall,
                self.HALL_DAYS_OF_WEEK_SHORT_DICT[self.dow],
                self.time_start,
                self.time_end,
                self.interval,
            )

    @classmethod
    def get_defaults(cls):
        result = []
        for dow in (1, 2, 3, 4, 5, 6, 7):
            result.append(dict(
              dow=dow,
              time_start=cls.HALL_DEFAULT_TIME_START,
              time_end=cls.HALL_DEFAULT_TIME_END,
              interval=cls.HALL_DEFAULT_INTERVAL,
              is_dayoff=False,
            ))
        return result

class HallTimeTable(models.Model):

    # Из зала прощания может быть или сразу кремация,
    # или могут вывозить для захоронения
    #
    BOOK_BURN = 'burn'
    BOOK_MOVE = 'move'

    BOOK_CHOICES = (
        (BOOK_BURN, _('Кремация')),
        (BOOK_MOVE, _('Вывоз на захоронение')),
    )

    hall = models.ForeignKey(Hall, verbose_name=_("Зал"), on_delete=models.CASCADE)
    dt_start = models.DateTimeField(_("Время начала"))
    dt_end = models.DateTimeField(_("Время окончания"))
    creator = models.ForeignKey('auth.User', verbose_name=_("Сотрудник"), on_delete=models.CASCADE)
    details =  models.TextField(_("Примечания"), blank=True)
    dt_created = models.DateTimeField(_("Дата/время создания"), auto_now_add=True)
    kind = models.CharField(_("Тип"), max_length=10, choices=BOOK_CHOICES, default=BOOK_BURN)

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
