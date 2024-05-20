readme.txt

Синхронизация Microsoft Access базы данных захоронений
с данными на сервере.


*   Установить Python для Windows:
        NB:
            !   разрядность MS Office (32 или 64 bit) должна быть той же, что у Python
            -   установка вроде требует наличие Интернет
            !   ставилось с Customize ..., а там:
                +   Install Python for all users
                +   Add Python to environment variables
            !   в конце установки может быть предложено удлинить строку путей. Выполните!

*   При подключенном Интернет:
        В командной строке (cmd)
        pip install pypyodbc

* settings.py, подправить, если необходимо,  параметры:
    - ODBC_DRIVER
    - CEMETERIES

!   При включении в задачу Планировщика заданий указать рабочую папку:
    где находится sysnc.pyw
