#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#   restore_replicate.py
#   -------------------
#
#   Восстановление на резервном сервере
#   баз данных, получаемых с основного сервера по Rsync
#
#   Параметры (переменные ПРОПИСНЫМИ буквами) импортируются из
#   restore_replicate_conf.py, в каталоге запуска сценария или в /usr/local/etc
#
#   - работаем в каталоге BACKUP_PATH
#   - запоминаем его содержимое.
#   - в каталог BACKUP_PATH копируем по rsync содержимое аналогичного
#   - каталога на основном сервере. Там должны быть дампы
#       * имя дампа: db-YYYYMMDDhhmmss.pg.gz, db - имя б.д.,
#       * в которую и будем восстанавливать
#     но может быть и lock_file. Если есть lock_file, то ждем
#     10 сек, далее повторяем rsync, если обнаружился lock_file,
#     еще 10 сек, но не более 5 мин.
#     сравниваем содержимое с тем, что ранее запомнили. Если
#     отличается выполняем восстановление.
#   - восстанавливаем из последнего файла для каждой б.д

import os, sys, time, re
import datetime

conf_dir = '/usr/local/etc'
if conf_dir not in sys.path:
    sys.path.append(conf_dir)
from restore_replicate_conf import *

def scram(message=None, rc=1):
    if message:
        print message
        # TODO: письмо
        exit(rc)

if not BACKUP_PATH.endswith('/'):
    BACKUP_PATH += '/'
if not os.path.isdir(BACKUP_PATH):
    scram("Failed to find backup folder: %s" % BACKUP_PATH)

db_dump_ext = '.pg.gz'
lock_file = BACKUP_PATH + 'this.lock'
wait_if_locked = 10
                                        # sec
stop_waiting = 30 * wait_if_locked

old_listdir = os.listdir(BACKUP_PATH)
waiting = 0
stopped_waiting = False
while True:
    rc = os.system('rsync -rltupv --delete %s %s' % (RSYNC_SENDER, BACKUP_PATH, ))
    if rc:
        scram("Failed to rsync '%s' into '%s' herein" % (RSYNC_SENDER, BACKUP_PATH, ))

    listdir = os.listdir(BACKUP_PATH)
    if lock_file not in listdir:
        break
    if waiting >= stop_waiting:
        stopped_waiting = True
        break
    time.sleep(wait_if_locked)
    waiting += wait_if_locked

if stopped_waiting:
    scram("Stopped waiting till the backup folder is locked at the sender")

if not listdir:
    print 'No dump files from the original server received. Nothing to do now'
    exit(0)
if not (set(listdir) - set(old_listdir)):
    print 'No changes against previous restore noticed. Nothing to do now'
    exit(0)

# нужен последний дамп для каждой базы из всех файлов
db_fname = {}
for db in DATABASES:
    db_fname[db] = ''
for fname in listdir:
    if '-' not in fname:
        scram("Illegal file '%s' in the backup folder" % fname)
    db = fname[:fname.index('-')]
    if db not in DATABASES:
        continue
    if db_fname[db] < fname:
        db_fname[db] = fname

for db, fname in db_fname.items():
    if not fname:
         print "WARNING: no dump file for '%s' database found" % db
         continue
    commands = ('dropdb -U postgres %s' % db,
                'createdb -U postgres %s' % db,
                'zcat %s | psql -U postgres %s' % (BACKUP_PATH + fname, db, ),
    )
    for command in commands:
        rc = os.system(command)
        if rc:
            scram("Failed to execute command '%s', rc=%s" % (command, rc, ))

print 'Success!'
exit(0)
