#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   backup_psql.py
#   --------------
#   Параметры конфигурации:
#       Переменные ПРОПИСНЫМИ буквами. Импортируются
#       из backup_psql_conf.py, в каталоге запуска сценария
#       или в /usr/local/etc
#
#   Назначение:
#       *   Резервное копирование psql баз данных:
#           - сегодняшнее (today):
#               Производится при любом запуске сценария, например,
#               планировщиком задач (crontab).
#               Туда попопадают все дампы, созданные за последние 24 ч.
#               Дампы старше суток удаляются.
#           -  ежедневное (daily):
#               Там по одному дампу в день, но не старше недели.
#           -  еженедельное (weekly):
#               Там по одному дампу в неделю, но не старше месяца.
#           -  ежемесячное (monthly):
#               Там по одному дампу в месяц, но не старше MONTHS*30 дней.
#           Дампы производятся в gzip- упакованные файлы
#           с именами db-YYYYMMDDhhmmss.pg.gz, где:
#               - db:   имя б.д;
#               - YYYYMMDDhhmmss - дата, время начала процесса дампа
#
#       *   Сегодняшние дампы можно использовать для репликации
#           этих б.д на другой сервер.
#           Для большей надежности этой репликации перед формированием
#           сегодняшних дампов создается LOCK_FILE, потом удаляется.
#           Если параметр LOCK_FILE не задан, т.е. None, False и т.п.,
#           то LOCK_FILE не создается.

import sys, os, datetime

conf_dir = '/usr/local/etc'
if conf_dir not in sys.path:
    sys.path.append(conf_dir)
from backup_psql_conf import *

# Чтоб все пути были каталогами, существовали и завершались '/'
for parm in ('BACKUP_PATH', 'TODAY_PATH', 'DAILY_PATH', 'WEEKLY_PATH', 'MONTHLY_PATH', ):
    if not globals()[parm].endswith('/'):
        globals()[parm] += '/'
    if parm != 'BACKUP_PATH':
        globals()[parm] = BACKUP_PATH + globals()[parm]
    if not os.path.isdir(globals()[parm]):
        print "Failed to find folder: %s" % globals()[parm]
        exit(1)

db_dump_ext = '.pg.gz'
datetime_format = '%Y%m%d%H%M%S'

def backup(db_name, dst_dir):
    now_str = datetime.datetime.now().strftime(datetime_format)
    dst_f_name = '%s%s-%s%s' % (dst_dir, db_name, now_str, db_dump_ext)
    rc = os.system('pg_dump -U postgres %s | gzip > %s' % (db_name, dst_f_name))
    if rc:
        print "Failed to create the db '%s' backup" % db_name
        exit(1)

def delta_datetime(fname):
    fname_datetime_str = fname.split('-')[-1].split('.')[0]
    return datetime.datetime.now() - datetime.datetime.strptime(fname_datetime_str, datetime_format)

# today backups
if LOCK_FILE:
    lock_file = open(TODAY_PATH + LOCK_FILE, 'w')
    lock_file.close()

one_day = datetime.timedelta(days=1)
for fname in os.listdir(TODAY_PATH):
    if fname.endswith(db_dump_ext) and delta_datetime(fname) >= one_day:
        os.remove(TODAY_PATH + fname)

for db in DATABASES:
    backup(db, TODAY_PATH)

if LOCK_FILE:
    os.remove(TODAY_PATH + LOCK_FILE)

max_delta = datetime.timedelta.max

# daily backups
one_week = datetime.timedelta(days=7)
for db in DATABASES:
    min_delta = max_delta
    for fname in os.listdir(DAILY_PATH):
        if fname.startswith(db + '-'):
            delta = delta_datetime(fname)
            min_delta = min(delta, min_delta)
            if delta >= one_week:
                os.remove(DAILY_PATH + fname)
    if min_delta >= one_day:
        backup(db, DAILY_PATH)

# weekly backups
one_month = datetime.timedelta(days=30)
for db in DATABASES:
    min_delta = max_delta
    for fname in os.listdir(WEEKLY_PATH):
        if fname.startswith(db + '-'):
            delta = delta_datetime(fname)
            min_delta = min(delta, min_delta)
            if delta >= one_month:
                os.remove(WEEKLY_PATH + fname)
    if min_delta >= one_week:
        backup(db, WEEKLY_PATH)

# monthly backups
max_month = datetime.timedelta(days=MONTHS*30)
for db in DATABASES:
    min_delta = max_delta
    for fname in os.listdir(MONTHLY_PATH):
        if fname.startswith(db + '-'):
            delta = delta_datetime(fname)
            min_delta = min(delta, min_delta)
            if delta >= max_month:
                os.remove(MONTHLY_PATH + fname)
    if min_delta >= one_month:
        backup(db, MONTHLY_PATH)

exit(0)
