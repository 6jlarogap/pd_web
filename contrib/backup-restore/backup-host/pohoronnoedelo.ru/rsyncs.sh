#! /bin/bash
#
# rsyncs.sh
#
REMOTE="reserve@register.ritual-minsk.by"
REMOTE_DIR="/home/reserve"
THIS_DIR="/home/soul/reserve/register.ritual-minsk.by"

sudo rsync -rltupvz --delete \
    --exclude=**/lost+found \
    --exclude=**/support \
    --exclude=**/thumbnails \
    --exclude=**/tmp \
    $REMOTE:/home/www-data/django/MEDIA/pd_web/ \
    /home/www-data/django/MEDIA/pd_web/

sudo chown -R www-data:www-data /home/www-data/django/MEDIA/pd_web

rsync -rltupvz --delete $REMOTE:$REMOTE_DIR/sys-backup/ \
                                           $THIS_DIR/sys-backup/
