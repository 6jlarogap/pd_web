# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('mobile.views',

    url(r'^mobile/hello/$', 'mobile_hello', name='mobile_hello'),

)
