install-readme.txt, utf8 code page
-------------------

Инструкции, точнее опыт установки одного из разработчиков:
 
    * Примечания:
        - ~/venv/pdweb:         virtual environment проекта
        - ~/projects/pd_web:    проект, в соответствии с именем на bitbucket.org
        - USERNAME:             имя пользователя на bitbucket.org

        - ubuntu:               ubuntu 16.04 или 18.04, если не уточняется
 
    * Д.б. установлено на Linux:
        - средства разработки:
            * python3, не ниже 3.5
                  * sudo apt install python3-all-dev
                  * sudo apt install g++
                  * sudo apt python3-virtualenv python3-pycurl

         - postgresql,
            * в т.ч. для разработчика, ubuntu:
              sudo apt-get install postgresql postgresql-server-dev-all
            полагаем, что используется база postgresql на localhost,
            в которой пользователю postgres всё дозволено. Это достигается
            (ubuntu 16.04) в /etc/postgresql/9.5/main/,
            (ubuntu 18.04) в /etc/postgresql/10/main/)

            заменой строки:
                local all postgres peer
            на:
                local all postgres trust
            с перезагрузкой postgresql (service postgresql restart)

         - библиотеки для графики, включая jpeg, в Ubuntu: libjpeg-dev

        - bower
            ubuntu 16.4 и ниже:
                * скачать NodeJS: http://nodejs.org/
                * распаковать, cd node-<VERSION>; ./configure && make && sudo make install
                * sudo npm install -g bower
            ubuntu 18.4:
                sudo apt install nodejs
                sudo apt install npm
                sudo npm install -g bower

        - программы:
            * wkhtmltopdf (конвертация в pdf, от Google):
                - для ubuntu 16.04 можно довольствоваться
                  архивной версией 0.12.0, в которой распространяется архив, его
                  распаковываешь куда-то и программа готова к запуску.
                    * (ubuntu 16.04) sudo apt-get install fontconfig
                    * (ubuntu 16.04) sudo apt-get install libxrender1
                    * скачать wkhtmltopdf-архив для 32 или 64 bit,
                      http://sourceforge.net/projects/wkhtmltopdf/files/archive/0.12.0/
                    * tar xf wkhtmltox-linux-<i386|amd64>_<версия>.tar.xz
                    * sudo rsync -a wkhtmltox /usr/local/bin && rm -rf wkhtmltox
                    * sudo ln -s /usr/local/bin/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
                ! На ubuntu 18.04:
                    (приходится таки ставить wkhtmltopdf из дистрибутива, и это всё потянуло кучу
                     инсталяций для X server'a):
                    sudo -i
                    apt-get install wkhtmltopdf
                    apt-get install xvfb
                    echo -e '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf -q $*' > /usr/local/bin/wkhtmltopdf.sh
                    chmod a+x /usr/local/bin/wkhtmltopdf.sh
                    ln -s /usr/local/bin/wkhtmltopdf.sh /usr/local/bin/wkhtmltopdf
                    logout
                - Проверка:
                    /usr/local/bin/wkhtmltopdf http://www.google.com ~/musor.pdf
                    ~/musor.pdf должен демонстрировать начальную страницу Google

         - web сервер apache2:
            (ubuntu: sudo apt-get install apache2  apache2-utils)

         -git (ubuntu: sudo apt-get install git)

    * Должен быть запущен postgresql сервер

    * mkdir ~/venv; cd ~/venv
    * virtualenv -p `which python3` pdweb
    * mkdir ~/projects; cd ~/projects
    * git clone https://USERNAME@bitbucket.org/USERNAME/pd_web.git
    * cd ~/projects/pd_web
    * bower install
        Там выбрать пункт 1:
            1) angular#1.0.8 which resolved to 1.0.8 and is required by angular-cookies#1.0.8, angular-resource#1.0.8, PD
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
            sudo apt-get install libapache2-mod-xsendfile libapache2-mod-wsgi-py3

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
            - sudo apt-get install postfix
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

    * Очистка "мусора"
        на производственном серверею
      В /etc/crontab такого типа строки:
          15 2 * * * www-data   cd /home/www-data/django/pd_prod/pd && ./manage.py clearsessions
          16 5 * * 0 www-data   rm -rf /home/www-data/django/MEDIA/pd_prod/thumbnails/*
