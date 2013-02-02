# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('persons.views',
    url(r'^create_deadman/(?P<br_pk>\d+)/$', 'create_deadman', name='create_deadman'),
    url(r'^create_responsible/(?P<br_pk>\d+)/$', 'create_responsible', name='create_responsible'),
)
