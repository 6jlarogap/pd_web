# coding: utf-8

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ASSETS_DEBUG = DEBUG

ADMIN_ENABLED = True
SUPERVISOR_ORG_INN = '------'

ADMINS = (
        ('Eugene Suprune', 'sev@bsuir.by'),
)

MANAGERS = ADMINS

TEMPLATE_DIRS = (
    '/home/sev/projects/ughone/pd_web/pd/templates/',
)

TIME_ZONE = 'Europe/Moscow'

STATIC_ROOT = '/home/sev/projects/STATIC/pd_web/'
MEDIA_ROOT = '/tmp/'

# Google reCaptcha keys, поучаемые из http://www.google.com/recaptcha,

RECAPTCHA_PUBLIC_KEY = '6Lc_JwUTAAAAAJ9LZnfjf-zAApcWEbdCeJ6st2RB'
RECAPTCHA_PRIVATE_KEY = '-------------'

#RECAPTCHA_PUBLIC_KEY = '6LcZ5ucSAAAAAE118VGTsppT8_PfKAeZBzKp-x3i'
#RECAPTCHA_PRIVATE_KEY = '-------'
RECAPTCHA_USE_SSL = False
NOCAPTCHA = True

SENTRY_DSN = ''

# для отправки кода активации
#
EMAIL_HOST = 'mail.bsuir.by'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'test@bsuir.by'
EMAIL_HOST_PASSWORD = '------'
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'test@bsuir.by'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pd_ughone',                      # Or path to database file if using sqlite3.
        'USER': 'postgres',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                      # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {
            'autocommit': True,
        },
    },
}

SMS_SERVICE = [
    { 'country_code': '7', 'user': '-----', 'password': '-----', },
    { 'country_code': 'default', 'user': '-------', 'password': '------', },
]

ORG_AD_PAY_RECIPIENT_PK = 1

# На production, а также на разработческих серверах,
# где налажена связка frontend - backend,
# установить этот параметр в True
#
REDIRECT_LOGIN_TO_FRONT_END = False

PRODUCTION_SITE = True

# Разрешить вводить идентификационный номер для усопшего:
DEADMAN_IDENT_NUMBER_ALLOW = True

# Разрешить формирование кабинетов отвественного, посредством задания
# мобильного телефона для входа отвественного:
CREATE_CABINET_ALLOW = False

CURRENCY_DEFAULT_CODE = 'BYR'

DEATH_CERTIFICATE_REQUIRED = False

BURIAL_PLAN_DATE_DAYS_FROM_TODAY = 0

SPECIFIC_RU_LOCALE = 'by'
