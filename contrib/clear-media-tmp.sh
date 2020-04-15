#! /bin/bash

# Очистка MEDIA/tmp. Параметр: pd_web или pd_prod

if [ "$1" == "pd_web" -o "$1" == "pd_prod" ]; then

    media_tmp_dir_="/home/www-data/django/MEDIA/$1/tmp"

    for old_file_ in `find $media_tmp_dir_/ -type f -mtime +2 2>/dev/null`; do
        rm -f $old_file_
    done

    for empty_dir in `find $media_tmp_dir_/ -type d -mtime +2 2>/dev/null`; do

        # Если непустой каталог, не будет удален. Это и надо.
        #
        rmdir $empty_dir 2> /dev/null
    done
else
    echo "Invalid parameter"
    exit 1
fi
exit 0
