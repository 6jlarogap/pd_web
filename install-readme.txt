install-readme.txt, utf8 code page
-------------------

Инструкции по установке на Ubuntu 24.04 lts (python 3.12))
 
    * Примечания:
        -   /home/www-data/             $ROOT_DIR, там всё внутри
                                        Все каталоги полагаются внутри этой папки
                                            На период установки сделать её доступной по записи
                                            пользователю. Пусть это будет $USER
        -   venv/pd_web/                virtual environment проекта
        -   django/pd_web/              код проекта
        -   register.org.com            адрес сервера

        -   archive@192.168.0.158:/mnt/backup/register.org.com/
                                        $BACKUP, где лежит резервная копия

    * Д.б. установлено на Linux:
        - средства разработки:
            * python3
                * sudo apt install python3-all-dev python3-virtualenv
                * sudo apt install software-properties-common libcurl4-gnutls-dev librtmp-dev

        - redis-server
                  * sudo apt install redis-server

        - postgresql,
            * в т.ч. для разработчика, ubuntu:
                sudo apt install postgresql postgresql-server-dev-all

                Используется база postgresql на localhost,
                в которой пользователю postgres всё дозволено. Это достигается
                в/etc/postgresql/16/main/pg_hba.conf

                заменой строки:
                    local all postgres peer
                на:
                    local all postgres trust
                с перезагрузкой postgresql (sudo service postgresql restart)

        - библиотеки для графики, включая jpeg, в Ubuntu: 
            sudo apt install libjpeg-dev

        - программы:
            * wkhtmltopdf (конвертация в pdf, от Google):
                    sudo -i
                    apt install wkhtmltopdf
                    apt install xvfb
                    echo -e '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf -q $*' > /usr/local/bin/wkhtmltopdf.sh
                    chmod a+x /usr/local/bin/wkhtmltopdf.sh
                    ln -s /usr/local/bin/wkhtmltopdf.sh /usr/local/bin/wkhtmltopdf
                    logout
                - Проверка:
                    /usr/local/bin/wkhtmltopdf http://www.google.com ~/musor.pdf
                    ~/musor.pdf должен демонстрировать начальную страницу Google

         - web сервер apache2:
            sudo apt install apache2  apache2-utils

    - Устанавливать будем, выполнив login пользователем $USER
        * sudo chown $USER:$USER $ROOT_DIR

    - Установим все необходимые библиотеки:
        * mkdir -p $ROOT_DIR/venv
        * cd $ROOT_DIR/venv
        * virtualenv -p `which python3` pd_web
        * cd $ROOT_DIR/venv/pd_web
        * rsync -av $BACKUP/code/pip.txt pip.txt
        * source ./bin/activate
        * pip install -r pip.txt
        * deactivate

    - Установим код проекта:
        * mkdir -p $ROOT_DIR/django/pd_web/pd
        * cd $ROOT_DIR/django/pd_web
        * rsync -av $BACKUP/code/pd/ pd/
        * ln -s $ROOT_DIR/venv/pd_web ENV

    - Выгрузим базу данных из последней резервной копии:
        * rsync -av $BACKUP/database/today/<LAST_COPY>.psql.gz /tmp/<LAST_COPY>.pg.gz
            -   <LAST_COPY> имеет вид, например, pd-20250515200301
        * createdb -U postgres pd
        * zcat /tmp/<LAST_COPY>.pg.gz | psql -U postgres pd

    - Подготовим и выгрузим каталог для медии: фото мест, файлов захоронений и т.п.:
        NB!
            файлы медии желательно держать в разделе отдельного диска,
            чтоб была возможность его увеличивать, не трогая систему.
            Пусть этот раздел смонтирован как /mnt/media
        * sudo mkdir /mnt/media/pd_web
        * sudo chown $USER:$USER /mnt/media/pd_web
        * ln -s /mnt/media/pd_web $ROOT_DIR/django/pd_web/MEDIA
        * rsync -av $BACKUP/media/ /mnt/media/pd_web/
        *** пошел долгий процесс. Можно параллельно продолжать
            другие работы в другом окне терминала

    - Можно проверить, как оно работает в тестовом режиме
        cd $ROOT_DIR/django/pd_web/pd
        ./manage.py runserver 0.0.0.0:8000
        http://register.org.com:8000,
            что-то можно посмотреть.
            ! Но пока копируется медия, не все файлы картинки увидите

Настройка сервера Apache:

    * Должен быть установлен Apache mod_wsgi и mod_xsendfile.
        sudo apt install libapache2-mod-xsendfile libapache2-mod-wsgi-py3

    * Используется ssl:
        sudo a2enmod ssl rewrite

    * поместить в /etc/apache2/{sites-available,sites-enabled}
        org_pd.conf из архива $BACKUP/media/sys1.tgz
    * скопировать  
        /usr/local/etc/ssl-certificates/ из того же архива
        Внимание. Сертификаты не вечные! Делайте их сами по истечении срока

    * Подготовка к запуску web сервера apache2:
        sudo chown -R www-data:www-data $ROOT_DIR/django $ROOT_DIR
        cd $ROOT_DIR/django/pd_web/pd
        sudo -u www-data ./manage.py collectstatic

    sudo service apache2 restart
    Можете идти на https://register.org.com

    * Другое:
        -   настройка выгрузки csv для терминалов:
                см. $BACKUP/media/sys1.tgz:
                    /etc/crontab
                    /etc/ssh/ssd_config
                    /usr/local/ssh_chroot
        -   очистка мусора,
            резервное копирование системных файлов,
            проверка не исчерпано ли место на диске
            :
                см. $BACKUP/media/sys1.tgz:/etc/crontab

