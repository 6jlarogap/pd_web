# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings


urlpatterns = patterns('persons.views',
    url(r'^autocomplete/fio/', 'autocomplete_fio', name='autocomplete_fio'),
    url(r'^autocomplete/alive/', 'autocomplete_alive', name='autocomplete_alive'),
    url(r'^autocomplete/firstname/', 'autocomplete_first_name', name='autocomplete_first_name'),
    url(r'^autocomplete/middlename/', 'autocomplete_middle_name', name='autocomplete_middle_name'),
    url(r'^autocomplete/docsources/', 'autocomplete_docsources', name='autocomplete_docsources'),
    
    url(r'^api/client/places/?$', 'api_client_places', name='api_client_places'),
    url(r'^api/client/places/(?P<pk>\d+)/?$', 'api_client_places_detail', name='api_client_places_detail'),
    url(r'^api/client/places/(?P<pk>\d+)/deadmans/?$', 'api_client_places_deadmans', name='api_client_places_deadmans'),
    url(r'^api/client/places/(?P<pk>\d+)/attachments/?$', 'api_client_places_attachments', name='api_client_places_attachments'),
    url(r'^api/client/places/(?P<pk>\d+)/deadmans/(?P<deadman_pk>\d+)/?$',
                    'api_client_places_deadmans_detail', name='api_client_places_deadmans_detail'),
    url(r'^api/client/places/(?P<pk>\d+)/orders/?$', 'api_client_places_orders', name='api_client_places_orders'),

    url(r'^api/client/deadmans/?$', 'api_client_deadmans', name='api_client_deadmans'),

    url(r'^api/custompersons/(?P<pk>\d+)/?$', 'api_customperson_detail', name='api_customperson_detail'),
    url(r'^api/custompersons/(?P<pk>\d+)/memories/?$', 'api_customperson_memory_gallery', name='api_customperson_memory_gallery'),
    url(r'^api/custompersons/(?P<pk>\d+)/gallery/?$', 'api_customperson_memory_photo', name='api_customperson_memory_photo'),
)
