# coding: utf-8

import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pd',                      # Or path to database file if using sqlite3.
        'USER': 'postgres',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {
            'autocommit': True,
        },
    },
}

TIME_ZONE = 'Europe/Moscow'

LANGUAGE_CODE = 'ru'

SITE_ID = 1

USE_I18N = True
USE_L10N = True
USE_TZ = False

DATE_INPUT_FORMATS = (
    '%d.%m.%Y', '%Y-%m-%d',
)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

MEDIA_ROOT = os.path.join(ROOT_DIR, 'media/')
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(ROOT_DIR, 'static/')
STATIC_URL = '/static/'


STATICFILES_DIRS = (
    os.path.join(ROOT_DIR, 'static_src/'),
    os.path.join(ROOT_DIR, 'asset_src/'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = 'r9ux__e!=awmsi7x%(&amp;-fd*#sob2u4*ks-h@1id=ldn0^f=11('

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'pd.middleware.LoginRequiredMiddleware',
    'corsheaders.middleware.CorsMiddleware',
)


TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.request",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "pd.context_processors.context_processor",
)

ROOT_URLCONF = 'pd.urls'

WSGI_APPLICATION = 'pd.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(ROOT_DIR, 'templates/'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',

    'rest_framework',
    'rest_framework.authtoken',

    'south',
    'pytils',
    'debug_toolbar',
    'raven.contrib.django',
    'captcha',

    'geo',
    'burials',
    'billing',
    'persons',
    'users',
    'orders',
    'logs',
    'reports',
    'import_burials',
    'mobile',
    'rest_api',
    'restthumbnails',
    'django_assets',
)

from pd.logging import skip_unreadable_post
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'skip_unreadable_posts': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_unreadable_post,
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false', 'skip_unreadable_posts', ],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

SOUTH_TESTS_MIGRATE = False

INTERNAL_IPS = ['127.0.0.1',]

# Разрешить вводить идентификационный номер для усопшего:
DEADMAN_IDENT_NUMBER_ALLOW = False

# Разрешить формирование кабинетов отвественного, посредством задания
# мобильного телефона для входа отвественного:
CREATE_CABINET_ALLOW = True

# LOGIN_URL, все REGISTER_URLS_REGEX, и некоторые другие -- в списке url,
# к которым возможен доступ без регистрации, см. pd/middleware.py
#
LOGIN_URL = "/login/"

# Это регулярные выражения!!! :
# URLs, не требующие регистрации в системе:
REGISTER_URLS_REGEX = r'^/?register(?:/|$)'
SUPPORT_URLS_REGEX = r'^/?support(?:/|$)'
# URLs, доступ к которым регулируется в соответствующих классах.as_view():
API_URLS_REGEX = r'^/?api(?:/|$)'
# URLs, доступные анонимным пользователям, например в публичном каталоге:
ANONYMOUS_URLS_REGEX = r'^/?(?:thumb|media)/product\-photo/'
# URLs, доступные анонимным пользователям, но при определенных условиях
ANONYMOUS_LIMITED_URLS_REGEX = r'^/?(?:thumb|media)/place\-photos/'

LOGOUT_URL = "/logout/"
LOGIN_REDIRECT_URL = "/"

SESSION_COOKIE_NAME = 'pdsession'

PAGINATION_USER_PER_PAGE_ALLOWED = True
PAGINATION_PER_PAGE = 50

# Кодировка для файлов обмена.
CSV_ENCODING = "utf8"

# Валюта по умолчанию, код:
CURRENCY_DEFAULT_CODE = 'RUR'

# Настройки пэйджинации.
PAGINATION_USER_PER_PAGE_MAX = 50
PAGINATION_PER_PAGE = 5

SENTRY_TESTING = True

DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS': False}

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# Google reCaptcha keys, поучаемые из http://www.google.com/recaptcha,
# подлежат замене в local_settings.py:
#
RECAPTCHA_PUBLIC_KEY = 'a-string-of-hex-and-digits'
RECAPTCHA_PRIVATE_KEY = 'another-string-of-hex-and-digits'
RECAPTCHA_USE_SSL = False

# Для отправки кода активации и прочей почты,
#
# По умолчанию почта отправляется через localhost:25.
# Если не настроен почтовый сервер на этом хосте,
# то необходимо заполнить параметры отправки почты
# в local_settings.py

# Этот адрес применяется как "От кого" в письмах,
# отправляемых от имени системы. Подлежит замене
# в local_settings.py
#
DEFAULT_FROM_EMAIL = 'EMAIL-HOST-USER@gmail.com'

# На этот адрес доставляются скрытые копии всех писем, отправленных
# с этого сервера. Если не задан (None), то такие копии не
# доставляются
#
BCC_OUR_MAIL = None 

# Для учета настроек, необязательных на сайтах разработчиков
#
PRODUCTION_SITE = False

# Необязательные параметры
#
# Давать ли доступ к Django Admin,
# по умолчанию - не давать
#
# ADMIN_ENABLED = False
#
# Имеет право регистировать нового пользователя
# только таковой с организации с этим ИНН
#
# SUPERVISOR_ORG_INN = 'строка'

# CORS:
# Переопределить в False в local_settings.py на production server
#
CORS_ORIGIN_ALLOW_ALL = True
#
# Задать в local_settings.py на production server:
#
#CORS_ORIGIN_WHITELIST = (
#   'pohoronnoedelo.ru',
#)

# THUMB
THUMBNAILS_FILE_SIGNATURE = '%(source)s/%(size)s~%(method)s~%(secret)s.%(extension)s'
THUMBNAILS_STORAGE_BASE_PATH = '/thumb/'
THUMBNAILS_PROXY_BASE_URL = '/thumb/'
#THUMBNAILS_STORAGE_BACKEND = 'testsuite.storages.TemporaryStorage'
# возможные длины и высоты:
THUMBNAILS_ALLOWED_SIZE_RANGE = range(20, 2001)

