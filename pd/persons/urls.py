# coding: utf-8

from django.conf.urls import url
from django.conf import settings

from persons import views

urlpatterns = [
    url(r'^autocomplete/fio_order/', views.autocomplete_fio_order, name='autocomplete_fio_order'),
    url(r'^autocomplete/fio/', views.autocomplete_fio, name='autocomplete_fio'),
    url(r'^autocomplete/alive/', views.autocomplete_alive, name='autocomplete_alive'),
    url(r'^autocomplete/(?P<what>firstname|middlename)/', views.autocomplete_name, name='autocomplete_name'),
    url(r'^autocomplete/docsources/', views.autocomplete_docsources, name='autocomplete_docsources'),

    url(r'^api/persons/autocomplete/?$', views.api_autocomplete_persons, name='api_autocomplete_persons'),
    
    url(r'^api/client/places/?$', views.api_client_places, name='api_client_places'),
    url(r'^api/client/places/(?P<pk>\d+)/?$', views.api_client_places_detail, name='api_client_places_detail'),
    url(r'^api/client/places/(?P<pk>\d+)/deadmans/?$', views.api_client_places_deadmans, name='api_client_places_deadmans'),
    url(r'^api/client/places/(?P<pk>\d+)/attachments/?$', views.api_client_places_attachments, name='api_client_places_attachments'),
    url(r'^api/client/places/(?P<pk>\d+)/deadmans/(?P<deadman_pk>\d+)/?$',
                    views.api_client_places_deadmans_detail, name='api_client_places_deadmans_detail'),
    url(r'^api/client/places/(?P<pk>\d+)/orders/?$', views.api_client_places_orders, name='api_client_places_orders'),

    url(r'^api/client/deadmans/?$', views.api_client_deadmans, name='api_client_deadmans'),

    url(r'^api/client/persons/?$', views.api_client_persons, name='api_client_persons'),
    url(r'^api/client/persons/(?P<pk>\d+)/?$', views.api_client_persons_detail, name='api_client_persons_detail'),

    url(r'^api/custompersons/(?P<pk>\d+)/?$', views.api_customperson_detail, name='api_customperson_detail'),
    url(r'^api/custompersons/(?P<pk>\d+)/memories/?$', views.api_customperson_memory_gallery, name='api_customperson_memory_gallery'),
    url(r'^api/custompersons/(?P<pk>\d+)/memories/(?P<memory_pk>\d+)/?$',
        views.api_customperson_memory_gallery_detail, name='api_customperson_memory_gallery_detail'),

    url(r'^api/oms/burials/?$', views.api_oms_burials, name='api_oms_burials'),
    url(r'^api/oms/burials/(?P<pk>\d+)/?$', views.api_oms_burials_detail, name='api_oms_burials_detail'),
]
