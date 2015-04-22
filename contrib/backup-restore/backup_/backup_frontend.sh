#! /bin/bash
#
# backup_frontend.sh
#
# Формирует архив front-end,
# самый свежий frontend-1.tgz, остальные -- ранее сделанные
#
launch_dir=`dirname $0`
BACKUP_PATH="$launch_dir/frontend-backup"
mkdir -p $BACKUP_PATH > /dev/null 2> /dev/null

# tar может не отработать, если во время архивации что-то вруг поменялось
#
loopcount=0
rc=0
while [ $loopcount -lt 10 ]; do
    loopcount=`expr $loopcount + 1`
    rm -f $BACKUP_PATH/current.tgz
    tar cfzh $BACKUP_PATH/current.tgz /home/jenkins/{current_build,current_prod_build} >/dev/null 2>&1
    rc=$?
    if [ $rc -eq 0 ]; then break; fi
done
if [ $rc -ne 0 ]; then 
    echo "Failed to create frontend archive, rc=$rc" >&2
    exit 1
fi

loopcount=2
while [ $loopcount -gt 1 ]; do
    nextcount=`expr $loopcount - 1`
    mv "$BACKUP_PATH/frontend-$nextcount.tgz" "$BACKUP_PATH/frontend-$loopcount.tgz" >/dev/null 2>&1
    loopcount=$nextcount
done
mv "$BACKUP_PATH/current.tgz" "$BACKUP_PATH/frontend-1.tgz" >/dev/null 2>&1
