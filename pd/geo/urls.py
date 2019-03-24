from django.conf.urls import url
from geo import views

urlpatterns = [
    url(r'^geo/autocomplete/country/$', views.autocomplete_countries, name='autocomplete_countries'),
    url(r'^geo/autocomplete/region/$', views.autocomplete_regions, name='autocomplete_regions'),
    url(r'^geo/autocomplete/city/$', views.autocomplete_cities, name='autocomplete_cities'),
    url(r'^geo/autocomplete/street/$', views.autocomplete_streets, name='autocomplete_streets'),

    url(r'^api/geo/country/list/$', views.country_list, name='country-list'),
    url(r'^api/geo/region/list/$',  views.region_list,  name='region-list'),
    url(r'^api/geo/city/list/$',    views.city_list,    name='city-list'),
    url(r'^api/geo/street/list/$',  views.street_list,  name='street-list'),
]
