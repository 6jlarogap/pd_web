from django.urls import re_path
from orders import views

urlpatterns = [
    re_path(r'^manage/product/$', views.manage_products, name='manage_products'),
    re_path(r'^manage/product/create/$', views.manage_products_create, name='manage_products_create'),
    re_path(r'^manage/product/(?P<pk>\d+)/edit/$', views.manage_products_edit, name='manage_products_edit'),

    re_path(r'^order/$', views.order_list, name='order_list'),
    re_path(r'^order/create/$', views.order_create, name='order_create'),
    re_path(r'^order/(?P<pk>\d+)/$', views.order_edit, name='order_go_edit'),
    re_path(r'^order/(?P<pk>\d+)/applicant/$', views.order_edit, name='order_edit'),
    re_path(r'^order/(?P<pk>\d+)/products/$', views.order_products, name='order_products'),
    re_path(r'^order/(?P<pk>\d+)/burial/$', views.order_burial, name='order_burial'),
    re_path(r'^order/(?P<pk>\d+)/services/$', views.order_services, name='order_services'),
    re_path(r'^order/(?P<pk>\d+)/info/$', views.order_info, name='order_info'),
    re_path(r'^order/(?P<pk>\d+)/print/$', views.order_print, name='order_print'),
    re_path(r'^order/(?P<pk>\d+)/receipt/print/$', views.order_receipt_print, name='order_receipt_print'),
    re_path(r'^order/(?P<pk>\d+)/contract/$', views.order_contract, name='order_contract'),
    re_path(r'^order/(?P<pk>\d+)/comment/$', views.order_comment, name='order_comment'),
    re_path(r'^order/(?P<pk>\d+)/annulate/$', views.order_annulate, {'referer': 'edit'}, name='order_annulate'),
    re_path(r'^order/(?P<pk>\d+)/annulate_from_list/$', views.order_annulate, {'referer': 'list'}, name='order_annulate_from_list'),

    re_path(r'^product/xlsxreport/$', views.product_xlsxreport, name='product_xlsxreport'),

    re_path(r'^api/order/(?P<what>paid|advanced)/(?P<pk>\d+)/status/?$', views.api_order_status, name='api_order_status'),

    re_path(r'^api/loru/product_places/?$', views.api_loru_product_places, name='api_loru_product_places'),

    re_path(r'^api/loru/product_types/?$', views.api_loru_product_types, name='api_loru_product_types'),
    re_path(r'^api/loru/products_management/products/?$', views.api_product_list, name='api_product_list'),
    re_path(r'^api/loru/products_management/products/(?P<pk>\d+)/?$', views.api_product_detail, name='api_product_detail'),

    re_path(r'^api/loru/orders/?$', views.api_loru_orders, name='api_loru_orders'),
    re_path(r'^api/loru/orders/(?P<pk>\d+)/?$', views.api_loru_orders_detail, name='api_loru_orders_detail'),
    re_path(r'^api/loru/categories/?$', views.api_loru_categories, name='api_loru_categories'),

    re_path(r'^api/catalog/products/(?P<product_slug>[\w-]+)/?$', views.api_catalog_products_detail, name='api_catalog_products_detail'),
    re_path(r'^api/catalog/categories/?$', views.api_catalog_categories, name='api_catalog_categories'),

    re_path(r'^api/optplaces/orders/?$', views.api_optplaces_orders, name='api_optplaces_orders'),
    re_path(r'^api/optplaces/orders/(?P<pk>\d+)/?$', views.api_optplaces_orders_detail, name='api_optplaces_orders_detail'),

    re_path(r'^api/services/?$', views.api_services, name='api_services'),
    re_path(r'^api/org/(?P<org_id>\d+)/services/?$', views.api_org_services, name='api_org_services'),
    re_path(r'^api/org/(?P<org_id>\d+)/services/(?P<service_name>\w+)/?$', views.api_org_services_edit, name='api_org_services_edit'),

    re_path(r'^api/client/available_performers/?$', views.api_client_available_performers, name='api_client_available_performers'),
    re_path(r'^api/client/orders/?$', views.api_client_orders, name='api_client_orders'),
    re_path(r'^api/client/orders/(?P<pk>\d+)/?$', views.api_client_orders_put_status, name='api_client_orders_put_status'),
    re_path(r'^api/client/orders/(?P<pk>\d+)/payments/?$', views.api_client_orders_payments, name='api_client_orders_payments'),

    re_path(r'^api/orders/?$', views.api_orders, name='api_orders'),
    re_path(r'^api/orders/(?P<pk>\d+)/comments/?$', views.api_orders_comments, name='api_orders_comments'),
    re_path(r'^api/orders/(?P<pk>\d+)/results/?$', views.api_orders_results, name='api_orders_results'),
    re_path(r'^api/orders/(?P<pk>\d+)/results/(?P<result_pk>\d+)/?$',
        views.api_orders_results_detail, name='api_orders_results_detail'),

    re_path(r'^api/orders/(?P<pk>\d+)/?$', views.api_orders_detail, name='api_orders_detail'),
    re_path(r'^api/orders/(?P<pk>\d+)/payment_methods/(?P<pay_system>[\w-]+)/?$', views.api_orders_payments, name='api_orders_payments'),

    re_path(r'^order/product/ajax_get_product_price/$', views.ajax_product_price, name='ajax_product_price'),

    re_path(r'^api/orders/(?P<pk>\d+)/webpay/notify/?$', views.api_orders_webpay_notify, name='api_orders_webpay_notify'),

    re_path(r'^api/shops/(?P<org_pk>\d+)/places/(?P<customplace_pk>\d+)/?$', views.api_shops_places, name='api_shops_places'),
]
