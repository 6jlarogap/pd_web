# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('orders.views',
    url(r'^manage/product/$', 'manage_products', name='manage_products'),
    url(r'^manage/product/create/$', 'manage_products_create', name='manage_products_create'),
    url(r'^manage/product/(?P<pk>\d+)/edit/$', 'manage_products_edit', name='manage_products_edit'),

    url(r'^order/$', 'order_list', name='order_list'),
    url(r'^order/create/$', 'order_create', name='order_create'),
    url(r'^order/(?P<pk>\d+)/edit/$', 'order_edit', name='order_edit'),
    url(r'^order/(?P<pk>\d+)/print/$', 'order_print', name='order_print'),
)
