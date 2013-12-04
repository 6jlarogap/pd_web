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
            * C /C++
            * g++
        - python-virtualenv
        - postgresql,           в т.ч. для разработчика
        - mysql,                в т.ч. для разработчика
    
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
            
        - fias db:
            echo 'create database fias' | mysql -u root
            # качаем, разархивируем, вносим в базу fias:
            wget -q -O - http://basicdata.ru/data/fias/fias_socrbase_table.sql.bz2 | bzcat | mysql -u root fias
            wget -q -O - http://basicdata.ru/data/fias/fias_socrbase_data.sql.bz2 | bzcat | mysql -u root fias
            wget -q -O - http://basicdata.ru/data/fias/fias_addrobj_table.sql.bz2 | bzcat | mysql -u root fias
            wget -q -O - http://basicdata.ru/data/fias/fias_addrobj_index.sql.bz2 | bzcat | mysql -u root fias
            wget -q -O - http://basicdata.ru/data/fias/fias_addrobj_data.sql.bz2 | bzcat | mysql -u root fias
            (последнее надолго, можно продолжать... :)
 
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

    * Должен быть установлен Apache mod_xsendfile.
        - В Debian/Ubuntu выполнить:
            sudo apt-get install libapache2-mod-xsendfile
    
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
