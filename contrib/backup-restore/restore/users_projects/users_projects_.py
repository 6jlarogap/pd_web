#! /usr/bin/env python
# -*- coding: utf-8 -*-

#   user_projects_.py

#   Просмотреть git- каталоги различных пользователей проекта,
#   если появилось что-то новое, то в соответствующем проекте
#   выполнить необходимое для обновления кода и данных
#
#   Использует конфигурационный файл user_projects_conf.py
#   (переменные ЗАГЛАВНЫМИ буквами)
#
# Требования:
# * Пароли:
#   - git:  сценарий считывает данные из git репозитариев.
#           Должна быть настройка, чтобы пароли git репозитариев
#           не запрашивались
#   - sudo: сценарий перезапускает apache
#           Должна быть настройка, чтобы пользователь,
#           под которым работает сценарий, мог выполнять
#           suso без пароля
# * Права на файлы и каталоги:
#   -   Файлы в каталогах проекта и там, где статические
#       файлы, должны быть доступны пользователю,
#       исполняющему apache web server, в т.ч.
#       по записи. "По записи" не требуется
#       в "классическом" django, но при использовании
#       assets обязательно (по крайней мере static)

import os, subprocess

from users_projects_conf import *

def main():
    for project in PROJECTS:
        print '\nChecking %s ...' % project[MANAGE_PY]
        os.chdir(project[MANAGE_PY])
        outp = do_cmd('sudo -u %s -H git pull' % (APACHE2_USER, ))
        if ALREADY_UP_TO_DATE in outp:
            continue
        else:
            do_cmd('sudo -u %s %s/bin/python ./manage.py migrate --noinput' % 
                    (APACHE2_USER, project[VENV]), )
            do_cmd('sudo -u %s %s/bin/python ./manage.py collectstatic --noinput' % 
                    (APACHE2_USER, project[VENV]), )
            do_cmd(APACHE2_RELOAD)

def do_cmd(cmd):
    outp = subprocess.check_output(cmd,
                                   stderr=subprocess.STDOUT,
                                   shell=True)
    print '> %s\n%s' % (cmd, outp,)
    return outp

main()
