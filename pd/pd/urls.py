# coding: utf-8

from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('')

urlpatterns += patterns('pd.views',
    url(r'^favicon\.ico$',
        RedirectView.as_view(url='{0}img/favicon16x16.ico'.format(settings.STATIC_URL))),
    url(r'^', include('users.urls')),
    url(r'^', include('burials.urls')),
    url(r'^', include('persons.urls')),
    url(r'^', include('orders.urls')),
    url(r'^', include('reports.urls')),
    url(r'^', include('mobile.urls')),
    url(r'^geo/', include('geo.urls')),
    url(r'^import/', include('import_burials.urls')),
)

# Для включения административных функций (http://.../admin)
# добавить параметр ADMIN_ENABLED  в pd/local_settings.py (!)
# и установить его в True
#
if 'ADMIN_ENABLED' in dir(settings) and settings.ADMIN_ENABLED:
    urlpatterns += patterns('',
        url(r'^admin/jsi18n/', 'django.views.i18n.javascript_catalog'),
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', include(admin.site.urls)),
    )

urlpatterns += patterns('',
    #
    # url(r'^media/(?P<path>.*)$',  'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    #
    # Здесь django.views.static.serve заменена на свою функцию
    # pd.views.media_xsendfile, которая проверяет, работаем ли мы под сервером Apache и если да,
    # то проверяем доступ к media файлу. Если проверки успешны, то Apache с mod_xsendfile
    # передает media файл клиенту.
    # Если работаем не под сервером Apache, а пока это только из ./manage.py runserver, то 
    # управление передается на django.views.static.serve, но это без проверок доступа к файлу
    #
    url(r'^media/(?P<path>.*)$',  'pd.views.media_xsendfile', {'document_root': settings.MEDIA_ROOT}),
)

if settings.DEBUG:
    urlpatterns += patterns('',
            url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
