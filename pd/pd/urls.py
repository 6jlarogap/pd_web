# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('')

urlpatterns += patterns('pd.views',
    url(r'^$', 'main_page', name='main_page'),
    url(r'^create/$', 'new_burial', name='new_burial'),
    url(r'^create/place/$', 'new_burial_place', name='new_burial_place'),
    url(r'^create/person/$', 'new_burial_person', name='new_burial_person'),
    url(r'^create/agent/$', 'new_agent', name='new_agent'),
    url(r'^create/dover/$', 'new_dover', name='new_dover'),
    url(r'^create/customer/$', 'new_burial_customer', name='new_burial_customer'),
    url(r'^create/responsible/$', 'new_burial_responsible', name='new_burial_responsible'),

    url(r'^edit/(?P<pk>\d+)/$', 'edit_burial', name='edit_burial'),

    url(r'^print/(?P<pk>\d+)/$', 'print_burial', name='print_burial'),
    url(r'^print/(?P<pk>\d+)/notification/$', 'print_notification', name='print_notification'),
    url(r'^print/cats/$', 'print_catafalques', name='print_catafalques'),

    url(r'^burial/(?P<pk>[^/]*)/$', 'view_burial', name='view_burial'),
    url(r'^burial/(?P<pk>[^/]*)/comment/$', 'add_comment', name='add_comment'),
    url(r'^place/(?P<pk>[^/]*)/$', 'view_place', name='view_place'),
    url(r'^comment/(?P<pk>[^/]*)/delete/$', 'delete_comment', name='delete_comment'),

    url(r'^management/user/$', 'management_user', name='management_user'),
    url(r'^management/org/$', 'management_org', name='management_org'),
    url(r'^management/cemetery/$', 'management_cemetery', name='management_cemetery'),

    url(r'^autocomplete/person/$', 'autocomplete_person', name='autocomplete_person'),
    url(r'^autocomplete/doc_source/$', 'autocomplete_doc_source', name='autocomplete_doc_source'),

    url(r'^profile/$', 'profile', name='profile'),

    url(r'^login/$', 'ulogin', name='ulogin'),
    url(r'^logout/$', 'ulogout', name='ulogout'),

    url(r'^geo/', include('geo.urls')),
)

urlpatterns += patterns('',
    url(r'^admin/jsi18n/', 'django.views.i18n.javascript_catalog'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('registration.views',
    url(r'^accounts/register/$', 'register', {'backend': 'pd.reg_backend.OrgRegBackend'}, name='registration_register'),
    url(r'^accounts/', include('registration.backends.default.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
