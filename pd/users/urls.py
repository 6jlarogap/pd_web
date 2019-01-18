# coding: utf-8

from django.conf.urls import url
from django.conf import settings
from users import views

urlpatterns = [
    url(r'^login/', views.ulogin, name='ulogin'),
    url(r'^logout/', views.ulogout, name='ulogout'),

    url(r'^api/auth/signin/?$', views.api_auth_signin, name='api_auth_signin'),
    url(r'^api/auth/sessions/?$', views.api_auth_sessions, name='api_auth_sessions'),
    url(r'^api/auth/signup/?$', views.api_auth_signup, name='api_auth_signup'),
    url(r'^api/auth/signout/?$', views.api_auth_signout, name='api_auth_signout'),

    url(r'^api/user/?$', views.api_auth_user, name='api_auth_user'),
    url(r'^api/feedback/?$', views.api_feedback, name='api_feedback'),
    url(r'^api/balance/?$', views.api_balance, name='api_balance'),
    url(r'^api/auth/get_password_by_sms/?$', views.auth_get_password_by_sms, name='auth_get_password_by_sms'),

    url(r'^api/auth/cookies/?$', views.api_auth_cookies, name='api_auth_cookies'),

    url(r'^api/profile/?$', views.api_profile, name='api_profile'),
    url(r'^api/settings/?$', views.api_settings, name='api_settings'),

    url(r'^api/settings/oauth_providers/?$', views.api_settings_oauth_providers, name='api_settings_oauth_providers'),
    url(r'^api/settings/oauth_providers/(?P<provider>[A-Za-z0-9]+)/?$', views.api_settings_oauth_providers_delete,
         name='api_settings_oauth_providers_delete'),

    url(r'^api/loru/places/?$', views.api_loru_places, name='api_loru_places'),
    url(r'^api/(?:org|loru)/stores/?$', views.api_loru_stores, name='api_loru_stores'),
    url(r'^api/(?:org|loru)/stores/(?P<pk>\d+)/?$', views.api_loru_store_detail, name='api_loru_store_detail'),

    url(r'^api/loru/favorite_suppliers/?$', views.api_loru_favorite_suppliers, name='api_loru_favorite_suppliers'),
    url(
        r'^api/loru/favorite_suppliers/(?P<supplier_id>\d+)/?$',
        views.api_loru_favorite_suppliers_edit,
        name='api_loru_favorite_suppliers_edit'
    ),

    url(r'^api/catalog/suppliers/?$', views.api_catalog_suppliers, name='api_catalog_suppliers'),
    url(r'^api/catalog/suppliers/(?P<org_slug>[\w-]+)/?$', views.api_catalog_suppliers_detail, name='api_catalog_suppliers_detail'),

    url(r'^api/optplaces/suppliers/?$', views.api_optplaces_suppliers, name='api_optplaces_suppliers'),
    url(r'^api/optplaces/suppliers/(?P<pk>\d+)/?$', views.api_optplaces_suppliers_detail, name='api_optplaces_suppliers_detail'),

    url(r'^api/shops/?$', views.api_shops, name='api_shops'),
    url(r'^api/shops/(?P<pk>\d+)/gallery/?$', views.api_shops_gallery, name='api_shops_gallery'),
    url(r'^api/shops/(?P<pk>[\w-]+)/?$', views.api_shops_detail, name='api_shops_detail'),
    url(r'^api/shops/(?P<pk>\d+)/reviews/?$', views.api_shops_reviews, name='api_shops_reviews'),

    url(r'^api/org/signup/?$', views.api_org_signup, name='api_org_signup'),

    url(r'^api/education/?$', views.api_education, name='api_education'),

    url(r'^testcaptcha2/$', views.testcaptcha2, name='testcaptcha2'),

    url(r'^register/$', views.register, name='register'),
    url(r'^register/(?P<key>[A-Za-z0-9]+)/activation/$', views.register_activation,
        name='register_activation'),
        
    url(r'^support/$', views.support, name='support'),
    url(r'^support/thanks/$', views.support_thanks, name='support_thanks'),
    url(r'^tutorial/$', views.tutorial, name='tutorial'),
    
    url(r'^registrants/$', views.registrants, name='registrants'),
    url(r'^registrant/(?P<pk>\d+)/delete/$', views.registrant_delete, name='registrant_delete'),
    url(r'^registrant/(?P<pk>\d+)/approve/$', views.registrant_approve, name='registrant_approve'),
    url(r'^registrant/(?P<pk>\d+)/decline/$', views.registrant_decline, name='registrant_decline'),
    
    url(r'^oms_burialstats/', views.oms_burial_stats, name='oms_burial_stats'),
    url(r'^oms_currentstats/', views.oms_current_stats, name='oms_current_stats'),
    url(r'^oms_operstats/', views.oms_oper_stats, name='oms_oper_stats'),
    url(r'^loru_currentstats/', views.loru_current_stats, name='loru_current_stats'),
    url(r'^loru_orderstats/', views.loru_order_stats, name='loru_order_stats'),
        
    url(r'^loruregistry/$', views.loru_registry, name='loru_registry'),

    url(r'^userprofile/$', views.edit_profile, {'my_profile': True}, name='user_profile'),
    url(r'^profile/(?P<pk>\d+)/edit/$', views.edit_profile, name='edit_profile'),
    url(r'^profile/create/$', views.edit_profile, name='create_profile'),

    url(r'^org/(?P<pk>\d+)/edit/$', views.edit_org, name='edit_org'),
    url(r'^org/log/$', views.org_log, name='org_log'),
    url(r'^org/log_org/$', views.org_log_org, name='org_log_org'),

    url(r'^loginlog/$', views.login_log, name='login_log'),

    url(r'^api/clients/(?P<token>[0-9a-f]+)/details/?$', views.api_client_site_detail, name='api_client_site_detail'),
    url(r'^api/clients/(?P<token>[0-9a-f]+)/messages/?$', views.api_client_site_messages, name='api_client_site_messages'),
    url(r'^api/clients/(?P<token>[0-9a-f]+)/employees/?$', views.api_client_site_employees, name='api_client_site_employees'),

    url(r'^api/clients/(?P<token>[0-9a-f]+)/departments/?$', views.api_client_site_departments, name='api_client_site_departments'),

    url(r'^api/cabinet/getcode/?$', views.api_cabinet_getcode, name='api_cabinet_getcode'),
    url(r'^api/cabinet/tokens/?$', views.api_cabinet_tokens, name='api_cabinet_tokens'),
    url(r'^api/cabinet/users/(?P<pk>\d+)/?$', views.api_cabinet_users, name='api_cabinet_users'),

    url(r'^api/cabinet/users/(?P<pk>\d+)/oauth-providers/?$', views.api_cabinet_oauth, name='api_cabinet_oauth'),
    url(r'^api/cabinet/users/(?P<user_id>\d+)/oauth-providers/(?P<oauth_id>\d+)/?$',
        views.api_cabinet_oauth_detail, name='api_cabinet_oauth_detail'),

    url(r'^api/thank/users_count/?$', views.api_thank_users_count, name='api_thank_users_count'),
    url(r'^api/thank/users/?$', views.api_thank_users, name='api_thank_users'),
    url(r'^api/thank/(?P<pk>\d+)/?$', views.api_thank_detail, name='api_thank_detail'),

    url(r'^api/videos/?$', views.api_videos, name='api_videos'),
    url(r'^api/videos/(?P<yid>\S+)/votes/?$', views.api_video_votes, name='api_video_votes'),
    url(r'^api/videos/(?P<yid>\S+)/aggregated-votes/?$', views.api_video_aggregated_votes, name='api_video_aggregated_votes'),
    url(r'^api/videos/(?P<yid>\S+)/statistics/?$', views.api_video_statistics, name='api_video_statistics'),
    url(r'^api/videos/(?P<yid>\S+)/statistics/current-user-time-votes/?$',
        views.api_video_statistics_current_user, name='api_video_statistics_current_user'),
    url(r'^api/videos/(?P<yid>\S+)/subtitles/?$', views.api_video_subtitles, name='api_video_subtitles'),
    url(r'^api/videos/(?P<yid>\S+)/subtitles-votes/?$', views.api_video_subtitles_votes, name='api_video_subtitles_votes'),
    url(r'^api/videos/(?P<yid>\S+)/timestamps/(?P<second>\d+)/voters/?$',
            views.api_video_timestamps_votes, name='api_video_timestamps_votes'),
    url(r'^videos/?$', views.videos, name='videos'),
    # Здесь обязательно '/' в конце шаблона, ибо '/' подпадает под \S+
    url(r'^api/videos/(?P<yid>\S+)/$', views.api_video_detail, name='api_video_detail'),

    url(r'^thanks/?$', views.thanks, name='thanks'),

    url(r'^api/vk/bot/(?P<group>\w+)/handler/?$', views.api_vk_bot_handler, name='api_vk_bot_handler'),

    url(r'^autocomplete/org/$', views.autocomplete_org, name='autocomplete_org'),
    url(r'^autocomplete/loru_in_burials/$', views.autocomplete_loru_in_burials, name='autocomplete_loru_in_burials'),
]
