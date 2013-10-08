# -*- coding: utf-8 -*-

#   user_projects_conf.py

#   Конфигурационный файл для user_projects_.py, обновления кода и 
#   миграции данных (если необходимо) проектов различных разработчиков

# ---------------------------------------------------------------------------

PROJECTS = ( 
            ('/home/www-data/django/pd_web_2/pd',      # manage.py && git
             '/home/www-data/django/pd_web_2/ENV',     # virtual_env
            ),
            ('/home/www-data/django/pd2_sk123/pd',     # manage.py && git
             '/home/www-data/django/pd2_sk123/ENV',    # virtual_env
            ),
           )

# Дополнительные команды, выполняемые после активизации нового кода,
# миграции... В это время мы находимя в каталоге, где ./manage.py
#
# NB!
#   Смысл этих команд един для любого сервера,
#   но конкретное содержание может отличаться

OTHER_COMMANDS = (
                    # Web Server Apache исполняется пользователем
                    #     www-data из группы www-data:
                    #
                    'sudo chmod -R g+w .',
                    #
                    # Пользователь из группы www-data может создавать 
                    # новые файлы *.pyc, и заменять имеющиеся *.pyc:
                    #
                    'find . -type d | sudo xargs sudo chmod g+rwx',
                    'sudo chgrp -R www-data .',
                 )
# ---------------------------------------------------------------------------

MANAGE_PY, VENV = 0, 1                      # индексы в списках PROJECTS

ALREADY_UP_TO_DATE = 'Already up-to-date.'  # если такое будет, значит ничего
                                            # нового в git

APACHE2_RELOAD = 'sudo /etc/init.d/apache2 reload'
# ---------------------------------------------------------------------------
