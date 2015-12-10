#! /bin/bash

MYORG=barjkh
MYORG_PK=24

HOST="register.ritual-minsk.by"
HOST_USER=suprune20
HOST_DB="pd"
MEDIA_ALL_HOST="/home/www-data/django/MEDIA/pd_web"
HOST_CHROOT="/home/chrooted"

PROJECTS="/home/sev/projects/ughone"
PROJECT="pd_web"
MEDIA_ALL_HERE="/home/sev/projects/backup/register.ritual-mink.by/MEDIA/pd_web"

# Если не используем специфичный ключ, то просто SSH_KEY=""
SSH_KEY="-i /home/suprune20/.ssh/id_rsa_pub_ritual"
RSSH="ssh $SSH_KEY"
RSCP="scp $SSH_KEY"

# Обновляем всю медию с сервера
#
rsync --rsh="$RSSH" \
    -rtupvz --delete \
    --exclude=**/support \
    --exclude=**/thumbnails \
    $HOST_USER@$HOST:$MEDIA_ALL_HOST/ $PROJECTS/MEDIA/pd_$MYORG/

# Забрасываем эту медию в здешний калог проекта
#
rsync -rtupvz --delete \
    "$MEDIA_ALL_HERE/" "$PROJECTS/MEDIA/pd_$MYORG/"

# Выполняю команду на сервере, получаю свежий дамп, забираю его,
# разворачиваю базу
#
$RSSH $HOST_USER@$HOST "pg_dump -U postgres $HOST_DB | gzip > /home/$HOST_USER/$HOST_DB.psql.gz"
$RSCP $HOST_USER@$HOST:/home/$HOST_USER/$HOST_DB.psql.gz /tmp/$HOST_DB.psql.gz
$RSSH $HOST_USER@$HOST "rm /home/$HOST_USER/$HOST_DB.psql.gz"
dropdb -U postgres "pd_ughone"
createdb -U postgres "pd_ughone"
zcat /tmp/$HOST_DB.psql.gz | psql -U postgres "pd_ughone"
rm /tmp/$HOST_DB.psql.gz

cd "$PROJECTS/$PROJECT"
git pull
cp -p "$PROJECTS/local_settings_$MYORG.py" "$PROJECTS/$PROJECT/pd/pd/local_settings.py"

cd "$PROJECTS/$PROJECT/pd"
./manage.py migrate --noinput
./manage.py create_burial_views yes

# Выделяю данные только этой организации
#
# ./manage.py one_ugh_leave.py $MYORG_PK yes

# Забрасываю дамп данных на сервер
#
pg_dump -U postgres "pd_ughone" | gzip > /tmp/dump.psql.gz
$RSCP /tmp/dump.psql.gz $HOST_USER@$HOST:/home/$HOST_USER
$RSSH $HOST_USER@$HOST "mv /home/$HOST_USER/dump.psql.gz $HOST_CHROOT/home/$MYORG"
$RSSH $HOST_USER@$HOST "sudo chown $MYORG:$HOST_USER $HOST_CHROOT/home/$MYORG/dump.psql.gz"
$RSSH $HOST_USER@$HOST "sudo chmod o-rw,g+rw $HOST_CHROOT/home/$MYORG/dump.psql.gz"
rm /tmp/dump.psql.gz

# Забрасываем медию на сервер
#
