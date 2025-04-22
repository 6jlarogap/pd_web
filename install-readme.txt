install-readme.txt, utf8 code page
-------------------

Инструкции, точнее опыт установки одного из разработчиков:
 
    * Примечания:
        - ~/venv/pdweb:         virtual environment проекта
        - ~/projects/pd_web:    проект, в соответствии с именем на bitbucket.org
        - USERNAME:             имя пользователя на bitbucket.org

        - ubuntu:               ubuntu 16.04 и выше, если не уточняется
                    !!! ubuntu 16.04, 18.04 имеют python3 версии ниже 3.8
                        Как установить там python 3.8, см. Приложение A
 
    * Д.б. установлено на Linux:
        - средства разработки:
            * python3, не ниже 3.8
                * sudo apt install python3-all-dev python3-virtualenv
                * sudo apt install software-properties-common libcurl4-gnutls-dev librtmp-dev

        - redis-server
                  * sudo apt install redis-server

        - postgresql,
            !!! версии не ниже 10. Если установлена более старая версия,
                например, в Ubuntu 16.04, то действовать по инструкции,
                см. Приложение B

            * в т.ч. для разработчика, ubuntu:
                sudo apt install postgresql postgresql-server-dev-all

                полагаем, что используется база postgresql на localhost,
                в которой пользователю postgres всё дозволено. Это достигается
                в /etc/postgresql/<версия_postgresql>/main/

                заменой строки:
                    local all postgres peer
                на:
                    local all postgres trust
                с перезагрузкой postgresql (service postgresql restart)

        - geoipupdate, инструкции, см. Приложение C

        - библиотеки для графики, включая jpeg, в Ubuntu: 
            sudo apt install libjpeg-dev

        - программы:
            * wkhtmltopdf (конвертация в pdf, от Google):
                - для ubuntu 16.04 можно довольствоваться
                  архивной версией 0.12.0, в которой распространяется архив, его
                  распаковываешь куда-то и программа готова к запуску.
                    * (ubuntu 16.04) sudo apt install fontconfig
                    * (ubuntu 16.04) sudo aptt install libxrender1
                    * скачать wkhtmltopdf-архив для 32 или 64 bit,
                      http://sourceforge.net/projects/wkhtmltopdf/files/archive/0.12.0/
                    * tar xf wkhtmltox-linux-<i386|amd64>_<версия>.tar.xz
                    * sudo rsync -a wkhtmltox /usr/local/bin && rm -rf wkhtmltox
                    * sudo ln -s /usr/local/bin/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
                ! На ubuntu 18.04+:
                    (приходится таки ставить wkhtmltopdf из дистрибутива, и это всё потянуло кучу
                     инсталяций для X server'a):
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
            (ubuntu: sudo apt install apache2  apache2-utils)

         -git (ubuntu: sudo apt install git)

    * Должен быть запущен postgresql сервер

    * mkdir ~/venv; cd ~/venv
    * virtualenv -p `which python3` pdweb
    * mkdir ~/projects; cd ~/projects
    * git clone https://USERNAME@bitbucket.org/USERNAME/pd_web.git
    * cd ~/projects/pd_web
    * source ~/venv/pdweb/bin/activate
    * pip install --no-cache-dir -r pip.txt
        ! --no-cache-dir :  избегает проблему с локалью, когда стандартные
                            сообщения django (например, "пароль")
                            вдруг печатаются по английски (password)
    * cd ~/projects/pd_web/pd/pd
    * cp local_settings.py.example local_settings.py
    * внести правки в local_settings.py, но если почти без правок, то:

        - получить у руководителя проекта dump базы данных pd
          (пусть это: pd.psql.gz)
            createdb pd
            zcat pd.psql.gz | psql -U postgres pd
        - MEDIA_ROOT:
            это дело вкуса, но в соответствии с local_settings.py.example:
            mkdir -p ~/projects/MEDIA/pd_web

    * cd ~/projects/pd_web
      ln -s /home/LINUX-USER-NAME/venv/pdweb ENV
            : virtual env, запускаемое из ./manage.py
    * deactivate
    !!! Можно запускать и отлаживать:
        cd ~/projects/pd_web/pd
        ./manage.py runserver <параметры>

Настройка сервера Apache:

    * Должен быть установлен Apache mod_wsgi и mod_xsendfile.
        - В ubuntu выполнить:
            sudo apt install libapache2-mod-xsendfile libapache2-mod-wsgi-py3

    * При использовании ssl: sudo a2enmod ssl
    * sudo a2enmod rewrite

    * пример настройки виртуального хоста Apache
        (имя сервера, каталоги могут отличаться)

        <VirtualHost *:80>
            ServerName SERVER.ORG.COM
            ServerAlias SERVER.ORG.COM

            XSendFile On
            # Каталог media должен быть доступен пользователю,
            # исполняющему Apache, по чтению-записи.

            # Для свежих версий mod_xsendfile:
            XSendFilePath /home/www-data/media/pd_web

            Alias /static/          /home/www-data/static/pd_web/
            Alias /robots.txt       /home/www-data/static/pd_web/system/robots.txt

            WSGIDaemonProcess SERVER.ORG.COM display-name=%{GROUP} processes=1 threads=2
            WSGIProcessGroup  SERVER.ORG.COM
            WSGIScriptAlias / /home/www-data/django/pd_web/pd/pd/wsgi.py
            WSGIChunkedRequest On
            # Чтобы работала restframework_token_authorization
            WSGIPassAuthorization On
            # Во избежание ошибок: premature end of script headers wsgi.py
            WSGIApplicationGroup %{GLOBAL}

            # По умолчанию это 300 (5 мин), пусть так и остается,
            # но для запуска длительных процессов, например, при импорте
            # желательно увеличить, при этом sudo service apache2 reload
            #
            # TimeOut 3000

            <Directory /home/www-data/static/pd_web>
                # ВНИМАНИЕ!
                # Каталог static должен быть доступен пользователю,
                # исполняющему Apache, не только, разумеется,
                # по чтению, но и по записи (AngularJS)
                Require all granted
            </Directory>
            <FilesMatch "wsgi\.py$">
                Require all granted
            </FilesMatch>
        </VirtualHost>

    * Добавить в конфигурацию (/etc/apache2/conf-enabled) .conf-файл, например,
      с именем reqtimeout.conf следующего содержания:

        # Minimize IOError request data read exeptions when posting data
        #
        # http://stackoverflow.com/questions/3823280/ioerror-request-data-read-error
        # http://httpd.apache.org/docs/2.2/mod/mod_reqtimeout.html
        #
        RequestReadTimeout header=90,MinRate=500 body=90,MinRate=500

        - выполнить sudo a2enmod reqtimeout

    * При такой конфигурации (ubuntu):
        sudo chown -R www-data:www-data /home/www-data/media /home/www-data/pw_web
        cd /home/www-data/pd_web/pd
        sudo -u www-data ./manage.py collectstatic --noinput

    * sitemap.xml (для production site):
        - обеспечить периодическую регенерацию, например, строчкой в /etc/crontab:
            19 1 * * *   www-data cd /home/www-data/django/pd_prod/pd && ./manage.py create_sitemap https://pohoronnoedelo all
        - submit sitemap посредством google webmaster tools, см. инструкцию
            https://support.google.com/webmasters/answer/183669?hl=en&ref_topic=4581713
        - обеспечить resubmit sitemap, после того как меняется sitemap, например, строчкой в /etc/crontab:
            22 1 * * *   www-data cd /home/www-data && sh ./resubmit_sitemap.sh
            где /home/www-data/resubmit_sitemap.sh содержит:
            #! /bin/bash
            wget www.google.com/webmasters/tools/ping?sitemap=https%3A%2F%2Fpohoronnoedelo.ru%2Fsitemap.xml

    * Почта.
      - системные настройки:
        Система использует отправку различной почты. Если на localhost НЕ НАСТРОЕН почтовый сервер,
        то необходимо заполнить параметры EMAIL_..., см. local_settings.py.example.

        На ПРОИЗВОДСТВЕННОМ localhost, а также на "главном" разработческом, настраиваем почтовый сервер
        в минимальной и безопасной конфигурации:
            * слушает только localhost
            * пересылает почту только от localhost
        Установка:
            - sudo apt install postfix
              (Если спросит, в какой конфигурации, выбираем local only)
            - подправить /etc/postfix в соответствии с contrib/email-server/postfix/main.cf,
              для сравнения там есть оригинальный mail.cf.Orig
        ВАЖНО:
            - почта с системы уходит, подписанная (MAIL FROM: в smtp заголовках) как от
              info@pohoronnoedelo.ru, параметр DEFAULT_FROM_EMAIL в local_settings.py.
              Почтовый домен @pohoronnoedelo.ru обслуживается в Google.
              Если отправляем почту на адреса, тоже обслуживаемые Google,
              тот может обнаружить, что письмо получено с сервера, не авторизованного
              для отправки с него google- почты. Дабы это не случилось, нужна запись
              в DNS:

              pohoronnoedelo.ru TXT     v=spf1 include:_spf.google.com ip4:46.182.24.67 ~all

              Где 46.182.24.67 - адрес сервера pohoronnoedelo.ru

       - Отправитель почты.
         Тот, кто будет фигурировать по умолчанию в поле "От кого" писем от системы
         надо заменить параметр DEFAULT_FROM_EMAIL в local_settings.py

       - Получатель скрытых копий отправленных писем.
         ОСОБЕННО на производственном сервере, откуда письма отправляются с локального
         почтового сервера.
         Система отправляет письма. Некоторые из них идут нам же, так что их копии незачем
         где-то хранить. Но очень многие идут заказчикам, и желательно иметь копию этих писем,
         чтоб проверить, ушло ли сообщение и в каком виде ушло. Для этого
         параметр BCC_OUR_MAIL в local_settings.py. Если не задан, то скрытые
         копии не формируются.

    * службы GOOGLE:
        параметр local_settings.GOOGLE_SERVER_API_KEY, серверный ключ приложения Google.
        Применяется при доступе к видео youtube.
        Среди API пользователя должно быть включено Youtube API.

    * Очистка "мусора":
        (на производственном сервере)
      В /etc/crontab такого типа строки:
          # устаревшие сессии
          15 2 * * * www-data   cd /home/www-data/django/pd_prod/pd && ./manage.py clearsessions
          # устаревшие иконки
          16 5 * * 0 www-data   rm -rf /home/www-data/django/MEDIA/pd_prod/thumbnails/*
          # устаревшие временные файлы
          28 2 * * * www-data   /home/www-data/django/pd_prod/contrib/clear-media-tmp.sh pd_prod

---------------------------------------------------------------------------------------------------

Приложение A

Установка python 3.8 на ubuntu 16.04, 18.04

    sudo apt update
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install python3.8 python3.8-venv python3.8-dev python3.8-gdbm apache2-dev

    sudo apt purge libapache2-mod-wsgi-py3
    cd
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    sudo service apache2 stop
    sudo python3.8 get-pip.py
    sudo python3.8 -m pip install --upgrade pip setuptools wheel virtualenv mod_wsgi

    mod_wsgi-express module-config
        # : вывод заносим в /etc/apache2/mods-available/wsgi-python38.load
        # Например, так:
            sudo -i
            echo 'LoadModule wsgi_module "/usr/local/lib/python3.8/dist-packages/mod_wsgi/server/mod_wsgi-py38.cpython-38-x86_64-linux-gnu.so"' > /etc/apache2/mods-available/wsgi-python38.load
            exit
    sudo ln -s /etc/apache2/mods-available/wsgi-python38.load /etc/apache2/mods-enabled/wsgi-python38.load

    # cd /path/to/venv: пусть это будет :
    cd /home/www-data/venv
    virtualenv -p `which python3.8` pdweb.python38
    cd pdweb.python38
    source ./bin/activate
    pip install -r /path/to/current/pip.txt
    deactivate
    
    # Поменять symlink pd_web/ENV:
    sudo ln -sfn /home/www-data/venv/pdweb.python38 /home/www-data/django/pd_web/ENV
    sudo service apache2 start

---------------------------------------------------------------------------------------------------

Приложение B

Установка последней версии postgresql

!!! В разделе, где /var/lib/postgresql должно быть свободное место, не меньше 120% от того,
    сколько занимает текущий /var/lib/postgresql
!!! Эта установка сначала добавляет все версии postgresql, начиная со следующей после
    текущей, так что должно быть достаточно места и на системном разделе,
    не меньше 700 Mb свободного места

sudo echo 'deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main' > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

sudo apt upgrade
    # На ubuntu 16.04 это обновит текущий postgresql 9.5, а также поставит версии 10, 11, 12, 13.
    # (на момент, когда вносятся эти строки)
    # Версии 10, 11, 12 потом удалим.

pg_lsclusters 
    # Увидим:
    #   Ver Cluster Port Status Owner    Data directory               Log file
    #   9.5 main    5432 online postgres /var/lib/postgresql/9.6/main /var/log/postgresql/postgresql-9.5-main.log
    #   13  main    5433 online postgres /var/lib/postgresql/13/main  /var/log/postgresql/postgresql-13-main.log

sudo pg_dropcluster 13 main --stop
sudo pg_upgradecluster 9.5 main
sudo pg_dropcluster 9.5 main

dpkg -l | grep postgresql
    # Удалить из системы все postgresl-XX, где XX < 13:
    # sudo apt purge postgresql-9.5... ....
    # sudo apt purge postgresql-10... ....
    # sudo apt purge postgresql-11... ....
    # sudo apt purge postgresql-12... ....

---------------------------------------------------------------------------------------------------

Приложение C

Установка geoipupdate. Требуется, если проект будет открыт только для определеных стран

    sudo apt purge geoip-database geoip-bin geoipupdate
    sudo add-apt-repository ppa:maxmind/ppa
    sudo apt update
    sudo apt install geoipupdate

    # - Получить на https://www.maxmind.com/en/home:
    #       Account/User ID
    #       License key
    # - Заменить полученным в /etc/GeoIp.conf

    sudo geoipupdate
    # Должно отработать:
    ls -l /usr/share/GeoIP
        # Должно быть примерно следующее
        # -rw-r--r-- 1 root root  1436463 Mar 15  2018 GeoIP.dat
        # -rw-r--r-- 1 root root  5545515 Mar 15  2018 GeoIPv6.dat
        # -rw-r--r-- 1 root root 77379291 Mar 14 17:26 GeoLite2-City.mmdb
        # -rw-r--r-- 1 root root  7044714 Mar 14 17:26 GeoLite2-Country.mmdb
    В /etc/crontab добавить строку типа:
        # Min         Hr      Day     Month   DayofW  User      Command
        11            0       *       *       3       root      geoipupdate

В local_settings.py возможны такие строки:
    GEOIP2_DB = '/usr/share/GeoIP/GeoLite2-Country.mmdb'
    # Например, ['RU', 'BY']
    COUNTRIES_ISO_CODES_ALLOW = []
