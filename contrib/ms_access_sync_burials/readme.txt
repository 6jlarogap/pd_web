readme.txt

Синхронизация Microsoft Access базы данных захоронений
с данными на сервере.

*   Установить Python для Windows:
        (!) для Windows XP, не выше версии 3.4
        На Windows 7 Python 3.4.4 тоже сгодится
        Качать отсюда:
        - 32bit version: https://www.python.org/ftp/python/3.4.4/python-3.4.4.msi
        - 64bit version: https://www.python.org/ftp/python/3.4.4/python-3.4.4.amd64.msi
        При установке всё, как предлагает

*   При подключенном Интернет:
        В командной строке (cmd), (!) запущенной от имени администратора (!):
        c:
        cd \Python34\Scripts
        pip install pypyodbc

* settings.py, подправить, если необходимо,  параметры:
    - ODBC_DRIVER
    - CEMETERIES