# REST framework
REST_FRAMEWORK = {
    'PAGINATE_BY': 50,
    'PAGINATE_BY_PARAM': 'page_size',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_api.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
}


#ASSETS_URL = STATIC_URL
ASSETS_MODULES = [
    'pd.assets'
]
ASSETS_DEBUG = False

# На production, а также на разработческих серверах,
# где налажена связка frontend - backend,
# установить этот параметр в True
#
REDIRECT_LOGIN_TO_FRONT_END = False

# Если работаем с налаженным front-end:
# ------------------------------------
# Начальная страница. Пользователь попадает на pd.ru. Это front-end,
# использующий ссылки на org.pd.ru, что является back-end.
# Иногда потребуется внутри back-end вычислять адрес front-end,
# для чего:
BACK_END_PREFIX = 'org.'
# В отладочных целях может использоваться (в local_settings.py):
FRONT_END_URL = None
# Если задан, например, FRONT_END_URL = 'http://localhost/api/',
# то действие BACK_END_PREFIX отменяется

# Учетные записи для SMS- службы рассылки СМС-сообщений,
# на разные страны могут быть разные учетные записи
# в службе рассылки сообщений. Если кода страны получателя
# сообщения нет в словарях списка SMS_SERVICE, то действует
# учетная запись с 'country_code': 'default'.
# Если и таковой нет, то отправка будет невозможна.
# Подлежат замене в local_settings.py production сервера:
SMS_SERVICE = [
    { 'country_code': '7', 'user': 'user7@email.org', 'password': 'secret7', },
    { 'country_code': '375', 'user': 'user375@email.org', 'password': 'secret375', },
    # Чтобы сразу нарваться на "Абонент не обслуживается", а не ждать, пока после установки
    # пароля об этом сообщит СМС служба:
    # { 'country_code': 'default', 'user': 'default@email.org', 'password': 'default-secret', },
]

# Получатели доходов от рекламы.
#
# NB    Подобраны ИНН для этих организаций, чтоб уменьшить риск совпадения
#       с ИНН имеющимихся организаций в разработческих сайтах.
#       Если же будет совпадение, то этим организациям в соотв. б.д.
#       придется играть соотв. роль.
#       На production site совпадений быть не должно.
#
# Организация, принимающая, затем распределяющая доход:
#
ORG_AD_PAY_RECIPIENT = {
    'name': 'AD Recipient',
    # Подлежит замене в local_settings.py для production site.
    'inn': '9999999991',
    # Доля, оставляемая в этой организации после распределения дохода между
    # ОМС и ORG_PD_FUND
    'share': 0.33,
}
# Первичный ключ этой организации. Если None, то организация ищется по ИНН,
# иначе (установлен в local_settings.py) по первичному ключу, для ускорения поиска
#
# ВНИМАНИЕ!!!
# Если задан ORG_AD_PAY_RECIPIENT_PK, то ORG_AD_PAY_RECIPIENT['inn'] не используется
#
ORG_AD_PAY_RECIPIENT_PK = None
#
# Фонд похоронного дела, получает свою долю от полученного ORG_AD_PAY_RECIPIENT'ом:
#
ORG_PD_FUND = {
    'name': 'PD Fund',
    # подлежит замене в local_settings.py, когда появится этот фонд с соотв. ИНН
    'inn': '9999999992',
    'share': 0.34,
}
# При авторизации посредством Oauth некоторые социальные сети, в частности одноклассники,
# требуют публичный и секретный ключ приложения. Разумеется, эта конфиденциальная информация
# должна быть заменена на реальную в local_settings.py
#
OAUTH_PROVIDERS_KEYS = {
    'odnoklassniki': {
        'public_key': 'PublicStuff',
        'private_key': 'PrivateStuff',
    },
}

YANDEX_API_KEYS = [
    # Ключи получены на пользователя pohoronnoedelo@yandex.ru.
    # В зависимости от доменв, откуда идет вызов к yandex api,
    # применяется тот или иной ключ
    #
    # NB:   скрывать их в local_settings нет смысла, они доступны
    #       в исходных кодах страниц
    { 
        're_host': r'pohoronnoedelo\.ru(?:\:\d+)?$',
        'api_key': r'AObGplMBAAAAuFr-WQIADlv2OrFxt6jLCsvlWYiJgtv7YDMAAAAAAAAAAABOAIr3zG31LfU7pllJzun2eZhJmg==',
    },
    { 
        're_host': r'pohoronnoedelo\.by(?:\:\d+)?$',
        'api_key': r'AFFSqFMBAAAAeVx-MwIAmJKPwA0dteKD-K4LTJ1nfnN2MTQAAAAAAAAAAABHBnSvshh-SZ_2hyIdqI0NU_lvCA==',
    },
]
    
WKHTMLTOPDF_CMD = '/usr/local/bin/wkhtmltopdf'

try:
    from local_settings import *
except ImportError:
    pass

# MEDIA_ROOT может измениться в local_settings
THUMBNAILS_STORAGE_ROOT = os.path.join(MEDIA_ROOT, 'thumbnails')

# Уведомления (о регистрации, об ошибках смс- сервиса),
# а также письма в поддержку направляются по этому списку:
#
try:
    # Задали ли это в local_settings ?
    SUPPORT_EMAILS
except NameError:
    # Нет, не задали, да и DEFAULT_FROM_EMAIL наверняка там изменится
    SUPPORT_EMAILS = (DEFAULT_FROM_EMAIL, )

import sys
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    from test_settings import *
