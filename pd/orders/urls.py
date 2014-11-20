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

    url(r'^api/loru/product_places/?$', 'api_loru_product_places', name='api_loru_product_places'),

    url(r'^api/loru/product_types/?$', 'api_loru_product_types', name='api_loru_product_types'),
    url(r'^api/loru/products_management/products/?$', 'api_product_list', name='api_product_list'),
    url(r'^api/loru/products_management/products/(?P<pk>\d+)/?$', 'api_product_detail', name='api_product_detail'),

    url(r'^api/catalog/products/(?P<product_slug>[\w-]+)/?$', 'api_catalog_products_detail', name='api_catalog_products_detail'),

    url(r'^api/optplaces/orders/?$', 'api_optplaces_orders', name='api_optplaces_orders'),
    url(r'^api/optplaces/orders/(?P<pk>\d+)/?$', 'api_optplaces_orders_detail', name='api_optplaces_orders_detail'),

    url(r'^api/profile/?$', 'api_profile', name='api_profile'),

    url(r'^api/services/?$', 'api_services', name='api_services'),
    url(r'^api/org/(?P<org_id>\d+)/services/?$', 'api_org_services', name='api_org_services'),
    url(r'^api/org/(?P<org_id>\d+)/services/(?P<service_name>\w+)/?$', 'api_org_services_edit', name='api_org_services_edit'),

    url(r'^api/client/available_performers/?$', 'api_client_available_performers', name='api_client_available_performers'),
    url(r'^api/client/orders/?$', 'api_client_orders', name='api_client_orders'),
    url(r'^api/client/orders/(?P<pk>\d+)/?$', 'api_client_orders_rate', name='api_client_orders_rate'),

    url(r'^api/orders/?$', 'api_orders', name='api_orders'),
    url(r'^api/orders/(?P<pk>\d+)/comments/?$', 'api_orders_comments', name='api_orders_comments'),
    url(r'^api/orders/(?P<pk>\d+)/results/?$', 'api_orders_results', name='api_orders_results'),
    url(r'^api/orders/(?P<pk>\d+)/?$', 'api_orders_detail', name='api_orders_detail'),

    url(r'^order/product/ajax_get_product_price/$', 'ajax_product_price', name='ajax_product_price'),
)
