Установка у заказчика ПК (виртуальной машины) с копией системы
    ! только их данные

    * Участвуют:
        - сервер:
            * держит для заказчика (пусть это будет barjkh) chrooted home folder
            * держит для всех подобных заказчиков один на всех каталог проекта
            * держит архив базы данных, содержащий данные только заказчика
            * держит каталог медийных файлов, только заказчика, в chrooted home folder
            * при обновлении проекта заодно обновляет тот
              один на всех каталог проекта (см. server/update_pd_django_only.sh)
        - посредник, пусть это будет ПК suprune20, см. dealer/*:
            * считывает данные всех заказчиков сервера, 
              базу данных и медию (rsync'ом)
            * разворачивает базу данных у себя
            * убирает из базы данные других организаций
              (заодно удаляется медия других организаций)
            * отправляет архив базы и медию (rsync'ом) на сервер,
              в каталог заказчика
        - виртуальная машина на ПК заказчика:
            (см. client-vm-home-folder/sync.txt)
            * забирает с сервера каталог проекта
            * обновляет виртуальное окружение для проекта
            * забирает с сервера архив базы данных, разворачивает ее
            * обновляет каталог проекта, включая миграцию:
                на всякий случай, если проект и данные не синхронизированы
                по структуре данных
        
    * Устанавливается виртуальная машина (ВМ), а в ней почти всё аналогично
      инструкциям в ../install-readme.txt.
      - Пользователь soul, пароль soul: нечего особо скрывать:
        ВМ будет у заказчика, пароль на доступном ему диске всегда
        может поменять. Даем soul права sudoer'a.
        Login shell: /bin/bash
      - каталог проекта: /home/www-data/django/pd_web
      - media проекта: /home/www-data/django/MEDIA/pd_web
      
    * Сервер: создаем пользователя. Пусть это barjkh.
      В группе пользователей, которым по ssh будет chroot- доступ:
          sudo groupmod -n chrooted barjkh
      NB:
          Если потом для другой организацию надо будет сделать
          аналогичную ВМ, то для нее создадим пользователя,
          например, another, но поменять у него группу:
              sudo usermod -g chrooted another

    * ВМ.
        Получаем ключи, обеспечиваем ssh по этим ключам с сервером:
            - ssh-keygen -t rsa (без challenge пароля),
            - содержимое /home/soul/.ssh/id_rsa.pub кладем в
              строчку файла /home/barjkh/authorized_keys на сервере
    
    * Сервер. Обеспечить chroot доступ по ssh (rsync via ssh)
        (по мотивам: http://allanfeid.com/content/creating-chroot-jail-ssh-access)
        chroot- каталог: /home/chrooted
            - sudo -i
            
            - mkdir -p /home/chrooted/{dev,etc,lib,usr,bin,home}
            - mkdir -p /home/chrooted/usr/bin
            - chown root.root /home/chrooted
            - mknod -m 666 /home/chrooted/dev/null c 1 3
            
            - cd /home/chrooted/etc
            - cp /etc/ld.so.cache .
            - cp /etc/ld.so.conf .
            - cp /etc/nsswitch.conf .
            - cp /etc/hosts .
            
            - cd /home/chrooted/bin
            - cp /bin/ls .
            - cp /bin/bash .

            - cd /home/chrooted/usr/bin
            - cp /usr/bin/rsync .

            - кладем в /usr/local/sbin процедуру l2chroot ,
              заполнения в chroot- jailed folder библиотек,
              необходимых для базовых команд: ls, bash, rsync,
              получена с http://www.cyberciti.biz/files/lighttpd/l2chroot.txt,
              подправлена в соответствии с chroot- каталогом:
                BASE=”/webroot” --> BASE=”/home/chrooted/”
            
            - l2chroot /bin/ls
            - l2chroot /bin/bash
            - l2chroot /usr/bin/rsync
            ! (для 64-битной ОС):
              cp /lib/x86_64-linux-gnu/ld-2.19.so /home/chrooted/lib/x86_64-linux-gnu/
              
            - в /etc/ssh/sshd_config добавить:
                Match Group chrooted
                    ChrootDirectory /home/chrooted/
                    X11Forwarding no
                    AllowTcpForwarding no
              service ssh restart

            - mkdir /home/chrooted/barjkh
            - cp -p -r /home/barjkh/.ssh /home/chrooted/home/barjkh
            - chown -R barjkh:suprune20 /home/chrooted/home/barjkh
            - chmod g+rwx /home/chrooted/home/barjkh
            - chmod -R u-r /home/chrooted/home/barjkh
              NB:
                  suprune20 - для доступа к этому каталогу посредника


