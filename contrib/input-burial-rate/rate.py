# coding=utf-8
#
# rate.py,
#
# Замерить производительность ввода звхоронений по фотографиям
#
# Запуск из ./manage.py shell :
#  execfile('../contrib/input-burial-rate/rate.py')

import datetime

from burials.models import Burial

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def main():
    
    diffs = list()
    previous = None
    for b in Burial.objects.filter(changed_by__username=u'korol').order_by('dt_created'):

        if previous is None:
            previous = trunc_msec(b.dt_created)
            continue
        current = trunc_msec(b.dt_created)

        print "%s,%s,%10d" % (
            previous.strftime(TIME_FORMAT),
            current.strftime(TIME_FORMAT),
            int(round((current-previous).total_seconds()))
       )
        
        previous = current

def trunc_msec(d):
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

main()
