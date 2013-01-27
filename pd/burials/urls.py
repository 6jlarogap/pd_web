# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('burials.views',
    url(r'^$', 'dashboard', name='dashboard'),
    url(r'^create/$', 'create_request', name='create_request'),
    url(r'^view/(?P<pk>\d+)/$', 'view_request', name='view_request'),

    url(r'^manage/cemetery/$', 'manage_cemeteries', name='manage_cemeteries'),
    url(r'^manage/cemetery/create/$', 'manage_cemeteries_create', name='manage_cemeteries_create'),
)
