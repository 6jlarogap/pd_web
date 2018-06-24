# -*- coding: utf-8 -*-

#   user_projects_conf.py

#   Конфигурационный файл для user_projects_.py, обновления кода и 
#   миграции данных (если необходимо) проектов различных разработчиков

# ---------------------------------------------------------------------------

PROJECTS = ( 
            # Где находится ./manage.py
            '/home/www-data/django/pd_prod/pd',
            '/home/www-data/django/pd_web/pd',
           )

# ---------------------------------------------------------------------------

MANAGE_PY, VENV = 0, 1                      # индексы в списках PROJECTS

ALREADY_UP_TO_DATE = 'Already up-to-date.'  # если такое будет, значит ничего
                                            # нового в git

APACHE2_RELOAD = 'sudo /home/soul/users_projects/apache-reload.sh'
    # 'sudo /etc/init.d/apache2 reload'

APACHE2_USER = 'www-data'

# ---------------------------------------------------------------------------
