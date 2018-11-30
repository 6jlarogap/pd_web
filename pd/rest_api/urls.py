# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

from rest_framework.urlpatterns import format_suffix_patterns

# from views import CemeteryList


urlpatterns = patterns('rest_api.views',
)


urlpatterns += patterns('geo.views',
    url(r'^geo/country/list/$', 'country_list', name='country-list'),
    url(r'^geo/region/list/$',  'region_list',  name='region-list'),
    url(r'^geo/city/list/$',    'city_list',    name='city-list'),
    url(r'^geo/street/list/$',  'street_list',  name='street-list'),
)
