# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

#from django.views.generic import TemplateView # Django v1.5
from django.views.generic.simple import direct_to_template 

from rest_framework.urlpatterns import format_suffix_patterns

# from views import CemeteryList


urlpatterns = patterns('rest_api.views',
    #url(r'^$', TemplateView.as_view(template_name='base_angular.html'),), # v1.5
    #(r'^angular$', direct_to_template, {'template': 'base_angular.html'}),

)


urlpatterns += patterns('geo.views',
    url(r'^geo/country/list/$', 'country_list', name='country-list'),
    url(r'^geo/region/list/$',  'region_list',  name='region-list'),
    url(r'^geo/city/list/$',    'city_list',    name='city-list'),
    url(r'^geo/street/list/$',  'street_list',  name='street-list'),
)