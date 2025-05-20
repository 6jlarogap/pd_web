#! /bin/bash
#
# rsyncs.sh
#

echo "*"
echo "*"
echo -n "* `date` "
echo "START: media, code, system settings backup"
echo "*"

echo "*"
echo -n "* `date` "
echo "Media backup"
echo "*"
rsync -av --no-owner --no-group --delete \
    --exclude=**/lost+found \
    --exclude=**/thumbnails \
    --exclude=**/tmp \
    reserve@register.ritual-minsk.by:/home/www-data/django/MEDIA/pd_web/ \
    /mnt/backup/register.ritual-minsk.by/media/

echo "*"
echo -n "* `date` "
echo "System settings backup"
echo "*"

rsync -av --no-owner --no-group --delete \
    reserve@register.ritual-minsk.by:/home/reserve/sys-backup/ \
    /mnt/backup/register.ritual-minsk.by/system


echo "*"
echo -n "* `date` "
echo "Code backup"
echo "*"

for f in pd/ install-readme.txt pip.txt; do
    rsync -av --no-owner --no-group --delete -L \
        --exclude=*.pyc \
        --exclude=**/.webassets-cache \
        reserve@register.ritual-minsk.by:/home/www-data/django/pd_web/$f \
        /mnt/backup/register.ritual-minsk.by/code/$f
done

echo "*"
echo -n "* `date` "
echo "DONE: media, code, system settings backup"
echo "*"
echo "*"
