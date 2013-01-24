# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('')

urlpatterns += patterns('orders.views',
    url(r'^create/$', 'new_order', name='new_order'),
    url(r'^(\d+)/add/$', 'new_order_item', name='new_order_item'),
)

