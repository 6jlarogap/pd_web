from django.urls import re_path
from django.conf import settings

from persons import views

urlpatterns = [
    re_path(r'^autocomplete/fio_order/', views.autocomplete_fio_order, name='autocomplete_fio_order'),
    re_path(r'^autocomplete/fio/', views.autocomplete_fio, name='autocomplete_fio'),
    re_path(r'^autocomplete/alive/', views.autocomplete_alive, name='autocomplete_alive'),
    re_path(r'^autocomplete/(?P<what>firstname|middlename)/', views.autocomplete_name, name='autocomplete_name'),
    re_path(r'^autocomplete/docsources/', views.autocomplete_docsources, name='autocomplete_docsources'),

    re_path(r'^api/persons/autocomplete/?$', views.api_autocomplete_persons, name='api_autocomplete_persons'),
    
    re_path(r'^api/client/places/?$', views.api_client_places, name='api_client_places'),
    re_path(r'^api/client/places/(?P<pk>\d+)/?$', views.api_client_places_detail, name='api_client_places_detail'),
    re_path(r'^api/client/places/(?P<pk>\d+)/deadmans/?$', views.api_client_places_deadmans, name='api_client_places_deadmans'),
    re_path(r'^api/client/places/(?P<pk>\d+)/attachments/?$', views.api_client_places_attachments, name='api_client_places_attachments'),
    re_path(r'^api/client/places/(?P<pk>\d+)/deadmans/(?P<deadman_pk>\d+)/?$',
                    views.api_client_places_deadmans_detail, name='api_client_places_deadmans_detail'),
    re_path(r'^api/client/places/(?P<pk>\d+)/orders/?$', views.api_client_places_orders, name='api_client_places_orders'),

    re_path(r'^api/client/deadmans/?$', views.api_client_deadmans, name='api_client_deadmans'),

    re_path(r'^api/client/persons/?$', views.api_client_persons, name='api_client_persons'),
    re_path(r'^api/client/persons/(?P<pk>\d+)/?$', views.api_client_persons_detail, name='api_client_persons_detail'),

    re_path(r'^api/custompersons/(?P<pk>\d+)/?$', views.api_customperson_detail, name='api_customperson_detail'),
    re_path(r'^api/custompersons/(?P<pk>\d+)/memories/?$', views.api_customperson_memory_gallery, name='api_customperson_memory_gallery'),
    re_path(r'^api/custompersons/(?P<pk>\d+)/memories/(?P<memory_pk>\d+)/?$',
        views.api_customperson_memory_gallery_detail, name='api_customperson_memory_gallery_detail'),

    re_path(r'^api/oms/burials/?$', views.api_oms_burials, name='api_oms_burials'),
    re_path(r'^api/oms/burials/(?P<pk>\d+)/?$', views.api_oms_burials_detail, name='api_oms_burials_detail'),
]
