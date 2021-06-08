from django.urls import re_path
from mobile import views

urlpatterns = [
    re_path(r'^mobile/cemetery/$', views.cemetery_list),    
    re_path(r'^api/mobile/cemetery/(?P<pk>\d+)/photo/?$', views.cemetery_photo),
    re_path(r'^api/mobile/cemetery/(?P<pk>\d+)/schema/?$', views.cemetery_schema),

    re_path(r'^mobile/area/$', views.area_list),
    re_path(r'^mobile/place/$', views.place_list),
    re_path(r'^api/mobile/place/(?P<place_id>\d+)/?$', views.api_mobile_place),
    re_path(r'^api/mobile/area/(?P<area_id>\d+)/places/?$', views.api_mobile_area_places),
    re_path(r'^api/mobile/grave/?$', views.api_mobile_grave),
    re_path(r'^mobile/burial/$', views.burial_list),
    re_path(r'^api/mobile/burials/?$', views.api_mobile_burials),
    re_path(r'^mobile/cemetery/upload/$', views.cemetery_upload),
    re_path(r'^mobile/area/upload/$', views.area_upload),
    re_path(r'^mobile/grave/upload/$', views.grave_upload),
    re_path(r'^mobile/burial/bind_burial_grave/$', views.bind_burial_grave),

    re_path(r'^mobile/placephoto/$', views.placephoto_list),
    re_path(r'^mobile/placephoto/upload/$', views.placephoto_upload),
    re_path(r'^mobile/placephoto/delete/$', views.placephoto_delete),

    re_path(r'^api/mobilekeeper/version/?$', views.api_mobilekeeper_version),
]
