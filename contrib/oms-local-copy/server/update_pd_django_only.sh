#! /bin/bash
PROJECT_='/home/www-data/django/pd_web'

TTY_=`tty`
cd "$PROJECT_/pd"
sudo -u www-data -H git pull
sudo -u www-data ./manage.py migrate --noinput
sudo -u www-data ./manage.py create_burial_views yes

sudo -u www-data ./manage.py collectstatic --noinput | \
tee $TTY_ | \
egrep -i '^[1-9][0-9]* static files? copied' > /dev/null && \
echo 'Static file(s) changed. Touching static folder.' && \
sudo -u www-data touch static

sudo /etc/init.d/apache2 reload

cd /home/chrooted/home/COMMON/django/pd_web
sudo -u www-data -H git pull
cd /home/chrooted/home/COMMON/django/pd_web/pd
sudo -u www-data ./manage.py collectstatic --noinput
