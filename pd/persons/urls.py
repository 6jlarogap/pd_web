# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings


urlpatterns = patterns('persons.views',
    url(r'^autocomplete/fio/', 'autocomplete_fio', name='autocomplete_fio'),
    url(r'^autocomplete/alive/', 'autocomplete_alive', name='autocomplete_alive'),
    url(r'^autocomplete/firstname/', 'autocomplete_first_name', name='autocomplete_first_name'),
    url(r'^autocomplete/middlename/', 'autocomplete_middle_name', name='autocomplete_middle_name'),
    url(r'^autocomplete/docsources/', 'autocomplete_docsources', name='autocomplete_docsources'),

    url(r'^api/client/customplaces/?$', 'api_client_customplaces', name='api_client_customplaces'),
    url(r'^api/client/customplaces/(?P<pk>\d+)/?$', 'api_client_customplaces_detail', name='api_client_customplaces_detail'),
   
    url(r'^api/customperson/(?P<pk>\d+)/memory/?$', 'api_customperson_memory', name='api_customperson_memory'),
    url(r'^api/customperson/(?P<pk>\d+)/memory/gallery/?$', 'api_customperson_memory_gallery', name='api_customperson_memory_gallery'),
)
