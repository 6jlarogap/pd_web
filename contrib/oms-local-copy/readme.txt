Установка у заказчика ПК (виртуальной машины) с копией системы
    ! только их данные

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
        chroot- каталог: /home/www-data
            - sudo -i
            
            - mkdir -p /home/www-data/{dev,etc,lib,usr,bin,home}
            - mkdir -p /home/www-data/usr/bin
            - chown root.root /home/www-data
            - mknod -m 666 /home/www-data/dev/null c 1 3
            
            - cd /home/www-data/etc
            - cp /etc/ld.so.cache .
            - cp /etc/ld.so.conf .
            - cp /etc/nsswitch.conf .
            - cp /etc/hosts .
            
            - cd /home/www-data/bin
            - cp /bin/ls .
            - cp /bin/bash .

            - cd /home/www-data/usr/bin
            - cp /usr/bin/rsync .

            - кладем в /usr/local/sbin процедуру l2chroot ,
              заполнения в chroot- jailed folder библиотек,
              необходимых для базовых команд: ls, bash, rsync,
              получена с http://www.cyberciti.biz/files/lighttpd/l2chroot.txt,
              подправлена в соответствии с chroot- каталогом:
                BASE=”/webroot” --> BASE=”/home/www-data/”
            
            - l2chroot /bin/ls
            - l2chroot /bin/bash
            - l2chroot /usr/bin/rsync
            ! (для 64-битной ОС):
              cp /lib/x86_64-linux-gnu/ld-2.19.so /home/www-data/lib/x86_64-linux-gnu/
              
            - в /etc/ssh/sshd_config добавить:
                Match Group chrooted
                    ChrootDirectory /home/www-data/
                    X11Forwarding no
                    AllowTcpForwarding no
              service ssh restart

            - mkdir /home/www-data/barjkh
            - cp -p -r /home/barjkh/.ssh /home/www-data/home/barjkh
            - chown -R barjkh:suprune20 /home/www-data/home/barjkh
            - chmod g+rwx /home/www-data/home/barjkh
              NB:
                  suprune20 - так как:
                      * дамп базы данных для barjkh, очищенный
                        от данных всех остальных организаций,
                        нежели barjkh, буду получать на ПК
                        suprune20, потом отправлять на сервер
                      * там же буду получать текст, содержащий
                        список медийных файлов организации barjkh


