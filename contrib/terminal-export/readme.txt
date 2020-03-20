Ряд минских кладбищ имеют терминалы: 3D графику о захоронениях на этих кладбищах.
Данные для программы терминала обновляются при ее запуске, обычно по утрам.
Данные, в формате .csv, содержат текущую информацию об усопших с привязкой к кладбищу,
участку, ряду, месту. Данные для всех таких кладбищ можно получить на сервере,
выполнив:

    ./manage.py export_terminal /home/terminal

где /home/terminal - домашний каталог пользователя, который будет забирать
экспортные .csv:

    - vostochoe_cemeteries.csv
    - voennoe_cemeteries.csv
    - zapadnoe_cemeteries.csv
    - kolodischi_cemeteries.csv
    - chizhovskoe_cemeteries_cemeteries.csv
    - severnoe_cemeteries_cemeteries.csv

В /etc/crontab можно занести строчку:

    30 1 * * * root cd /home/www-data/django/pd_web/pd && ./manage.py export_terminal /home/terminal

Пользователь terminal создается с login shell == /bin/false, для него прописывается
в /etc/ssh/sshd_config:

    Match User terminal
        ChrootDirectory /home/terminal
        ForceCommand internal-sftp
        AllowTcpForwarding no
        PermitTunnel no
        X11Forwarding no

В Ubuntu 18.04:
    Не найден способ, как в Ubuntu 18.04 у пользователя terminal сделать chroot
    на его домашний каталог в настройке /etc/ssh/sshd_config, но можно выполнить
    chroot на какую-то другую папку, например на /usr/local/ssh_chroot/terminal.
    В /etc/ssh/sshd_config:

    Match User terminal
        ChrootDirectory /usr/local/ssh_chroot/terminal
        ForceCommand internal-sftp
        AllowTcpForwarding no
        PermitTunnel no
        X11Forwarding no

Таким образом, единственное, что он может делать на сервере, это выполнять
sftp операции только в своем домашнем каталоге, причем только чтение,
ибо еще настраивается:

    chown root:root /home/terminal

Или в Ubuntu 18.04:

    chown root:root /usr/local/ssh_chroot/terminal

Для доступа к экспортным файлам терминалов на ПК с Windows на кладбище ставится
PuTTY Installer, http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html
Также должны быть ssh ключи, получаемые в PuTTYgen:
    - putty.ppk, приватный ключ,
    - публичный ключ, содержимое которого вносится в строчку в
      /home/terminal/.ssh/authorized_keys на сервере.

Теперь задача: периодически забирать экспортный .csv для терминала, посреди рабочего
времени смотрителя на кладбище, на его ПК, и так, чтобы это происходило незаметно
от пользователя за ПК, т.е. без выскакивания окна с выводом, возможно пустым,
процедуры чтения терминального экспорта.

--- Действия на кладбище --------------------------------------------

Есть офисный ПК, есть ПК терминала

Делаем на офисном ПК кладбища, например, Военного, папку d:\terminal,
куда кладем файлы:

    putty.ppk
    invisible.vbs
    sftp.bat

*   Из командной строки (CMD) запускаем:

        psftp.exe -l terminal -i putty.ppk register.ritual-minsk.by

    (Будет ответ, что программа не найдена, прописать путь к программе
     psftp.exe в системную переменную среды PATH)

    Будет запрос подтвердить ключ, отвечаем y (да)

*   На офисном ПК создать задание в планировщике заданий с действием:

    - программа/сценарий:   C:\Windows\System32\wscript.exe
    - аргументы:            invisible.vbs "sftp.bat voennoe_cemeteries"
                            (кавычки обязательны!)
    - рабочая папка:        d:\terminal

    Время запуска задания -- в какое-то рабочее время ежедневно.
    Тогда в это время будет появляться (обновляться) файл export.csv
    для Военного кладбища.

*   Папку d:\terminal надо сделать доступной по записи для ПК с терминалом,
    а в параметре db_file секции [Main] конфигурационного файла config.ini
    программы терминала прописать путь к export.csv

