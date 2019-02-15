# coding: utf-8

from django.conf.urls import url
from mobile import views

urlpatterns = [
    url(r'^mobile/cemetery/$', views.cemetery_list),    
    url(r'^api/mobile/cemetery/(?P<pk>\d+)/photo/?$', views.cemetery_photo),
    url(r'^api/mobile/cemetery/(?P<pk>\d+)/schema/?$', views.cemetery_schema),

    url(r'^mobile/area/$', views.area_list),
    url(r'^mobile/place/$', views.place_list),
    url(r'^api/mobile/place/(?P<place_id>\d+)/?$', views.api_mobile_place),
    url(r'^api/mobile/area/(?P<area_id>\d+)/places/?$', views.api_mobile_area_places),
    url(r'^api/mobile/grave/?$', views.api_mobile_grave),
    url(r'^mobile/burial/$', views.burial_list),
    url(r'^api/mobile/burials/?$', views.api_mobile_burials),
    url(r'^mobile/cemetery/upload/$', views.cemetery_upload),
    url(r'^mobile/area/upload/$', views.area_upload),
    url(r'^mobile/grave/upload/$', views.grave_upload),
    url(r'^mobile/burial/bind_burial_grave/$', views.bind_burial_grave),

    url(r'^mobile/placephoto/$', views.placephoto_list),
    url(r'^mobile/placephoto/upload/$', views.placephoto_upload),
    url(r'^mobile/placephoto/delete/$', views.placephoto_delete),

    url(r'^api/mobilekeeper/version/?$', views.api_mobilekeeper_version),
]
