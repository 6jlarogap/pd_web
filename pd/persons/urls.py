# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('persons.views',
    url(r'^autocomplete/fio/', 'autocomplete_fio', name='autocomplete_fio'),
    url(r'^autocomplete/alive/', 'autocomplete_alive', name='autocomplete_alive'),
)
