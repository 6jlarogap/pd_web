# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('geo.views',
    url(r'^autocomplete/country/$', 'autocomplete_countries', name='autocomplete_countries'),
    url(r'^autocomplete/region/$', 'autocomplete_regions', name='autocomplete_regions'),
    url(r'^autocomplete/city/$', 'autocomplete_cities', name='autocomplete_cities'),
    url(r'^autocomplete/street/$', 'autocomplete_streets', name='autocomplete_streets'),
)
