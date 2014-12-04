# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

#from django.views.generic import TemplateView # Django v1.5
from django.views.generic.simple import direct_to_template 

from users.models import Org


urlpatterns = patterns('burials.views',
    url(r'^$', 'dashboard', name='dashboard'),

    url(r'^burials/add_agent/$', 'add_agent', name='add_agent'),
    url(r'^burials/add_loru_agent/$', 'add_agent', dict(prefix='loru_'), name='add_agent'),
    url(r'^burials/add_dover/$', 'add_dover', name='add_dover'),
    url(r'^burials/add_loru_dover/$', 'add_dover', dict(prefix='loru_'), name='add_dover'),
    url(r'^burials/add_org/$', 'add_org', name='add_org'),
    url(r'^burials/add_zags/$', 'add_org', dict(type=Org.PROFILE_ZAGS), name='add_org'),
    url(r'^burials/add_loru/$', 'add_org', dict(type=Org.PROFILE_LORU), name='add_org'),
    url(r'^burials/add_doctype/$', 'add_doctype', name='add_doctype'),

    url(r'^burials/archive/$', 'archive', name='archive'),
    url(r'^burials/create/$', 'create_burial', name='create_burial'),
    url(r'^burials/get_place/$', 'get_place', name='get_place'),
    url(r'^burials/get_graves_number/$', 'get_graves_number', name='get_graves_number'),

    url(r'^burials/(?P<pk>\d+)/$', 'view_burial', name='view_burial'),
    url(r'^burials/(?P<pk>\d+)/edit/$', 'edit_burial', name='edit_burial'),
    url(r'^burials/(?P<pk>\d+)/notification/$', 'make_notification', name='make_notification'),
    url(r'^burials/(?P<pk>\d+)/spravka/$', 'make_spravka', name='make_spravka'),
    url(r'^burials/(?P<pk>\d+)/comment/$', 'burial_comment', name='burial_comment'),
    url(r'^burials/(?P<pk>\d+)/exhumate/$', 'burial_exhumate', name='burial_exhumate'),
    url(r'^burials/(?P<pk>\d+)/exhumate/cancel/$', 'burial_cancel_exhumation', name='burial_cancel_exhumation'),
    url(r'^burials/(?P<pk>\d+)/exhumate/report/$', 'make_exhumate_report', name='make_exhumate_report'),
    url(r'^burials/(?P<pk>\d+)/exhumate/notification/$', 'make_exhumate_notification', name='make_exhumate_notification'),
    url(r'^burials/$', 'burial_list', name='burial_list'),
    url(r'^burials/search/$', 'burial_public_list', name='burial_public_list'),
    
    url(r'^burialfiles/(?P<pk>\d+)/delete/$', 'delete_burialfile', name='delete_burialfile'),
    url(r'^burialfiles/(?P<pk>\d+)/editcomment/$', 'edit_burialfile_comment', name='edit_burialfile_comment'),

    url(r'^places/(?P<pk>\d+)/certificate$', 'place_certificate', name='place_certificate'),

    url(r'^places/(?P<pk>\d+)/$', 'view_place', name='view_place'),
    url(r'^places/(?P<pk>\d+)/responsible/remove/$', 'rm_responsible', name='rm_responsible'),

    #url(r'^manage/cemetery/$', 'manage_cemeteries', name='manage_cemeteries'),
    #url(r'^manage/cemetery/create/$', 'manage_cemeteries_create', name='manage_cemeteries_create'),
    #url(r'^manage/cemetery/(?P<pk>\d+)/edit/$', 'manage_cemeteries_edit', name='manage_cemeteries_edit'),
    url(r'^manage/cemetery/(?P<pk>\d+)/merge/$', 'manage_cemeteries_merge', name='manage_cemeteries_merge'),

    url(r'^cemetery_times/', 'cemetery_times', name='cemetery_times'),
    url(r'^autocomplete/cemeteries/', 'autocomplete_cemeteries', name='autocomplete_cemeteries'),
    url(r'^autocomplete/areas/', 'autocomplete_areas', name='autocomplete_areas'),

    url(r'^api/client/places/(?P<pk>\d+)/?$', 'api_client_places_detail', name='api_client_places_detail'),
    url(r'^api/client/places/(?P<pk>\d+)/graves/?$', 'api_client_place_graves', name='api_client_place_graves'),

    # REST API
    #url(r'^$', TemplateView.as_view(template_name='base_angular.html'),), # v1.5
    url(r'^manage/cemetery$', direct_to_template, {'template': 'base_angular.html'}, name='manage_cemeteries'),
)
