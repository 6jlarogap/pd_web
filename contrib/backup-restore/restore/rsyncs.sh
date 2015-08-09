#! /bin/bash
#
# restore_MEDIA.sh
#
sudo rsync -rltupvz --delete reserve@46.182.24.67:/home/www-data/django/MEDIA/pd_prod/ \
                                           /home/www-data/django/MEDIA/pd_prod/

sudo chown -R www-data:www-data /home/www-data/django/MEDIA/pd_prod

rsync -rltupvz --delete reserve@46.182.24.67:/home/reserve/frontend-backup/ \
                                           /home/suprune20/reserve/frontend-backup/

sudo rsync -rltupvz --delete "/var/lib/jenkins/workspace/PD frontend prod/dist/" \
                                           /home/suprune20/reserve.pohoronnoedelo.ru/dist/

rsync -rltupvz --delete reserve@46.182.24.67:/home/reserve/sys-backup/ \
                                           /home/suprune20/reserve/sys-backup/

rsync -rltupvz --delete reserve@46.182.24.67:/home/reserve/sys-backup/ \
                                           /home/suprune20/reserve/sys-backup/

rsync -rltupvz --delete reserve@46.182.24.67:/home/reserve/pgsql-backup/ \
                                           /home/suprune20/reserve/pgsql-backup/

rsync -rltupvz --delete reserve@46.182.24.67:/home/reserve/media-backup/ \
                                           /home/suprune20/reserve/media-backup/

rsync -rltupvz --delete reserve@46.182.24.67:/home/suprune20/support/ \
                                           /home/suprune20/support/
