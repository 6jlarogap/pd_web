#! /bin/bash
#
# backup_sensitive.sh
#
# Формирует архив различных системных данных
# самый свежий sys-1.tgz, остальные -- ранее сделанные
#
launch_dir=`dirname $0`
BACKUP_PATH="$launch_dir/sys-backup"
FILE_LIST=/tmp/backup_sys_files.txt
mkdir -p $BACKUP_PATH > /dev/null 2> /dev/null

# tar может не отработать, если во время архивации что-то вруг поменялось
#
loopcount=0
rc=0
while [ $loopcount -lt 10 ]; do
    loopcount=`expr $loopcount + 1`
    rm -f $BACKUP_PATH/current.tgz $FILE_LIST
    find /etc > $FILE_LIST
    find /home/www-data/django | egrep "local_settings.py$" >> $FILE_LIST
    find /home | egrep "\.ssh/" >> $FILE_LIST
    find /root | egrep "\.ssh/" >> $FILE_LIST
    find /var/www | egrep "\.ssh/" >> $FILE_LIST
    tar cfz "$BACKUP_PATH/current.tgz" -T $FILE_LIST
    rc=$?
    if [ $rc -eq 0 ]; then break; fi
done
if [ $rc -ne 0 ]; then 
    echo "Failed to create the archive, rc=$rc" >&2
    exit 1
fi

loopcount=2
while [ $loopcount -gt 1 ]; do
    nextcount=`expr $loopcount - 1`
    mv "$BACKUP_PATH/sys-$nextcount.tgz" "$BACKUP_PATH/sys-$loopcount.tgz" >/dev/null 2>&1
    loopcount=$nextcount
done
mv "$BACKUP_PATH/current.tgz" "$BACKUP_PATH/sys-1.tgz" >/dev/null 2>&1
