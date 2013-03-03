# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('import_burials.views',
    url(r'^$', 'import_forms', name='import_forms'),
    url(r'^orgs/$', 'import_orgs', name='import_orgs'),
    url(r'^burials/$', 'import_burials', name='import_burials'),
    url(r'^kaluga/$', 'import_kaluga', name='import_kaluga'),
    url(r'^services/$', 'import_services', name='import_services'),
    url(r'^orders/$', 'import_orders', name='import_orders'),
    url(r'^banks/$', 'import_banks', name='import_banks'),
)
