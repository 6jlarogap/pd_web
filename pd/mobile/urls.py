# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('mobile.views',

    url(r'^mobile/getcemetery/$', 'mobile_get_cemetery', name='mobile_get_cemetery'),
    url(r'^mobile/getarea/$', 'mobile_get_area', name='mobile_get_area'),
    url(r'^mobile/getplace/$', 'mobile_get_place', name='mobile_get_place'),
    url(r'^mobile/getgrave/$', 'mobile_get_grave', name='mobile_get_grave'),
    url(r'^mobile/getburial/$', 'mobile_get_burial', name='mobile_get_burial'),
    url(r'^mobile/uploadgravephoto/$', 'mobile_upload_gravephoto', name='mobile_upload_gravephoto'),
    url(r'^mobile/uploadplacephoto/$', 'mobile_upload_placephoto', name='mobile_upload_placephoto'),
    url(r'^mobile/uploadcemetery/$', 'mobile_upload_cemetery', name='mobile_upload_cemetery'),
    url(r'^mobile/uploadarea/$', 'mobile_upload_area', name='mobile_upload_area'),
    url(r'^mobile/uploadplace/$', 'mobile_upload_place', name='mobile_upload_place'),
    url(r'^mobile/uploadgrave/$', 'mobile_upload_grave', name='mobile_upload_grave'),
    url(r'^mobile/removegravephoto/$', 'mobile_remove_gravephoto', name='mobile_remove_gravephoto'),
    url(r'^mobile/removeplacephoto/$', 'mobile_remove_placephoto', name='mobile_remove_placephoto'),

)
