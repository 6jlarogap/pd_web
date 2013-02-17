# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('burials.views',
    url(r'^$', 'dashboard', name='dashboard'),
    url(r'^burials/archive/$', 'archive', name='archive'),
    url(r'^burials/create/$', 'create_burial', name='create_burial'),
    url(r'^burials/(?P<pk>\d+)/$', 'view_burial', name='view_burial'),
    url(r'^burials/(?P<pk>\d+)/edit/$', 'edit_burial', name='edit_burial'),
    url(r'^burials/(?P<pk>\d+)/notification/$', 'make_notification', name='make_notification'),
    url(r'^burials/$', 'burial_list', name='burial_list'),

    url(r'^places/(?P<pk>\d+)/$', 'view_place', name='view_place'),

    url(r'^manage/cemetery/$', 'manage_cemeteries', name='manage_cemeteries'),
    url(r'^manage/cemetery/create/$', 'manage_cemeteries_create', name='manage_cemeteries_create'),
    url(r'^manage/cemetery/(?P<pk>\d+)/edit/$', 'manage_cemeteries_edit', name='manage_cemeteries_edit'),

    url(r'^cemetery_times/', 'cemetery_times', name='cemetery_times'),

)
