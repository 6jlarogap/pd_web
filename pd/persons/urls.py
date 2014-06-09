# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings


urlpatterns = patterns('persons.views',
    url(r'^autocomplete/fio/', 'autocomplete_fio', name='autocomplete_fio'),
    url(r'^autocomplete/alive/', 'autocomplete_alive', name='autocomplete_alive'),
    url(r'^autocomplete/firstname/', 'autocomplete_first_name', name='autocomplete_first_name'),
    url(r'^autocomplete/middlename/', 'autocomplete_middle_name', name='autocomplete_middle_name'),
    url(r'^autocomplete/docsources/', 'autocomplete_docsources', name='autocomplete_docsources'),

    url(r'^api/places/?$', 'api_places', name='api_places'),
   
)
