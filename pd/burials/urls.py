# coding: utf-8

from django.conf.urls import url
from django.views.generic import TemplateView

from burials import views
from users.models import Org

urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),

    url(r'^burials/add_agent/$', views.add_agent, name='add_agent'),
    url(r'^burials/add_loru_agent/$', views.add_agent, dict(prefix='loru_'), name='add_agent'),
    url(r'^burials/add_dover/$', views.add_dover, name='add_dover'),
    url(r'^burials/add_loru_dover/$', views.add_dover, dict(prefix='loru_'), name='add_dover'),
    url(r'^burials/add_org/$', views.add_org, name='add_org'),
    url(r'^burials/add_zags/$', views.add_org, dict(type=Org.PROFILE_ZAGS), name='add_org'),
    url(r'^burials/add_medic/$', views.add_org, dict(type=Org.PROFILE_MEDIC), name='add_org'),
    url(r'^burials/add_loru/$', views.add_org, dict(type=Org.PROFILE_LORU), name='add_org'),
    url(r'^burials/add_doctype/$', views.add_doctype, name='add_doctype'),
    url(r'^burials/place/(?P<pk>\d+)/add_graves/$', views.add_graves, name='add_graves'),

    url(r'^burials/archive/$', views.archive, name='archive'),
    url(r'^burials/create/$', views.create_burial, name='create_burial'),
    url(r'^burials/get_place/$', views.get_place, name='get_place'),
    url(r'^burials/get_graves_number/$', views.get_graves_number, name='get_graves_number'),

    url(r'^burials/(?P<pk>\d+)/$', views.view_burial, name='view_burial'),
    url(r'^burials/(?P<pk>\d+)/edit/$', views.edit_burial, name='edit_burial'),
    url(r'^burials/(?P<pk>\d+)/notification/$', views.make_notification, name='make_notification'),
    url(r'^burials/(?P<pk>\d+)/spravka/$', views.make_spravka, name='make_spravka'),
    url(r'^burials/(?P<pk>\d+)/comment/$', views.burial_comment, name='burial_comment'),
    url(r'^burials/(?P<pk>\d+)/comments/edit/$', views.burials_comments_edit, name='burials_comments_edit'),
    url(r'^burials/(?P<pk>\d+)/exhumate/$', views.burial_exhumate, name='burial_exhumate'),
    url(r'^burials/(?P<pk>\d+)/exhumate/cancel/$', views.burial_cancel_exhumation, name='burial_cancel_exhumation'),
    url(r'^burials/(?P<pk>\d+)/exhumate/report/$', views.make_exhumate_report, name='make_exhumate_report'),
    url(r'^burials/(?P<pk>\d+)/exhumate/notification/$', views.make_exhumate_notification, name='make_exhumate_notification'),
    url(r'^burials/$', views.burial_list, name='burial_list'),
    url(r'^burials/search/$', views.burial_public_list, name='burial_public_list'),
    
    url(r'^burialfiles/(?P<pk>\d+)/delete/$', views.delete_burialfile, name='delete_burialfile'),
    url(r'^burialfiles/(?P<pk>\d+)/editcomment/$', views.edit_burialfile_comment, name='edit_burialfile_comment'),

    url(r'^places/(?P<pk>\d+)/certificate$', views.place_certificate, name='place_certificate'),

    url(r'^cemetery_personal_data/', views.cemetery_personal_data, name='cemetery_personal_data'),

    url(r'^cemetery_times/', views.cemetery_times, name='cemetery_times'),
    url(r'^autocomplete/cemeteries/', views.autocomplete_cemeteries, name='autocomplete_cemeteries'),
    url(r'^autocomplete/areas/', views.autocomplete_areas, name='autocomplete_areas'),

    # REST API
    url(r'^manage/cemetery$', TemplateView.as_view(template_name='base_angular.html'), name='manage_cemeteries'),

    url(r'^api/cemetery-editors/?$', views.api_cemeteries_editors, name='api_cemeteries_editors'),

    url(r'^api/oms/photo-places/?$', views.api_oms_photo_places, name='api_oms_photo_places'),
    url(r'^api/oms/photo-places/(?P<pk>\d+)/?$', views.api_oms_photo_places_change, name='api_oms_photo_places_change'),
    url(r'^api/oms/photo-places/place/(?P<pk>\d+)/?$', views.api_oms_photo_places_detail, name='api_oms_photo_places_detail'),
    url(r'^api/oms/photo-places/counts/?$', views.api_oms_photo_places_counts, name='api_oms_photo_places_counts'),

    url(r'^api/oms/cemeteries/?$', views.api_oms_cemeteries, name='api_oms_cemeteries'),
    url(r'^api/oms/cemeteries/(?P<pk>\d+)/areas/?$', views.api_oms_cemeteries_areas, name='api_oms_cemeteries_areas'),
    url(r'^api/oms/cemeteries/(?P<pk>\d+)/deleted_burials/?$',
        views.api_oms_cemeteries_deleted_burials, name='api_oms_cemeteries_deleted_burials'),
    url(r'^api/loru/cemeteries/?$', views.api_loru_cemeteries, name='api_loru_cemeteries'),
    url(r'^api/loru/cemeteries/(?P<pk>\d+)/areas/?$', views.api_loru_cemeteries_areas, name='api_loru_cemeteries_areas'),
    url(r'^api/oms/cemeteries/(?P<cemetery_pk>\d+)/areas/(?P<area_pk>\d+)/places/?$',
        views.api_oms_areas_places, name='api_oms_areas_places'),

    url(r'^api/oms/area/(?P<pk>\d+)/msaccess/sync/?$', views.api_oms_area_msaccess_sync,
        name='api_oms_area_msaccess_sync'),

    url(r'^api/oms/places/bounds/?$', views.api_oms_places_bounds, name='api_oms_places_bounds'),
    url(r'^api/oms/(?P<ugh_id>\d+)/places/clusters/?$', views.api_oms_places_clusters, name='api_oms_places_clusters'),

    url(r'^api/clients/(?P<token>[0-9a-f]+)/cemeteries/?$', views.api_client_site_cemeteries, name='api_client_site_cemeteries'),
    url(r'^api/clients/(?P<token>[0-9a-f]+)/burials-places/?$', views.api_client_site_places, name='api_client_site_places'),
    url(
        r'^api/clients/(?P<ugh_token>[0-9a-f]+)/burials-places/(?P<place_pk>\d+)/photos/?$',
        views.api_client_site_placephotos, name='api_client_site_placephotos'),
    url(r'^api/clients/(?P<token>[0-9a-f]+)/burials-places/(?P<pk>\d+)/?$',
        views.api_client_site_places_id, name='api_client_site_places_id'),

    url(r'^api/place/(?P<pk>\d+)/photo-upload/?$', views.api_place_photo_upload, name='api_place_photo_upload'),

    url(r'^burials/doubles/$', views.burials_doubles, name='burials_doubles'),
    url(r'^burials/double/$', views.burials_double, name='burials_double'),

    url(r'^burials/registry/$', views.burials_registry, name='burials_registry'),
]
