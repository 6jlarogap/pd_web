# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('mobile.views',

    url(r'^mobile/getcemetery/$', 'mobile_get_cemetery', name='mobile_get_cemetery'),
    url(r'^mobile/getarea/$', 'mobile_get_area', name='mobile_get_area'),
    url(r'^mobile/getplace/$', 'mobile_get_place', name='mobile_get_place'),
    url(r'^mobile/getgrave/$', 'mobile_get_grave', name='mobile_get_grave'),
    url(r'^mobile/uploadphoto/$', 'mobile_upload_photo', name='mobile_upload_photo'),
    url(r'^mobile/uploadcemetery/$', 'mobile_upload_cemetery', name='mobile_upload_cemetery'),
    url(r'^mobile/uploadarea/$', 'mobile_upload_area', name='mobile_upload_area'),
    url(r'^mobile/uploadplace/$', 'mobile_upload_place', name='mobile_upload_place'),
    url(r'^mobile/uploadgrave/$', 'mobile_upload_grave', name='mobile_upload_grave'),

)
