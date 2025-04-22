from django.urls import re_path
from django.views.generic import TemplateView

from burials import views
from users.models import Org

urlpatterns = [
    re_path(r'^$', views.dashboard, name='dashboard'),

    re_path(r'^burials/add_agent/$', views.add_agent, name='add_agent'),
    re_path(r'^burials/add_loru_agent/$', views.add_agent, dict(prefix='loru_'), name='add_agent'),
    re_path(r'^burials/add_dover/$', views.add_dover, name='add_dover'),
    re_path(r'^burials/add_loru_dover/$', views.add_dover, dict(prefix='loru_'), name='add_dover'),
    re_path(r'^burials/add_org/$', views.add_org, name='add_org'),
    re_path(r'^burials/add_zags/$', views.add_org, dict(type=Org.PROFILE_ZAGS), name='add_org'),
    re_path(r'^burials/add_medic/$', views.add_org, dict(type=Org.PROFILE_MEDIC), name='add_org'),
    re_path(r'^burials/add_loru/$', views.add_org, dict(type=Org.PROFILE_LORU), name='add_org'),
    re_path(r'^burials/add_doctype/$', views.add_doctype, name='add_doctype'),
    re_path(r'^burials/place/(?P<pk>[0-9]+)/add_graves/$', views.add_graves, name='add_graves'),

    re_path(r'^burials/archive/$', views.archive, name='archive'),
    re_path(r'^burials/create/$', views.create_burial, name='create_burial'),
    re_path(r'^burials/get_place/$', views.get_place, name='get_place'),
    re_path(r'^burials/get_graves_number/$', views.get_graves_number, name='get_graves_number'),

    re_path(r'^burials/(?P<pk>[0-9]+)/$', views.view_burial, name='view_burial'),
    re_path(r'^burials/(?P<pk>[0-9]+)/edit/$', views.edit_burial, name='edit_burial'),
    re_path(r'^burials/(?P<pk>[0-9]+)/notification/$', views.make_notification, name='make_notification'),
    re_path(r'^burials/(?P<pk>[0-9]+)/spravka/$', views.make_spravka, name='make_spravka'),
    re_path(r'^burials/(?P<pk>[0-9]+)/comment/$', views.burial_comment, name='burial_comment'),
    re_path(r'^burials/(?P<pk>[0-9]+)/comments/edit/$', views.burials_comments_edit, name='burials_comments_edit'),
    re_path(r'^burials/(?P<pk>[0-9]+)/exhumate/$', views.burial_exhumate, name='burial_exhumate'),
    re_path(r'^burials/(?P<pk>[0-9]+)/exhumate/cancel/$', views.burial_cancel_exhumation, name='burial_cancel_exhumation'),
    re_path(r'^burials/(?P<pk>[0-9]+)/exhumate/report/$', views.make_exhumate_report, name='make_exhumate_report'),
    re_path(r'^burials/(?P<pk>[0-9]+)/exhumate/notification/$', views.make_exhumate_notification, name='make_exhumate_notification'),
    re_path(r'^burials/$', views.burial_list, name='burial_list'),
    re_path(r'^burials/search/$', views.burial_public_list, name='burial_public_list'),
    
    re_path(r'^burialfiles/(?P<pk>[0-9]+)/delete/$', views.delete_burialfile, name='delete_burialfile'),
    re_path(r'^burialfiles/(?P<pk>[0-9]+)/editcomment/$', views.edit_burialfile_comment, name='edit_burialfile_comment'),

    re_path(r'^places/(?P<pk>[0-9]+)/certificate$', views.place_certificate, name='place_certificate'),

    re_path(r'^cemetery_personal_data/', views.cemetery_personal_data, name='cemetery_personal_data'),

    re_path(r'^cemetery_times/', views.cemetery_times, name='cemetery_times'),
    re_path(r'^autocomplete/cemeteries/', views.autocomplete_cemeteries, name='autocomplete_cemeteries'),
    re_path(r'^autocomplete/areas/', views.autocomplete_areas, name='autocomplete_areas'),

    # REST API
    re_path(r'^manage/cemetery$', TemplateView.as_view(template_name='base_angular.html'), name='manage_cemeteries'),

    re_path(r'^api/cemetery-editors/?$', views.api_cemeteries_editors, name='api_cemeteries_editors'),

    re_path(r'^api/oms/photo-places/?$', views.api_oms_photo_places, name='api_oms_photo_places'),
    re_path(r'^api/oms/photo-places/(?P<pk>[0-9]+)/?$', views.api_oms_photo_places_change, name='api_oms_photo_places_change'),
    re_path(r'^api/oms/photo-places/place/(?P<pk>[0-9]+)/?$', views.api_oms_photo_places_detail, name='api_oms_photo_places_detail'),
    re_path(r'^api/oms/photo-places/counts/?$', views.api_oms_photo_places_counts, name='api_oms_photo_places_counts'),

    re_path(r'^api/oms/cemeteries/?$', views.api_oms_cemeteries, name='api_oms_cemeteries'),
    re_path(r'^api/oms/cemeteries/(?P<pk>[0-9]+)/areas/?$', views.api_oms_cemeteries_areas, name='api_oms_cemeteries_areas'),
    re_path(r'^api/oms/cemeteries/(?P<pk>[0-9]+)/deleted_burials/?$',
        views.api_oms_cemeteries_deleted_burials, name='api_oms_cemeteries_deleted_burials'),
    re_path(r'^api/loru/cemeteries/?$', views.api_loru_cemeteries, name='api_loru_cemeteries'),
    re_path(r'^api/loru/cemeteries/(?P<pk>[0-9]+)/areas/?$', views.api_loru_cemeteries_areas, name='api_loru_cemeteries_areas'),
    re_path(r'^api/oms/cemeteries/(?P<cemetery_pk>[0-9]+)/areas/(?P<area_pk>[0-9]+)/places/?$',
        views.api_oms_areas_places, name='api_oms_areas_places'),

    re_path(r'^api/oms/area/(?P<pk>[0-9]+)/msaccess/sync/?$', views.api_oms_area_msaccess_sync,
        name='api_oms_area_msaccess_sync'),

    re_path(r'^api/oms/places/bounds/?$', views.api_oms_places_bounds, name='api_oms_places_bounds'),
    re_path(r'^api/oms/(?P<ugh_id>[0-9]+)/places/clusters/?$', views.api_oms_places_clusters, name='api_oms_places_clusters'),

    re_path(r'^api/clients/(?P<token>[0-9a-f]+)/cemeteries/?$', views.api_client_site_cemeteries, name='api_client_site_cemeteries'),
    re_path(r'^api/clients/(?P<token>[0-9a-f]+)/burials-places/?$', views.api_client_site_places, name='api_client_site_places'),
    re_path(
        r'^api/clients/(?P<ugh_token>[0-9a-f]+)/burials-places/(?P<place_pk>[0-9]+)/photos/?$',
        views.api_client_site_placephotos, name='api_client_site_placephotos'),
    re_path(r'^api/clients/(?P<token>[0-9a-f]+)/burials-places/(?P<pk>[0-9]+)/?$',
        views.api_client_site_places_id, name='api_client_site_places_id'),

    re_path(r'^api/place/(?P<pk>[0-9]+)/photo-upload/?$', views.api_place_photo_upload, name='api_place_photo_upload'),

    re_path(r'^burials/doubles/$', views.burials_doubles, name='burials_doubles'),
    re_path(r'^burials/double/$', views.burials_double, name='burials_double'),

    re_path(r'^burials/registry/$', views.burials_registry, name='burials_registry'),
]
