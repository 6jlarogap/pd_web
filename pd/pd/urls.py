# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('')

urlpatterns += patterns('pd.views',
    url(r'^', include('users.urls')),
    url(r'^', include('burials.urls')),
    url(r'^', include('persons.urls')),
    url(r'^', include('orders.urls')),
    url(r'^', include('reports.urls')),
    url(r'^', include('mobile.urls')),
    url(r'^geo/', include('geo.urls')),
    url(r'^import/', include('import_burials.urls')),
    url(r'^import/', include('import_burials.urls')),
)

# Для добавления административных функций (http://.../admin)
# добавить параметр ADMIN_ENABLED  в pd/local_settings.py
# и установить его в True
#
if 'ADMIN_ENABLED' in dir(settings) and settings.ADMIN_ENABLED:
    urlpatterns += patterns('',
        url(r'^admin/jsi18n/', 'django.views.i18n.javascript_catalog'),
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', include(admin.site.urls)),
    )

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
