import sys, os, datetime

DEBUG = False

ALLOWED_HOSTS = ['*']

# После django 1.5 сессии хранятся по умолчанию в json формате по умолчанию,
# но переход к этому формату означает потерю всех сессий, что наверняка
# приведет к необходимости вводить имя/пароль и следовательно,
# организационные проблемы.
#
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

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

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'pd.middleware.LoginRequiredMiddleware',
    'corsheaders.middleware.CorsMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(ROOT_DIR, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': False,
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "pd.context_processors.context_processor",
            ],
        },
    },
]

ROOT_URLCONF = 'pd.urls'

WSGI_APPLICATION = 'pd.wsgi.application'

INSTALLED_APPS = [
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

    'pytils',
    'debug_toolbar',
    'raven.contrib.django',

    'nocaptcha_recaptcha',

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
    'googlecharts',

    # Заглушка для javascript locales.
    # Если не подключаем специфичную локаль, то js функция gettext()
    # будет искать здесь locale/ru/LC_MESSAGES/djangojs.mo,
    # но найдет только locale/ru/LC_MESSAGES.
    #
    'django.conf',
]

from pd.logging import skip_ioerror_post
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'skip_ioerror_posts': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_ioerror_post,
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': [
                'require_debug_false',
                'skip_ioerror_posts',
             ],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}


INTERNAL_IPS = ['127.0.0.1',]

# Объем отправляемых данных, в байтах, исключая файлы.
# По умолчанию 2.5М. Добавим на всякий случай: у нас
# вводят иногда тексты.
#
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880

# With the default file upload settings, files larger than
# FILE_UPLOAD_MAX_MEMORY_SIZE now have the same permissions as
# temporary files (often 0o600).
#
# А это неудобно для резервного копирования медии: его обычно
# выполняет другой пользователь, нежели www-data и т.п.
#
# Set the FILE_UPLOAD_PERMISSIONS if you need the same permission
# regardless of file size.
#
FILE_UPLOAD_PERMISSIONS = 0o644

# Разрешить вводить идентификационный номер для усопшего:
# Это же применяется для кода, значимого для реестра
#
DEADMAN_IDENT_NUMBER_ALLOW = False
# Год, с которого введен реестр в стране
#
DEADMAN_REGISTER_START_DATE = datetime.date(2013, 1, 1)

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
# URLs, доступные анонимным пользователям, например в публичном каталоге, 
# а также общедоступные, например, из front-end, скрипты:
ANONYMOUS_URLS_REGEX = r'^/?(?:(?:thumb|media)/(?:product\-photo|support|user\-photos|store\-photos|cemetery\-photos))|jsi18n/'
# URLs, доступные анонимным пользователям, но при определенных условиях
ANONYMOUS_LIMITED_URLS_REGEX = r'^/?(?:thumb|media)/place\-photos/'

LOGOUT_URL = "/logout/"
LOGIN_REDIRECT_URL = "/"

UHOD_MOGIL_URL = "http://dev.uhodmogil.ru/places"
HRAM_PREDKOV_URL = "http://dev.hrampredkov.ru/persons"

SESSION_COOKIE_NAME = 'pdsession'

PAGINATION_USER_PER_PAGE_ALLOWED = True
PAGINATION_PER_PAGE = 50

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
NORECAPTCHA_SITE_KEY = 'public-norecaptcha-key'
NORECAPTCHA_SECRET_KEY = 'secret-norecaptcha-key'

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
#
# Переопределить в False в local_settings.py на production server
#
CORS_ORIGIN_ALLOW_ALL = True
#
# Задать в local_settings.py на production server:
#
# CORS_ORIGIN_REGEX_WHITELIST = (r'^(https?://)?(\w+\.)?pohoronnoedelo\.\w+$', )
#
# Может быть authentication cookies, при доступе к апи из множества
# доменов *.pohoronnoedelo.ru, посему:
#
CORS_ALLOW_CREDENTIALS = True

# THUMB
THUMBNAILS_FILE_SIGNATURE = '%(source)s/%(size)s~%(method)s~%(secret)s.%(extension)s'
THUMBNAILS_STORAGE_BASE_PATH = '/thumb/'
THUMBNAILS_PROXY_BASE_URL = '/thumb/'
#THUMBNAILS_STORAGE_BACKEND = 'testsuite.storages.TemporaryStorage'
# возможные длины и высоты:
THUMBNAILS_ALLOWED_SIZE_RANGE = dict(min=20, max=2000)

