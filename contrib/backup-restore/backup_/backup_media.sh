#! /bin/bash
#
# backup_media.sh
#
# Формирует архивы media-1.tgz, media-2.tgz, ... media-$NUM_ARCHIVES.tgz,
# самый свежий media-1.tgz, остальные -- ранее сделанные
#
# См. конфигурацию в backup_media.conf в каталоге запуска сценария
# или в /usr/local/etc
#
launch_dir=`dirname $0`

if [ -f "$launch_dir/backup_media.conf" ]; then
    source "$launch_dir/backup_media.conf"
else
    if [ -f "/usr/local/etc/backup_media.conf" ]; then
       source "/usr/local/etc/backup_media.conf"
    else
       echo "Config file not found" >&2
       exit 255
    fi
fi

# tar может не отработать, если во время архивации что-то вруг поменялось
#
loopcount=0
rc=0
while [ $loopcount -lt 100 ]; do
    loopcount=`expr $loopcount + 1`
    rm -f $BACKUP_PATH/current.tgz
    tar cfz $BACKUP_PATH/current.tgz $MEDIA_PATH --exclude=**/thumbnails/* >/dev/null 2>&1
    rc=$?
    if [ $rc -eq 0 ]; then break; fi
done
if [ $rc -ne 0 ]; then 
    echo "Failed to create media archive, rc=$rc" >&2
    exit 1
fi

loopcount=$NUM_ARCHIVES
while [ $loopcount -gt 1 ]; do
    nextcount=`expr $loopcount - 1`
    mv "$BACKUP_PATH/media-$nextcount.tgz" "$BACKUP_PATH/media-$loopcount.tgz" >/dev/null 2>&1
    loopcount=$nextcount
done
mv "$BACKUP_PATH/current.tgz" "$BACKUP_PATH/media-1.tgz" >/dev/null 2>&1
