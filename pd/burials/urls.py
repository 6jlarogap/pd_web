# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('burials.views',
    url(r'^$', 'dashboard', name='dashboard'),

    url(r'^burials/add_agent/$', 'add_agent', name='add_agent'),
    url(r'^burials/add_dover/$', 'add_dover', name='add_dover'),
    url(r'^burials/add_org/$', 'add_org', name='add_org'),

    url(r'^burials/archive/$', 'archive', name='archive'),
    url(r'^burials/create/$', 'create_burial', name='create_burial'),
    url(r'^burials/get_place/$', 'get_place', name='get_place'),

    url(r'^burials/(?P<pk>\d+)/$', 'view_burial', name='view_burial'),
    url(r'^burials/(?P<pk>\d+)/edit/$', 'edit_burial', name='edit_burial'),
    url(r'^burials/(?P<pk>\d+)/notification/$', 'make_notification', name='make_notification'),
    url(r'^burials/(?P<pk>\d+)/spravka/$', 'make_spravka', name='make_spravka'),
    url(r'^burials/(?P<pk>\d+)/comment/$', 'burial_comment', name='burial_comment'),
    url(r'^burials/$', 'burial_list', name='burial_list'),

    url(r'^places/(?P<pk>\d+)/$', 'view_place', name='view_place'),

    url(r'^manage/cemetery/$', 'manage_cemeteries', name='manage_cemeteries'),
    url(r'^manage/cemetery/create/$', 'manage_cemeteries_create', name='manage_cemeteries_create'),
    url(r'^manage/cemetery/(?P<pk>\d+)/edit/$', 'manage_cemeteries_edit', name='manage_cemeteries_edit'),

    url(r'^cemetery_times/', 'cemetery_times', name='cemetery_times'),
    url(r'^autocomplete/cemeteries/', 'autocomplete_cemeteries', name='autocomplete_cemeteries'),
    url(r'^autocomplete/areas/', 'autocomplete_areas', name='autocomplete_areas'),

)
