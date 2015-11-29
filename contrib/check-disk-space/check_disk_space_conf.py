# coding=utf-8

# check_disk_space_conf.py
# ------------------------

# Конфигурационный файл для check_disk_space.py

# Разделы, которые надо проверять:
#
CDS_PARTITIONS = (
    '/',
    '/home/www-data/django/MEDIA/pd_prod',
)

# В процентах, когда слать почту
#
CDS_THRESHOLD = 90

CDS_MANAGERS = (
    'suprune20@gmail.com',
    'drozd.vitaliy@gmail.com',
)

CDS_EMAIL_FROM = 'no-reply@pohoronnoedelo.ru'

CDS_HOSTNAME = 'prohoronnoedelo.ru'

CDS_EMAIL_HOST = None               # default localhost
CDS_EMAIL_PORT = None               # default 25
CDS_EMAIL_HOST_USER = None
CDS_EMAIL_HOST_PASSWORD = None
