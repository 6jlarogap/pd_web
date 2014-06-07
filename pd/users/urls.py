# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('users.views',
    url(r'^login/', 'ulogin', name='ulogin'),
    url(r'^logout/', 'ulogout', name='ulogout'),

    url(r'^api/auth/signin/?$', 'api_auth_signin', name='api_auth_signin'),
    url(r'^api/auth/signup/?$', 'api_auth_signup', name='api_auth_signup'),
    url(r'^api/auth/signout/?$', 'api_auth_signout', name='api_auth_signout'),

    url(r'^api/settings/oauth_providers/?$', 'api_settings_oauth_providers', name='api_settings_oauth_providers'),

    url(r'^api/loru/places/?$', 'api_loru_places', name='api_loru_places'),
    url(r'^api/loru/stores/?$', 'api_loru_stores', name='api_loru_stores'),
    url(r'^api/loru/stores/(?P<pk>\d+)/?$', 'api_loru_store_detail', name='api_loru_store_detail'),

    url(r'^api/education/?$', 'api_education', name='api_education'),

    url(r'^registration-old/$', 'registration_old', name='registration_old'),
    
    url(r'^testcaptcha/$', 'testcaptcha', name='testcaptcha'),

    url(r'^register/$', 'register', name='register'),
    url(r'^register/(?P<key>[A-Za-z0-9]+)/activation/$', 'register_activation',
        name='register_activation'),
        
    url(r'^support/$', 'support', name='support'),
    url(r'^support/thanks/$', 'support_thanks', name='support_thanks'),
    url(r'^tutorial$', 'tutorial', name='tutorial'),
    
    url(r'^registrants/$', 'registrants', name='registrants'),
    url(r'^registrant/(?P<pk>\d+)/delete/$', 'registrant_delete', name='registrant_delete'),
    url(r'^registrant/(?P<pk>\d+)/approve/$', 'registrant_approve', name='registrant_approve'),
    url(r'^registrant/(?P<pk>\d+)/decline/$', 'registrant_decline', name='registrant_decline'),
    
    url(r'^orgburialstats/', 'org_burial_stats', name='org_burial_stats'),
    url(r'^currentstats/', 'org_current_stats', name='org_current_stats'),
        
    url(r'^profile/', 'profile', name='profile'),
    url(r'^loruregistry/', 'loru_registry', name='loru_registry'),
    url(r'^userprofile/', 'user_profile', name='user_profile'),

    url(r'^user/(?P<pk>\d+)/edit/', 'edit_user', name='edit_user'),
    url(r'^user/(?P<pk>\d+)/password/', 'change_password', name='change_password'),
    url(r'^user/create/', 'add_user', name='add_user'),

    url(r'^org/(?P<pk>\d+)/edit/', 'edit_org', name='edit_org'),
    url(r'^org/log/$', 'org_log', name='org_log'),

    url(r'^loginlog/$', 'login_log', name='login_log'),

    url(r'^autocomplete/org/', 'autocomplete_org', name='autocomplete_org'),
    url(r'^autocomplete/loru_in_burials/', 'autocomplete_loru_in_burials', name='autocomplete_loru_in_burials'),
)
