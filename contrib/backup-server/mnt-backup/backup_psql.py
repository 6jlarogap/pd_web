#   backup_psql.py
#   --------------
#   Параметры конфигурации
#       Переменные ПРОПИСНЫМИ буквами. Импортируются
#       из backup_psql_conf.py в каталоге запуска сценария
#
#   Назначение:
#       *   Резервное копирование psql баз данных
#           с удаленного сервера
#           - сегодняшнее (today):
#               Производится при любом запуске сценария, например,
#               планировщиком задач (crontab).
#               Туда попопадают все дампы, созданные за последние 24 ч.
#               Дампы старше суток удаляются.
#               На удаленном сервере удаляются страые дампы, чтоб
#               их осталось не более CURRENT_DUMPS_NUM
#           -  ежедневное (daily):
#               Там по одному дампу в день, но не старше недели.
#           -  еженедельное (weekly):
#               Там по одному дампу в неделю, но не старше месяца.
#           -  ежемесячное (monthly):
#               Там по одному дампу в месяц
#           -  ежегодное (yearly):
#               Там по одному дампу в год, но не старше YEARS лет
#           Дампы производятся в gzip- упакованные файлы
#           с именами db-YYYYMMDDhhmmss.pg.gz, где:
#               - db:   имя б.д;
#               - YYYYMMDDhhmmss - дата, время начала процесса дампа
#
#       *   Сегодняшние дампы можно использовать для репликации
#           этих б.д на другой сервер.
#           Для большей надежности этой репликации перед формированием
#           сегодняшних дампов создается LOCK_FILE, потом удаляется.
#           Если параметр LOCK_FILE не задан, т.е. None, False и т.п.,
#           то LOCK_FILE не создается.

import sys, os, datetime

from backup_psql_conf import *

db_dump_ext = '.pg.gz'
datetime_format = '%Y%m%d%H%M%S'

rssh = "ssh %(ssh_key)s %(host_user)s@%(host)s" % dict(
    ssh_key=SSH_KEY,
    host_user=HOST_USER,
    host=HOST,
)
host_folder = HOST_FOLDER.rstrip('/')

def backup(db_name, dst_dir):
    now_str = datetime.datetime.now().strftime(datetime_format)
    gz_name = '%s-%s%s' % (db_name, now_str, db_dump_ext)
    pg_dump_command = \
        '%(rssh)s ' \
        '"' \
            'umask 0277 && ' \
            "export PGPASSWORD='%(pg_password)s' && " \
            'pg_dump -U %(pg_user)s %(db_name)s | ' \
            'gzip > %(host_folder)s/%(gz_name)s' \
        '"' % dict(
        rssh=rssh,
        db_name=db_name,
        host_folder=host_folder,
        gz_name=gz_name,
        pg_password=PG_PASSWORD,
        pg_user=PG_USER,
    )
    rc = os.system(pg_dump_command)
    if rc:
        print("Failed to create db '%s' dump at %s" % (db_name, HOST))
        exit(1)

    dst_f_name = '%s%s-%s%s' % (dst_dir, db_name, now_str, db_dump_ext)
    pg_copy_command = \
        'scp ' \
        '%(ssh_key)s ' \
        '%(host_user)s@%(host)s:%(host_folder)s/%(gz_name)s ' \
        '%(dst_f_name)s ' \
        '> /dev/null 2>&1 ' \
        % dict(
            ssh_key=SSH_KEY,
            host_user=HOST_USER,
            host=HOST,
            host_folder=host_folder,
            gz_name=gz_name,
            dst_f_name=dst_f_name,
        )
    rc = os.system(pg_copy_command)
    if rc:
        print("Failed to copy db dump from %s to here: %s" % (HOST, dst_f_name))
        exit(1)

def delta_datetime(fname):
    fname_datetime_str = fname.split('-')[-1].split('.')[0]
    return datetime.datetime.now() - datetime.datetime.strptime(fname_datetime_str, datetime_format)

# Чтоб все пути были каталогами, существовали и завершались '/'
for parm in ('BACKUP_PATH', 'TODAY_PATH', 'DAILY_PATH', 'WEEKLY_PATH', 'MONTHLY_PATH', 'YEARLY_PATH',):
    if not globals()[parm].endswith('/'):
        globals()[parm] += '/'
    if parm != 'BACKUP_PATH':
        globals()[parm] = BACKUP_PATH + globals()[parm]
    if not os.path.isdir(globals()[parm]):
        print("Failed to find folder: %s" % globals()[parm])
        exit(1)

