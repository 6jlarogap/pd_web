from django.urls import re_path
from django.conf import settings
from users import views

urlpatterns = [
    re_path(r'^login/', views.ulogin, name='ulogin'),
    re_path(r'^logout/', views.ulogout, name='ulogout'),

    re_path(r'^api/auth/signin/?$', views.api_auth_signin, name='api_auth_signin'),
    re_path(r'^api/auth/sessions/?$', views.api_auth_sessions, name='api_auth_sessions'),
    re_path(r'^api/auth/signup/?$', views.api_auth_signup, name='api_auth_signup'),
    re_path(r'^api/auth/signout/?$', views.api_auth_signout, name='api_auth_signout'),

    re_path(r'^api/user/?$', views.api_auth_user, name='api_auth_user'),
    re_path(r'^api/feedback/?$', views.api_feedback, name='api_feedback'),
    re_path(r'^api/balance/?$', views.api_balance, name='api_balance'),
    re_path(r'^api/auth/get_password_by_sms/?$', views.auth_get_password_by_sms, name='auth_get_password_by_sms'),

    re_path(r'^api/auth/cookies/?$', views.api_auth_cookies, name='api_auth_cookies'),

    re_path(r'^api/profile/?$', views.api_profile, name='api_profile'),
    re_path(r'^api/settings/?$', views.api_settings, name='api_settings'),

    re_path(r'^api/settings/oauth_providers/?$', views.api_settings_oauth_providers, name='api_settings_oauth_providers'),
    re_path(r'^api/settings/oauth_providers/(?P<provider>[A-Za-z0-9]+)/?$', views.api_settings_oauth_providers_delete,
         name='api_settings_oauth_providers_delete'),

    re_path(r'^api/loru/places/?$', views.api_loru_places, name='api_loru_places'),
    re_path(r'^api/(?:org|loru)/stores/?$', views.api_loru_stores, name='api_loru_stores'),
    re_path(r'^api/(?:org|loru)/stores/(?P<pk>[0-9]+)/?$', views.api_loru_store_detail, name='api_loru_store_detail'),

    re_path(r'^api/loru/favorite_suppliers/?$', views.api_loru_favorite_suppliers, name='api_loru_favorite_suppliers'),
    re_path(
        r'^api/loru/favorite_suppliers/(?P<supplier_id>[0-9]+)/?$',
        views.api_loru_favorite_suppliers_edit,
        name='api_loru_favorite_suppliers_edit'
    ),

    re_path(r'^api/catalog/suppliers/?$', views.api_catalog_suppliers, name='api_catalog_suppliers'),
    re_path(r'^api/catalog/suppliers/(?P<org_slug>[\w-]+)/?$', views.api_catalog_suppliers_detail, name='api_catalog_suppliers_detail'),

    re_path(r'^api/optplaces/suppliers/?$', views.api_optplaces_suppliers, name='api_optplaces_suppliers'),
    re_path(r'^api/optplaces/suppliers/(?P<pk>[0-9]+)/?$', views.api_optplaces_suppliers_detail, name='api_optplaces_suppliers_detail'),

    re_path(r'^api/shops/?$', views.api_shops, name='api_shops'),
    re_path(r'^api/shops/(?P<pk>[0-9]+)/gallery/?$', views.api_shops_gallery, name='api_shops_gallery'),
    re_path(r'^api/shops/(?P<pk>[\w-]+)/?$', views.api_shops_detail, name='api_shops_detail'),
    re_path(r'^api/shops/(?P<pk>[0-9]+)/reviews/?$', views.api_shops_reviews, name='api_shops_reviews'),

    re_path(r'^api/org/signup/?$', views.api_org_signup, name='api_org_signup'),

    re_path(r'^api/education/?$', views.api_education, name='api_education'),

    re_path(r'^testcaptcha2/$', views.testcaptcha2, name='testcaptcha2'),

    re_path(r'^register/$', views.register, name='register'),
    re_path(r'^register/(?P<key>[A-Za-z0-9]+)/activation/$', views.register_activation,
        name='register_activation'),
        
    re_path(r'^support/$', views.support, name='support'),
    re_path(r'^support/thanks/$', views.support_thanks, name='support_thanks'),
    re_path(r'^tutorial/$', views.tutorial, name='tutorial'),
    
    re_path(r'^registrants/$', views.registrants, name='registrants'),
    re_path(r'^registrant/(?P<pk>[0-9]+)/delete/$', views.registrant_delete, name='registrant_delete'),
    re_path(r'^registrant/(?P<pk>[0-9]+)/approve/$', views.registrant_approve, name='registrant_approve'),
    re_path(r'^registrant/(?P<pk>[0-9]+)/decline/$', views.registrant_decline, name='registrant_decline'),
    
    re_path(r'^oms_burialstats/', views.oms_burial_stats, name='oms_burial_stats'),
    re_path(r'^oms_currentstats/', views.oms_current_stats, name='oms_current_stats'),
    re_path(r'^oms_operstats/', views.oms_oper_stats, name='oms_oper_stats'),
    re_path(r'^loru_operstats/', views.loru_oper_stats, name='loru_oper_stats'),
    re_path(r'^loru_currentstats/', views.loru_current_stats, name='loru_current_stats'),
    re_path(r'^loru_orderstats/', views.loru_order_stats, name='loru_order_stats'),
        
    re_path(r'^loruregistry/$', views.loru_registry, name='loru_registry'),

    re_path(r'^userprofile/$', views.edit_profile, {'my_profile': True}, name='user_profile'),
    re_path(r'^profile/(?P<pk>[0-9]+)/edit/$', views.edit_profile, name='edit_profile'),
    re_path(r'^profile/create/$', views.edit_profile, name='create_profile'),

    re_path(r'^org/(?P<pk>[0-9]+)/edit/$', views.edit_org, name='edit_org'),
    re_path(r'^org/log/$', views.org_log, name='org_log'),
    re_path(r'^org/log_org/$', views.org_log_org, name='org_log_org'),

    re_path(r'^loginlog/$', views.login_log, name='login_log'),

    re_path(r'^api/clients/(?P<token>[0-9a-f]+)/details/?$', views.api_client_site_detail, name='api_client_site_detail'),
    re_path(r'^api/clients/(?P<token>[0-9a-f]+)/messages/?$', views.api_client_site_messages, name='api_client_site_messages'),
    re_path(r'^api/clients/(?P<token>[0-9a-f]+)/employees/?$', views.api_client_site_employees, name='api_client_site_employees'),

    re_path(r'^api/clients/(?P<token>[0-9a-f]+)/departments/?$', views.api_client_site_departments, name='api_client_site_departments'),

    re_path(r'^api/cabinet/getcode/?$', views.api_cabinet_getcode, name='api_cabinet_getcode'),
    re_path(r'^api/cabinet/tokens/?$', views.api_cabinet_tokens, name='api_cabinet_tokens'),
    re_path(r'^api/cabinet/users/(?P<pk>[0-9]+)/?$', views.api_cabinet_users, name='api_cabinet_users'),

    re_path(r'^api/cabinet/users/(?P<pk>[0-9]+)/oauth-providers/?$', views.api_cabinet_oauth, name='api_cabinet_oauth'),
    re_path(r'^api/cabinet/users/(?P<user_id>[0-9]+)/oauth-providers/(?P<oauth_id>[0-9]+)/?$',
        views.api_cabinet_oauth_detail, name='api_cabinet_oauth_detail'),

    re_path(r'^api/thank/users_count/?$', views.api_thank_users_count, name='api_thank_users_count'),
    re_path(r'^api/thank/users/?$', views.api_thank_users, name='api_thank_users'),
    re_path(r'^api/thank/(?P<pk>[0-9]+)/?$', views.api_thank_detail, name='api_thank_detail'),

    re_path(r'^thanks/?$', views.thanks, name='thanks'),

    re_path(r'^autocomplete/org/$', views.autocomplete_org, name='autocomplete_org'),
    re_path(r'^autocomplete/loru_in_burials/$', views.autocomplete_loru_in_burials, name='autocomplete_loru_in_burials'),
]
