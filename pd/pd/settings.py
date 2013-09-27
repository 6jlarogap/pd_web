# coding: utf-8

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Arcady Chumachenko', 'arcady.chumachenko@gmail.com'),
)

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
    'fias': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'fias',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

TEST_FIAS = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'fias',                      # Or path to database file if using sqlite3.
    'USER': '',                      # Not used with sqlite3.
    'PASSWORD': '',                  # Not used with sqlite3.
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

MEDIA_ROOT = './media/'
MEDIA_URL = '/media/'

STATIC_ROOT = './static/'
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    './static_src/',
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
    'users.middleware.ProfileMiddleware',
    'pd.middleware.LoginRequiredMiddleware'
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
    './templates/',
)

SENTRY_DSN = 'https://3d969464fe0c413f8394d2a045afc2d9:ab5346a1afbc43ceb131bd02c1f2ed53@app.getsentry.com/4786'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',

    'south',
    'pytils',
    'debug_toolbar',
    'raven.contrib.django',
    'captcha',

    'geo',
    'burials',
    'persons',
    'users',
    'orders',
    'logs',
    'reports',
    'import_burials',
    'mobile',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
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

ACCOUNT_ACTIVATION_DAYS = 7

# LOGIN_URL, все REGISTER_URLS_REGEX, и некоторые другие -- в списке url,
# к которым возможен доступ без регистрации, см. pd/middleware.py
#
LOGIN_URL = "/login/"
REGISTER_URLS_REGEX = r'^/?register(?:/|$)'
LOGOUT_URL = "/logout/"
LOGIN_REDIRECT_URL = "/"

SESSION_COOKIE_NAME = 'pdsession'

PAGINATION_USER_PER_PAGE_ALLOWED = True
PAGINATION_PER_PAGE = 50

# Кодировка для файлов обмена.
CSV_ENCODING = "utf8"

# Настройки пэйджинации.
PAGINATION_USER_PER_PAGE_MAX = 50
PAGINATION_PER_PAGE = 5

SENTRY_TESTING = True

DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS': False}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Google reCaptcha keys, поучаемые из http://www.google.com/recaptcha,
# подлежат замене в local_settings.py:
#
RECAPTCHA_PUBLIC_KEY = 'a-string-of-hex-and-digits'
RECAPTCHA_PRIVATE_KEY = 'another-string-of-hex-and-digits'
RECAPTCHA_USE_SSL = False

# для отправки кода активации и прочей почты от сервера,
# по умолчанию, подлежат замене в local_settings.py:
#
AUTH_USER_EMAIL_UNIQUE = True
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = 'user'
EMAIL_HOST_PASSWORD = 'secret'
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'admin@org.com'

# Длительность действия заявки на регистрацию
#
ACCOUNT_ACTIVATION_DAYS = 3

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

try:
    from local_settings import *
except ImportError:
    pass

import sys
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    from test_settings import *
