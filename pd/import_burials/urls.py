# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('import_burials.views',
    url(r'^$', 'import_forms', name='import_forms'),
    url(r'^orgs/$', 'import_orgs', name='import_orgs'),
    url(r'^burials/$', 'import_burials', name='import_burials'),
)
