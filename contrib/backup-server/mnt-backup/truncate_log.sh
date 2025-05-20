#! /bin/bash

if test -f "$1"; then
    /bin/true
else
    echo "1st parm: give me existing log"
    exit 1
fi
if [ -z "$2" ]; then
    echo "2nd parm: give me lines to truncate"
    exit 1
fi

LOG_=$1
LINES_=$2
TMP_="/tmp/__truncate_log__"
mv $LOG_ $TMP_
tail -n $LINES_ $TMP_ > $LOG_
rm -f $TMP_
