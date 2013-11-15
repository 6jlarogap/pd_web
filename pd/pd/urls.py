# coding: utf-8

from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
from django.conf import settings

#from django.views.generic import TemplateView # Django v1.5
from django.views.generic.simple import direct_to_template 
 

from django.contrib import admin
admin.autodiscover()

from rest_framework.routers import DefaultRouter
router = DefaultRouter(trailing_slash=False)



from geo.views import LocationViewSet, LocationStaticViewSet

from burials.views import CemeteryViewSet, AreaViewSet, PlaceViewSet, \
    GraveViewSet, BurialViewSet, AreaPhotoViewSet, GravePhotoViewSet, AreaPurposeViewSet

from persons.views import AlivePersonViewSet, DeadPersonViewSet, PhoneViewSet 
from logs.views import LogViewSet
 
# Burial
router.register(r'^api/log', LogViewSet)
router.register(r'^api/cemetery', CemeteryViewSet)
router.register(r'^api/area', AreaViewSet)
router.register(r'^api/place', PlaceViewSet)

router.register(r'^api/place', PlaceViewSet)
router.register(r'^api/grave', GraveViewSet)
router.register(r'^api/burial', BurialViewSet)
router.register(r'^api/grave-photo', GravePhotoViewSet)
router.register(r'^api/area-photo', AreaPhotoViewSet)
router.register(r'^api/area-purpose', AreaPurposeViewSet)

router.register(r'^api/alive-person', AlivePersonViewSet)
router.register(r'^api/dead-person', DeadPersonViewSet)

router.register(r'^api/alive-person-phone', PhoneViewSet)



# Geo
router.register(r'^api/geo/location', LocationViewSet)
router.register(r'^api/geo/location/static', LocationStaticViewSet)

urlpatterns = patterns('',
    url(r'^thumb/', include('restthumbnails.urls')),
)

urlpatterns += patterns('pd.views',
    url(r'^favicon\.ico$',
        RedirectView.as_view(url='{0}img/favicon16x16.ico'.format(settings.STATIC_URL))),
    url(r'^', include('users.urls')),
    url(r'^', include('burials.urls')),
    url(r'^', include('persons.urls')),
    url(r'^', include('orders.urls')),
    url(r'^', include('reports.urls')),
    url(r'^', include('mobile.urls')),
    url(r'^geo/', include('geo.urls')),
    url(r'^import/', include('import_burials.urls')),
    
    url(r'^api/', include('rest_api.urls')),
    url(r'^', include(router.urls)),
)

# Redirects. Move into nginx at production
urlpatterns += patterns('rest_api.views',
    url(r'^api$', 'api_root'),
    url(r'^manage/404$', 'base_page'),
    url(r'^manage/500$', 'base_page'),
    url(r'^manage/cemetery/$', 'base_page'),
    url(r'^manage/cemetery/(?P<id>.*)$', 'base_page'),
    url(r'^manage/area/(?P<id>.*)$', 'base_page'),
    url(r'^manage/place/(?P<id>.*)$', 'base_page'),
)

# Для включения административных функций (http://.../admin)
# добавить параметр ADMIN_ENABLED  в pd/local_settings.py (!)
# и установить его в True
#
if 'ADMIN_ENABLED' in dir(settings) and settings.ADMIN_ENABLED:
    urlpatterns += patterns('',
        url(r'^admin/jsi18n/', 'django.views.i18n.javascript_catalog'),
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', include(admin.site.urls)),
    )

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
