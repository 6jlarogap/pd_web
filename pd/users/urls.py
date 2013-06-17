# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('users.views',
    url(r'^login/', 'ulogin', name='ulogin'),
    url(r'^logout/', 'ulogout', name='ulogout'),

    url(r'^register/', 'uregister', name='uregister'),
    url(r'^profile/', 'profile', name='profile'),
    url(r'^loruregistry/', 'loru_registry', name='loru_registry'),
    url(r'^userprofile/', 'user_profile', name='user_profile'),

    url(r'^user/(?P<pk>\d+)/edit/', 'edit_user', name='edit_user'),
    url(r'^user/(?P<pk>\d+)/password/', 'change_password', name='change_password'),
    url(r'^user/create/', 'add_user', name='add_user'),

    url(r'^org/(?P<pk>\d+)/edit/', 'edit_org', name='edit_org'),

    url(r'^autocomplete/org/', 'autocomplete_org', name='autocomplete_org'),
)
