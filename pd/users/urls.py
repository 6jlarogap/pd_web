# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('users.views',
    url(r'^login/', 'ulogin', name='ulogin'),
    url(r'^logout/', 'ulogout', name='ulogout'),
    url(r'^register/', 'uregister', name='uregister'),
)