# REST framework
REST_FRAMEWORK = {

    # Вместо русской 'a' выводить \u0430, например.
    # Так было  в Django REST v2 по умолчанию.
    # Наш мобильный клиент понимает только \u0430,
    # и некоторые, -- особенно старые, -- браузеры
    # non ascii json вывод не понимают
    #
    'UNICODE_JSON': False,

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
# использующий ссылки на org.pd.ru (api.pd.ru), что является back-end.
# Иногда потребуется внутри back-end вычислять адрес front-end,
# для чего:
BACK_END_PREFIX_REGEX = r'org|api'
# В отладочных целях может использоваться (в local_settings.py):
FRONT_END_URL = None
# Если задан, например, FRONT_END_URL = 'http://localhost/api/',
# то действие BACK_END_PREFIX_REGEX отменяется

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

# Устанавливать в True в local_settings.py, если SMS служба отключена
#
DO_NOT_SEND_SMS = False

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
    #
    # Применяются в паспорте захоронения, чтоб нарисовать
    # квадратик карты вокруг точки с координатами.
    #
    # Ключи получены на пользователя invozm@yandex.ru.
    # В зависимости от домена, откуда идет вызов к yandex api,
    # применяется тот или иной ключ
    # Список ключей: https://tech.yandex.ru/maps/keys/
    #
    # NB:   скрывать их в local_settings нет смысла, они доступны
    #       в исходных кодах страниц
    {
        're_host': r'pohoronnoedelo\.ru(?:\:\d+)?$',
        'api_key': r'AEfPfFcBAAAACEfKJQIARwumbXjjFpZ_egGO3IDEnrmUexgAAAAAAAAAAAD940aylrCTc5s1dpgnIt8PuP7TNQ==',
    },
    {
        're_host': r'register\.ritual-minsk\.by(?:\:\d+)?$',
        'api_key': r'ABbQfFcBAAAAHpk_PQMAaRj6lhhOXXH_kdCtu-FYNSCf56QAAAAAAAAAAABN50Vtg6pAgH0zG7J-hConv75h9Q==',
    },
    {
        're_host': r'nasledievnukov\.ru(?:\:\d+)?$',
        'api_key': r'AHTQfFcBAAAAiwhqVQIAF5pKrcRARkWFQz4O7Bmk2a96PfEAAAAAAAAAAADmLypkR_nHQYl48js0gkDR0fWVQg==',
    },
]

# Серверный ключ приложения пользователя. У пользователя должно быть
# активизировано Youtube API v3
#
GOOGLE_SERVER_API_KEY = None

WKHTMLTOPDF_CMD = '/usr/local/bin/wkhtmltopdf'

# Обязательность свидетельства о смерти
DEATH_CERTIFICATE_REQUIRED = True

# Когда предлагать плановую дату захронения, сколько дней от сегодняшней даты
BURIAL_PLAN_DATE_DAYS_FROM_TODAY = 1

# Переход из года в год:
#   - за сколько дней до нового года показывать даты на следующий год
#   - до какого числа января следующего года учетный номер захоронения
#     может быть за предыдущий год
#
YEAR_OVER_DAYS = 15

# В Беларуси говорят по русски, но терминология там согласно закона
# несколько иная. Например, то что в РФ именуем кладбищем,
# в Беларуси будет местом погребения. Да и в РФ могут быть
# специфичные наименования.
#
# это код страны, для РБ -- 'by'
#
SPECIFIC_RU_LOCALE = 'ru'
#
# это имя приложения, для РБ -- 'locale_by'
#
SPECIFIC_RU_LOCALE_APP = ''

# Где находится мобильный смотритель, относительно MEDIA_ROOT
#
MOBILEKEEPER_MEDIA_PATH = "support/download/mobilekeeper.apk"

# Покажем статистику операций как козырь, когда придет время
SHOW_OPER_STATS = True

# Это убирает предупреждение, что появилась новая
# система тестирования
#
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

try:
    from .local_settings import *
except ImportError:
    pass

for t in TEMPLATES:
    t['OPTIONS']['debug'] = DEBUG
ASSETS_DEBUG = DEBUG

# Миграции, начиная с Django 1.7, вносят verbose_name
# поля, а это меняется для разных локалей
#
if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
    USE_I18N = False
    USE_L10N = False
    SPECIFIC_RU_LOCALE = ''

if SPECIFIC_RU_LOCALE:
    SPECIFIC_RU_LOCALE_APP = 'locale_%s' % SPECIFIC_RU_LOCALE
    LOCALE_PATHS = (
        os.path.join(ROOT_DIR, SPECIFIC_RU_LOCALE_APP , 'locale'),
    )
    INSTALLED_APPS.append(SPECIFIC_RU_LOCALE_APP)

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

# Django 1.8:
# Seconds have been removed from any locales that had them in
# TIME_FORMAT, DATETIME_FORMAT, or SHORT_DATETIME_FORMAT.
#
from django.conf.locale.ru import formats as ru_formats
sec_suffix = ":s"
if not ru_formats.TIME_FORMAT.endswith(sec_suffix):
    ru_formats.TIME_FORMAT += sec_suffix
if not ru_formats.DATETIME_FORMAT.endswith(sec_suffix):
    ru_formats.DATETIME_FORMAT += sec_suffix
if not ru_formats.SHORT_DATETIME_FORMAT.endswith(sec_suffix):
    ru_formats.SHORT_DATETIME_FORMAT += sec_suffix

# Test system is to be revised.
#import sys
#if len(sys.argv) > 1 and sys.argv[1] == 'test':
    #from test_settings import *
