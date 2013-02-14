# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('orders.views',
    url(r'^manage/product/$', 'manage_products', name='manage_products'),
    url(r'^manage/product/create/$', 'manage_products_create', name='manage_products_create'),
    url(r'^manage/product/(?P<pk>\d+)/edit/$', 'manage_products_edit', name='manage_products_edit'),
)
