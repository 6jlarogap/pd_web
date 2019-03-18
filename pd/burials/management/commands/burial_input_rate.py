# -*- coding: utf-8 -*-

# burial_input_rate.py
# ------------------

# Замер производительности при вводе захоронений

# Запуск: : ./manage.py burial_input_rate username from_time to_time output_file
#
#       from_time, to_time  - с какого по какое время,
#                             в формате YYYY-MM-DDTHH:MM,
#                             например 2015-02-26T16:00
#
# Результат: csv вывод в output_file

import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from burials.models import Burial

TEMPLATE_DATE_TIME = '%Y-%m-%dT%H:%M'
TEMPLATE_DATE_TIME_HELP = TEMPLATE_DATE_TIME.replace('%', '%%')

OUTPUT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class Command(BaseCommand):
    help = "print user invent place input rate from from_time to to_time to output_file"

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='username')
        parser.add_argument('from_time', type=str, help='from_time (%s)' % TEMPLATE_DATE_TIME_HELP)
        parser.add_argument('to_time', type=str, help='to_time (%s)' % TEMPLATE_DATE_TIME_HELP)
        parser.add_argument('output_file', type=str, help='output_time')

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

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        from_time = kwargs['from_time']
        to_time = kwargs['to_time']
        output_file = kwargs['output_file']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            print("ERROR! User %s not found" % username)
            quit()
        try:
            from_time = datetime.datetime.strptime(from_time, TEMPLATE_DATE_TIME)
            to_time = datetime.datetime.strptime(to_time, TEMPLATE_DATE_TIME)
        except ValueError:
            print('ERROR! Invalid from_time or/and to_time. Type --help to get help')
            quit()
        if from_time > to_time:
            print('ERROR! From_time > to_time. Type --help to get help')
            quit()
        f = open(output_file, 'w')

        previous = None
        for b in Burial.objects.filter(
                 changed_by=user,
                 dt_created__gte=from_time,
                 dt_created__lte=to_time,
                 ).distinct().order_by('dt_created'):

            if previous is None:
                previous = self.trunc_msec(b.dt_created)
                continue
            current = self.trunc_msec(b.dt_created)

            f.write("%s,%s,%10d\n" % (
                previous.strftime(OUTPUT_TIME_FORMAT),
                current.strftime(OUTPUT_TIME_FORMAT),
                int(round((current-previous).total_seconds()))
        ))
            
            previous = current
        f.close()
