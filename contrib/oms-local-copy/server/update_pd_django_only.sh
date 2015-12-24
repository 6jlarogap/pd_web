#! /bin/bash
cd /home/www-data/django/pd_web && \
sudo -u www-data -H git pull && \
cd /home/www-data/django/pd_web/pd && \
sudo -u www-data ./manage.py migrate --noinput && \
sudo -u www-data ./manage.py create_burial_views yes || true && \
sudo -u www-data ./manage.py collectstatic --noinput && \
sudo /etc/init.d/apache2 reload

cd /home/chrooted/home/COMMON/django/pd_web && \
sudo -u www-data -H git pull && \
cd /home/chrooted/home/COMMON/django/pd_web/pd && \
sudo -u www-data ./manage.py collectstatic --noinput
