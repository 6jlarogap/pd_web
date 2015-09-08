# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('users.views',
    url(r'^login/', 'ulogin', name='ulogin'),
    url(r'^logout/', 'ulogout', name='ulogout'),

    url(r'^api/auth/signin/?$', 'api_auth_signin', name='api_auth_signin'),
    url(r'^api/auth/sessions/?$', 'api_auth_sessions', name='api_auth_sessions'),
    url(r'^api/auth/signup/?$', 'api_auth_signup', name='api_auth_signup'),
    url(r'^api/auth/signout/?$', 'api_auth_signout', name='api_auth_signout'),

    url(r'^api/profile/?$', 'api_profile', name='api_profile'),
    url(r'^api/settings/?$', 'api_settings', name='api_settings'),

    url(r'^api/settings/oauth_providers/?$', 'api_settings_oauth_providers', name='api_settings_oauth_providers'),
    url(r'^api/settings/oauth_providers/(?P<provider>[A-Za-z0-9]+)$', 'api_settings_oauth_providers_delete',
         name='api_settings_oauth_providers_delete'),

    url(r'^api/loru/places/?$', 'api_loru_places', name='api_loru_places'),
    url(r'^api/loru/stores/?$', 'api_loru_stores', name='api_loru_stores'),
    url(r'^api/loru/stores/(?P<pk>\d+)/?$', 'api_loru_store_detail', name='api_loru_store_detail'),

    url(r'^api/loru/favorite_suppliers/?$', 'api_loru_favorite_suppliers', name='api_loru_favorite_suppliers'),
    url(
        r'^api/loru/favorite_suppliers/(?P<supplier_id>\d+)/?$',
        'api_loru_favorite_suppliers_edit',
        name='api_loru_favorite_suppliers_edit'
    ),

    url(r'^api/catalog/suppliers/?$', 'api_catalog_suppliers', name='api_catalog_suppliers'),
    url(r'^api/catalog/suppliers/(?P<org_slug>[\w-]+)/?$', 'api_catalog_suppliers_detail', name='api_catalog_suppliers_detail'),

    url(r'^api/optplaces/suppliers/?$', 'api_optplaces_suppliers', name='api_optplaces_suppliers'),
    url(r'^api/optplaces/suppliers/(?P<pk>\d+)/?$', 'api_optplaces_suppliers_detail', name='api_optplaces_suppliers_detail'),

    url(r'^api/shops/?$', 'api_shops', name='api_shops'),
    url(r'^api/shops/(?P<pk>\d+)/gallery/?$', 'api_shops_gallery', name='api_shops_gallery'),
    url(r'^api/shops/(?P<pk>[\w-]+)/?$', 'api_shops_detail', name='api_shops_detail'),
    url(r'^api/shops/(?P<pk>\d+)/reviews/?$', 'api_shops_reviews', name='api_shops_reviews'),

    url(r'^api/org/signup/?$', 'api_org_signup', name='api_org_signup'),

    url(r'^api/education/?$', 'api_education', name='api_education'),

    url(r'^registration-old/$', 'registration_old', name='registration_old'),
    
    url(r'^testcaptcha/$', 'testcaptcha', name='testcaptcha'),

    url(r'^register/$', 'register', name='register'),
    url(r'^register/(?P<key>[A-Za-z0-9]+)/activation/$', 'register_activation',
        name='register_activation'),
        
    url(r'^support/$', 'support', name='support'),
    url(r'^support/thanks/$', 'support_thanks', name='support_thanks'),
    url(r'^tutorial/$', 'tutorial', name='tutorial'),
    
    url(r'^registrants/$', 'registrants', name='registrants'),
    url(r'^registrant/(?P<pk>\d+)/delete/$', 'registrant_delete', name='registrant_delete'),
    url(r'^registrant/(?P<pk>\d+)/approve/$', 'registrant_approve', name='registrant_approve'),
    url(r'^registrant/(?P<pk>\d+)/decline/$', 'registrant_decline', name='registrant_decline'),
    
    url(r'^oms_burialstats/', 'oms_burial_stats', name='oms_burial_stats'),
    url(r'^oms_currentstats/', 'oms_current_stats', name='oms_current_stats'),
    url(r'^loru_currentstats/', 'loru_current_stats', name='loru_current_stats'),
    url(r'^loru_orderstats/', 'loru_order_stats', name='loru_order_stats'),
        
    url(r'^profile/$', 'profile', name='profile'),
    url(r'^loruregistry/', 'loru_registry', name='loru_registry'),
    url(r'^userprofile/', 'user_profile', name='user_profile'),

    url(r'^profile/(?P<pk>\d+)/edit/', 'edit_profile', name='edit_profile'),
    url(r'^profile/create/', 'edit_profile', name='create_profile'),
    url(r'^user/(?P<pk>\d+)/edit/', 'edit_user', name='edit_user'),
    url(r'^user/(?P<pk>\d+)/password/', 'change_password', name='change_password'),
    url(r'^user/create/', 'add_user', name='add_user'),

    url(r'^org/(?P<pk>\d+)/edit/', 'edit_org', name='edit_org'),
    url(r'^org/log/$', 'org_log', name='org_log'),

    url(r'^loginlog/$', 'login_log', name='login_log'),

    url(r'^autocomplete/org/', 'autocomplete_org', name='autocomplete_org'),
    url(r'^autocomplete/loru_in_burials/', 'autocomplete_loru_in_burials', name='autocomplete_loru_in_burials'),
)
