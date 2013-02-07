# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('burials.views',
    url(r'^$', 'dashboard', name='dashboard'),
    url(r'^requests/archive/$', 'archive', name='archive'),
    url(r'^requests/create/$', 'create_request', name='create_request'),
    url(r'^requests/view/(?P<pk>\d+)/$', 'view_request', name='view_request'),
    url(r'^requests/edit/(?P<pk>\d+)/$', 'edit_request', name='edit_request'),

    url(r'^burials/(?P<pk>\d+)/$', 'view_burial', name='view_burial'),
    url(r'^burials/create/$', 'create_burial', name='create_burial'),
    url(r'^burials/$', 'burial_list', name='burial_list'),

    url(r'^places/(?P<pk>\d+)/$', 'view_place', name='view_place'),

    url(r'^manage/cemetery/$', 'manage_cemeteries', name='manage_cemeteries'),
    url(r'^manage/cemetery/create/$', 'manage_cemeteries_create', name='manage_cemeteries_create'),
    url(r'^manage/cemetery/(?P<pk>\d+)/edit/$', 'manage_cemeteries_edit', name='manage_cemeteries_edit'),

)
