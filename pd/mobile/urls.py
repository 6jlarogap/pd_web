# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('mobile.views',

    url(r'^api/mobile/cemetery/$', 'cemetery_list'),    
    url(r'^api/mobile/area/$', 'area_list'),
    url(r'^api/mobile/place/$', 'place_list'),
    url(r'^api/mobile/grave/$', 'grave_list'),
    url(r'^api/mobile/burial/$', 'burial_list'),
    url(r'^api/mobile/gravephoto/upload/$', 'gravephoto_upload'),
    url(r'^api/mobile/placephoto/upload/$', 'placephoto_upload'),
    url(r'^api/mobile/cemetery/upload/$', 'cemetery_upload'),
    url(r'^api/mobile/area/upload/$', 'area_upload'),
    url(r'^api/mobile/place/upload/$', 'place_upload'),
    url(r'^api/mobile/grave/upload/$', 'grave_upload'),
    url(r'^api/mobile/gravephoto/delete/$', 'gravephoto_delete'),
    url(r'^api/mobile/placephoto/delete/$', 'placephoto_delete'),

)
