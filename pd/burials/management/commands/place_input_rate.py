# -*- coding: utf-8 -*-

# burial_input_rate.py
# ------------------

# Замер производительности при вводе мест 

# Запуск: : ./manage.py place_input_rate username from_time to_time
#
#       from_time, to_time  - с какого по какое время,
#                             в формате YYYY-MM-DDTHH:MM,
#                             например 2015-02-26T16:00
#
# Результат: csv вывод в output_file

import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from burials.models import Place
from logs.models import Log

TEMPLATE_DATE_TIME = '%Y-%m-%dT%H:%M'

OUTPUT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class Command(BaseCommand):
    args = 'username, from_time (%s), to_time (%s), output_file' % (
        TEMPLATE_DATE_TIME,
        TEMPLATE_DATE_TIME
    )
    help = "print user burial input rate from from_time to to_time to output_file"

    def trunc_msec(self, d):
        """
        Округлить datetime до секунд
        """
        dt = datetime.datetime(
            year=d.year, month=d.month, day=d.day,
            hour=d.hour, minute=d.minute, second=d.second,
        )
        if d.microsecond > 500000:
            dt += datetime.timedelta(seconds=1)
        return dt

    def handle(self, *args, **options):
        if len(args) < 4:
            print "ERROR! Not all the parms given. Type --help to get help"
            quit()
        username = args[0].decode("utf-8")
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            print u"ERROR! User %s not found" % username
            quit()
        from_time = args[1].decode("utf-8")
        to_time = args[2].decode("utf-8")
        try:
            from_time = datetime.datetime.strptime(from_time, TEMPLATE_DATE_TIME)
            to_time = datetime.datetime.strptime(to_time, TEMPLATE_DATE_TIME)
        except ValueError:
            print 'ERROR! Invalid from_time or/and to_time. Type --help to get help'
            quit()
        if from_time > to_time:
            print 'ERROR! From_time > to_time. Type --help to get help'
            quit()
        output_file = args[3].decode("utf-8")
        f = open(output_file, 'w')

        ct = ContentType.objects.get(app_label="burials", model="place")
        previous = None
        for p in Place.objects.filter(
                 is_invent=True,
                 dt_created__gte=from_time,
                 dt_created__lte=to_time,
                 ).distinct().order_by('dt_created'):
            
            try:
                logrec = Log.objects.get(
                    ct=ct,
                    obj_id=int(p.pk),
                    user=user,
                    msg=u"Место '%s' создано через мобильное приложение" % p.place
                )
            except Log.DoesNotExist:
                continue

            if previous is None:
                previous = self.trunc_msec(p.dt_created)
                continue
            current = self.trunc_msec(p.dt_created)

            f.write("%s,%s,%10d\n" % (
                previous.strftime(OUTPUT_TIME_FORMAT),
                current.strftime(OUTPUT_TIME_FORMAT),
                int(round((current-previous).total_seconds())),
        ))
            
            previous = current
        f.close()
