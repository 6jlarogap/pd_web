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
#       Должна быть настройка, чтобы пользователь,
#       под которым работает сценарий, мог выполнять
#       операции над файлами и каталогами, например,
#       manage.py collectstatic, без проблем

import os, subprocess

from users_projects_conf import *

def main():
    for project in PROJECTS:
        print '\nChecking %s ...' % project[MANAGE_PY]
        os.chdir(project[MANAGE_PY])
        outp = do_cmd('git pull')
        if ALREADY_UP_TO_DATE in outp:
            continue
        else:
            do_cmd('%s/bin/python ./manage.py migrate --noinput' % 
                    project[VENV])
            do_cmd('%s/bin/python ./manage.py collectstatic --noinput' % 
                    project[VENV])
            do_cmd(APACHE2_RELOAD)

def do_cmd(cmd):
    outp = subprocess.check_output(cmd,
                                   stderr=subprocess.STDOUT,
                                   shell=True)
    print '> %s\n%s' % (cmd, outp,)
    return outp

main()
