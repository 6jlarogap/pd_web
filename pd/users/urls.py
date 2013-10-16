# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('users.views',
    url(r'^login/', 'ulogin', name='ulogin'),
    url(r'^logout/', 'ulogout', name='ulogout'),

    url(r'^register-old/$', 'register_old', name='register_old'),
    
    # Внимание: все URLs, которые re.match(r'^/?register(?:/|$)')
    # не требуют входа пользователя в систему,
    # см. pd/middleware.py.LoginRequiredMiddleware.
    # register_old требует не просто входа пользователя, а супервизора!
    #
    url(r'^register/$', 'register', name='register'),
    url(r'^register/(?P<key>[A-Za-z0-9]+)/activation/$', 'register_activation',
        name='register_activation'),
        
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
)
