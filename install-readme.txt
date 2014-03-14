install-readme.txt, utf8 code page
-------------------

Инструкции, точнее опыт установки одного из разработчиков:
 
    * Примечания:
        - ~/venv/pdweb:         virtual environment проекта
        - ~/projects/pd_web:    проект, в соответствии с именем на bitbucket.org
        - USERNAME:             имя пользователя на bitbucket.org
 
    * Д.б. установлено на Linux:
        - средства разработки:
            * python, не ниже 2.6
              - пакеты python, которые могут не быть в его "стандартной поставке":
                  * python-dev
                  * python-virtualenv
                  * python-pycurl
            * C/C++
            * g++
         - postgresql,           в т.ч. для разработчика
            полагаем, что используется база postgresql на localhost,
            в которой пользователю postgres всё дозволено. Это достигается
            правкой pg_hba.conf (на ubuntu 12.04 в /etc/postgresql/9.1/main/)
            заменой строки:
                local all all peer
            на:
                local all all trust
            с перезагрузкой postgresql (service postgresql restart)
         - библиотеки для графики, включая jpeg, в Ubuntu 12.04: libjpeg-dev
    
        - bower
            * скачать NodeJS: http://nodejs.org/
            * распаковать, cd node-<VERSION>; ./configure; make; sudo make install
            * sudo npm install -g bower
 
    * Д.б. запущены postgresql & mysql серверы
 
    * mkdir ~/venv; cd ~/venv; virtualenv --no-site-packages pdweb
    * mkdir ~/projects; cd ~/projects
    * git clone https://USERNAME@bitbucket.org/USERNAME/pd_web.git
    * cd ~/projects/pd_web
    * bower install
    * source ~/venv/pdweb/bin/activate
    * export VIRTUALENV_DISTRIBUTE=true
    * curl http://python-distribute.org/distribute_setup.py | python
    * rm distribute-<VERSION>.tar.gz
    * pip install -r pip.txt
 
    * cd ~/projects/pd_web/pd/pd
    * cp local_settings.py.example local_settings.py
    * внести правки в local_settings.py, но если почти без правок, то:
 
        - получить у руководителя проекта dump базы данных pd
          (пусть это: pd.psql.gz)
            createdb pd
            zcat pd.psql.gz | psql -U postgres pd

           (create database '<database>' encoding 'UTF-8' owned by '<user>';)
            
        - MEDIA_ROOT:
            это дело вкуса, но в соответствии с local_settings.py.example:
            mkdir -p ~/projects/MEDIA/pd_web
 
    * cd ~/projects/pd_web
      ln -s /home/sev/venv/pdweb ENV
            : virtual env, запускаемое из ./manage.py
    * deactivate
    !!! Можно запускать и отлаживать:
        cd ~/projects/pd_web/pd
        ./manage.py runserver <параметры>
 
Настройка сервера Apache:

    * Должен быть установлен Apache mod_wsgi и mod_xsendfile.
        - В Debian/Ubuntu выполнить:
            sudo apt-get install libapache2-mod-wsgi libapache2-mod-xsendfile
    
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
            # Для версий ниже 1.0 (на "старом" Debian):
            # XSendFileAllowAbove on

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
                Order deny,allow
                Allow from all
            </Directory>
            <FilesMatch "wsgi\.py$">
                Order deny,allow
                Allow from all
            </FilesMatch>
        </VirtualHost>
