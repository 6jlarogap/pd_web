#! /bin/bash
PROJECT_='/home/www-data/django/pd_web'

TTY_=`tty`
cd "$PROJECT_"
sudo chown -R www-data:www-data .
sudo -u www-data -H git pull

sudo chown -R $USER:$USER .
bower install
sudo chown -R www-data:www-data .

cd "$PROJECT_/pd"
sudo -u www-data ./manage.py migrate --noinput
sudo -u www-data ./manage.py create_burial_views yes

sudo -u www-data ./manage.py collectstatic --noinput | \
tee $TTY_ | \
egrep -i '^[1-9][0-9]* static files? copied' > /dev/null && \
echo 'Static file(s) changed. Touching static folder.' && \
sudo -u www-data touch static

sudo /etc/init.d/apache2 reload
