#! /bin/bash

# Синхронизация данных, медиа файлов и проч

MYORG=barjkh
HOST="register.ritual-minsk.by"

ping -c 4 $HOST || { echo "No Internet connection"; exit; }

sudo -u www-data rsync -rtlupvz --delete \
     --exclude=ENV \
     --exclude=pd/pd/local_settings.py \
     --exclude=**/*.pyc \
     $MYORG@$HOST:/home/COMMON/django/pd_web \
     /home/www-data/django

source ~/venv/pdweb/bin/activate
pip install -r /home/www-data/django/pd_web/pip.txt
deactivate

rsync -rtlupvz --delete $MYORG@$HOST:/home/COMMON/support/ /home/COMMON/support/
rsync $MYORG@$HOST:/home/$MYORG/dump.psql.gz ~/

dropdb -U postgres pd
createdb -U postgres pd
zcat ~/dump.psql.gz | psql -U postgres pd

sudo -u www-data rsync -rtupvz --delete \
     $MYORG@$HOST:/home/$MYORG/media/ \
     /home/www-data/django/MEDIA/pd_web/
sudo chmod u+rwx /home/www-data/django/MEDIA/pd_web/

cd /home/www-data/django/pd_web/pd
sudo -u www-data ./manage.py migrate --noinput
sudo -u www-data ./manage.py create_burial_views yes
sudo -u www-data ./manage.py collectstatic --noinput
sudo service apache2 reload
