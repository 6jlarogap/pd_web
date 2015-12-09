#! /bin/bash

# Синхронизация данных, медиа файлов и проч

MYORG=barjkh
HOST="register.ritual-minsk.by"

sudo -u www-data rsync -rltupvz --delete \
     --exclude=ENV --exclude=pd/pd/local_settings.py \
     $MYORG@$HOST:/django/pd_web \
     /home/www-data/django

source ~/venv/pdweb/bin/activate
pip install -r /home/www-data/django/pd_web/pip.txt
deactivate

rsync $MYORG@$HOST:/home/$MYORG/dump.psql.gz ~/

dropdb -U postgres pd
createdb -U postgres pd
zcat ~/dump.psql.gz | psql -U postgres pd

cd /home/www-data/django/pd_web/pd
sudo -u www-data ./manage.py migrate --noinput
sudo -u www-data ./manage.py create_burial_views yes || true
sudo -u www-data ./manage.py collectstatic --noinput
