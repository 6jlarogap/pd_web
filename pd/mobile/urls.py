# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('mobile.views',

    url(r'^mobile/cemetery/$', 'cemetery_list'),    
    url(r'^api/mobile/cemetery/(?P<pk>\d+)/photo/?$', 'cemetery_photo'),

    url(r'^mobile/area/$', 'area_list'),
    url(r'^mobile/place/$', 'place_list'),
    url(r'^api/mobile/place/(?P<place_id>\d+)/?$',
        'api_mobile_place', name='api_mobile_place'),
    url(r'^api/mobile/area/(?P<area_id>\d+)/places/?$',
        'api_mobile_area_places', name='api_mobile_area_places'),
    url(r'^mobile/grave/$', 'grave_list'),
    url(r'^mobile/burial/$', 'burial_list'),
    url(r'^mobile/placephoto/$', 'placephoto_list'),
    url(r'^mobile/placephoto/upload/$', 'placephoto_upload'),
    url(r'^mobile/cemetery/upload/$', 'cemetery_upload'),
    url(r'^mobile/area/upload/$', 'area_upload'),
    url(r'^mobile/grave/upload/$', 'grave_upload'),
    url(r'^mobile/burial/bind_burial_grave/$', 'bind_burial_grave'),
    url(r'^mobile/placephoto/delete/$', 'placephoto_delete'),

    url(r'^api/mobilekeeper/version/?$', 'api_mobilekeeper_version'),
)