def print_date():
    print(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'), end =" ")    

print_date()
print(f'Backup postgres databases from {HOST}')

if LOCK_FILE:
    lock_file = open(TODAY_PATH + LOCK_FILE, 'w')
    lock_file.close()

one_day = datetime.timedelta(days=1)
for fname in os.listdir(TODAY_PATH):
    if fname.endswith(db_dump_ext) and delta_datetime(fname) >= one_day:
        os.remove(TODAY_PATH + fname)

for db in DATABASES:
    print_date()
    print(f'{db}: today backup')
    backup(db, TODAY_PATH)

if LOCK_FILE:
    os.remove(TODAY_PATH + LOCK_FILE)

max_delta = datetime.timedelta.max

# daily backups
one_week = datetime.timedelta(days=7)
for db in DATABASES:
    min_delta = max_delta
    for fname in os.listdir(DAILY_PATH):
        if fname.startswith(db + '-'):
            delta = delta_datetime(fname)
            min_delta = min(delta, min_delta)
            if delta >= one_week:
                os.remove(DAILY_PATH + fname)
    if min_delta >= one_day:
        print_date()
        print(f'{db}: daily backup')
        backup(db, DAILY_PATH)

# weekly backups
one_month = datetime.timedelta(days=30)
for db in DATABASES:
    min_delta = max_delta
    for fname in os.listdir(WEEKLY_PATH):
        if fname.startswith(db + '-'):
            delta = delta_datetime(fname)
            min_delta = min(delta, min_delta)
            if delta >= one_month:
                os.remove(WEEKLY_PATH + fname)
    if min_delta >= one_week:
        print_date()
        print(f'{db}: weekly backup')
        backup(db, WEEKLY_PATH)

# monthly backups
one_year = datetime.timedelta(days=365)
for db in DATABASES:
    min_delta = max_delta
    for fname in os.listdir(MONTHLY_PATH):
        if fname.startswith(db + '-'):
            delta = delta_datetime(fname)
            min_delta = min(delta, min_delta)
            if delta >= one_year:
                os.remove(MONTHLY_PATH + fname)
    if min_delta >= one_month:
        print_date()
        print(f'{db}: monthly backup')
        backup(db, MONTHLY_PATH)

# yearly backups
max_years = datetime.timedelta(days=YEARS * 365)
for db in DATABASES:
    min_delta = max_delta
    for fname in os.listdir(YEARLY_PATH):
        if fname.startswith(db + '-'):
            delta = delta_datetime(fname)
            min_delta = min(delta, min_delta)
            if delta >= max_years:
                os.remove(YEARLY_PATH + fname)
    if min_delta >= one_year:
        print_date()
        print(f'{db}: yearly backup')
        backup(db, YEARLY_PATH)

# Почистить старые дампы с удаленного сервера
#
current_dumps_num = CURRENT_DUMPS_NUM + 1
for db_name in DATABASES:
    print_date()
    print(f'{db_name}: clear unused copies at {HOST}')
    pg_list_command = \
            '%(rssh)s ' \
            '"' \
                'find %(host_folder)s/%(db_name)s-*%(db_dump_ext)s -type f | sort' \
            '"' % dict(
            rssh=rssh,
            host_folder=host_folder,
            db_name=db_name,
            db_dump_ext=db_dump_ext,
        )

    pipe = os.popen(pg_list_command)
    remote_dumps = pipe.read()
    rc = pipe.close()
    if rc:
        print("Failed to count dumps at %s" % (HOST, dst_f_name))
        exit(1)
    remote_dumps = remote_dumps.strip().split('\n')
    # Ограничим число удаляемых файлов до 3 шт, чтоб не была слишкой длинной строка удаления
    #
    to_remove = ''
    count_removed_dumps = 0
    num_remote_dumps = len(remote_dumps)
    if num_remote_dumps > CURRENT_DUMPS_NUM:
        for rd in remote_dumps:
            if count_removed_dumps >= 3 or num_remote_dumps <= CURRENT_DUMPS_NUM:
                break
            num_remote_dumps -= 1
            count_removed_dumps += 1
            to_remove = "%s %s" % (to_remove, rd)
    if to_remove:
        pg_remove_command = \
            '%(rssh)s ' \
            '"' \
                'rm %(to_remove)s' \
            '"' % dict(
            rssh=rssh,
            to_remove=to_remove,
        )
        rc = os.system(pg_remove_command)
        if rc:
            print("Failed to remove outdated dumps at %s" % HOST)
            exit(1)

print_date()
print(f'Done')
exit(0)
