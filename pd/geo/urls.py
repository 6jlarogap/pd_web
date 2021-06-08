from django.urls import re_path
from geo import views

urlpatterns = [
    re_path(r'^geo/autocomplete/country/$', views.autocomplete_countries, name='autocomplete_countries'),
    re_path(r'^geo/autocomplete/region/$', views.autocomplete_regions, name='autocomplete_regions'),
    re_path(r'^geo/autocomplete/city/$', views.autocomplete_cities, name='autocomplete_cities'),
    re_path(r'^geo/autocomplete/street/$', views.autocomplete_streets, name='autocomplete_streets'),

    re_path(r'^api/geo/country/list/$', views.country_list, name='country-list'),
    re_path(r'^api/geo/region/list/$',  views.region_list,  name='region-list'),
    re_path(r'^api/geo/city/list/$',    views.city_list,    name='city-list'),
    re_path(r'^api/geo/street/list/$',  views.street_list,  name='street-list'),
]
