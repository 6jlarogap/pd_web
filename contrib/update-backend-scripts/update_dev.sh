#! /bin/bash
cd /home/www-data/django/pd_web && \
sudo -u www-data -H git pull && \
sudo chown -R $USER:$USER . && \
sudo -u $USER bower install && \
sudo chown -R www-data:www-data . && \
cd /home/www-data/django/pd_web/pd && \
sudo -u www-data ./manage.py migrate --noinput && \
sudo -u www-data ./manage.py create_burial_views yes && \
sudo -u www-data ./manage.py collectstatic --noinput && \
sudo service apache2 reload
