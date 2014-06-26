# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('orders.views',
    url(r'^manage/product/$', 'manage_products', name='manage_products'),
    url(r'^manage/product/create/$', 'manage_products_create', name='manage_products_create'),
    url(r'^manage/product/(?P<pk>\d+)/edit/$', 'manage_products_edit', name='manage_products_edit'),

    url(r'^order/$', 'order_list', name='order_list'),
    url(r'^order/create/$', 'order_create', name='order_create'),
    url(r'^order/(?P<pk>\d+)/applicant/$', 'order_edit', name='order_edit'),
    url(r'^order/(?P<pk>\d+)/products/$', 'order_products', name='order_products'),
    url(r'^order/(?P<pk>\d+)/burial/$', 'order_burial', name='order_burial'),
    url(r'^order/(?P<pk>\d+)/services/$', 'order_services', name='order_services'),
    url(r'^order/(?P<pk>\d+)/info/$', 'order_info', name='order_info'),
    url(r'^order/(?P<pk>\d+)/print/$', 'order_print', name='order_print'),
    url(r'^order/(?P<pk>\d+)/contract/$', 'order_contract', name='order_contract'),
    url(r'^order/(?P<pk>\d+)/comment/$', 'order_comment', name='order_comment'),
    url(r'^order/(?P<pk>\d+)/annulate/$', 'order_annulate', name='order_annulate'),

    url(r'^api/catalog/suppliers/?$', 'api_catalog_suppliers', name='api_catalog_suppliers'),

    url(r'^api/loru/product_places/?$', 'api_loru_product_places', name='api_loru_product_places'),

    url(r'^order/product/ajax_get_product_price/$', 'ajax_product_price', name='ajax_product_price'),
)
