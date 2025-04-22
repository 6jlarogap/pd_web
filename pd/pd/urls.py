from django.urls import include, re_path, path
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve
from django.conf import settings

from django.contrib import admin
from django.templatetags.static import static

from rest_framework.routers import DefaultRouter
router = DefaultRouter(trailing_slash=False)

from geo.views import LocationViewSet, LocationStaticViewSet
from rest_api.views import base_page, api_root
from pd.views import media_xsendfile

from burials.views import CemeteryViewSet, AreaViewSet, PlaceViewSet, \
    GraveViewSet, BurialViewSet, AreaPhotoViewSet, AreaPurposeViewSet, \
    PlaceSizeViewSet, ApiOmsPlacesViewSet, ApiCatalogPlacesViewSet

from persons.views import AlivePersonViewSet, DeadPersonViewSet, PhoneViewSet 
from logs.views import LogViewSet
from orders.views import ProductsViewSet, ProductsOptViewSet, UghPublishedProductsViewSet

# Burial
router.register(r'^api/log', LogViewSet, basename='api-log-viewset')
router.register(r'^api/cemetery', CemeteryViewSet, basename='api-cemetery-viewset')
router.register(r'^api/area', AreaViewSet, basename='api-area-viewset')
router.register(r'^api/place', PlaceViewSet, basename='api-place-viewset')
router.register(r'^api/grave', GraveViewSet, basename='api-grave-viewset')
router.register(r'^api/burial', BurialViewSet, basename='api-burial-viewset')
router.register(r'^api/area-photo', AreaPhotoViewSet, basename='api-areaphoto-viewset')
router.register(r'^api/area-purpose', AreaPurposeViewSet, basename='api-area-purpose-viewset')
router.register(r'^api/oms/places', ApiOmsPlacesViewSet, basename='api-oms-places-viewset')
router.register(r'^api/catalog/places', ApiCatalogPlacesViewSet, basename='api-catalog-place-viewset')

router.register(r'^api/alive-person', AlivePersonViewSet, basename='api-aliveperson-viewset')
router.register(r'^api/dead-person', DeadPersonViewSet, basename='api-deadperson-viewset')

router.register(r'^api/alive-person-phone', PhoneViewSet, basename='api-aliveperson-phone-viewset')
router.register(r'^api/placesize', PlaceSizeViewSet, basename='api-placesize-viewset')

# Orders
router.register(r'^api/catalog/products/?$', ProductsViewSet, basename='api-catalog-categories-viewset')
router.register(r'^api/loru/products', UghPublishedProductsViewSet)
router.register(r'^api/optplaces/suppliers/(?P<loru_pk>[0-9]+)/products/?$', ProductsOptViewSet, basename='api-optplaces-suppliers-viewset')

# Geo
router.register(r'^api/geo/location', LocationViewSet, basename='api-geo-location-viewset')
router.register(r'^api/geo/location/static', LocationStaticViewSet, basename='api-geo-location-static-viewset')

urlpatterns = [
    re_path(r'^favicon\.ico$',
        RedirectView.as_view(url=static('img/favicon16x16.ico'), permanent=True)),
    re_path(r'^thumb/', include('pd.restthumbnails_urls')),

    path('', include('users.urls')),
    path('', include('burials.urls')),
    path('', include('persons.urls')),
    path('', include('orders.urls')),
    path('', include('reports.urls')),
    path('', include('mobile.urls')),
    path('', include('geo.urls')),
    path('', include('import_burials.urls')),
    path('', include('halls.urls')),
    
    path('', include(router.urls)),
]

# Redirects. Move into nginx at production
urlpatterns += [
    re_path(r'^api$', api_root),
    re_path(r'^manage/404$', base_page),
    re_path(r'^manage/500$', base_page),
    re_path(r'^manage/cemetery/$', base_page),
    re_path(r'^manage/cemetery/(?P<id>.*)$', base_page),
    re_path(r'^manage/area/(?P<id>.*)$', base_page),
    re_path(r'^manage/place/(?P<id>.*)$', base_page),
]

js_locale_kwargs = dict()
if settings.SPECIFIC_RU_LOCALE_APP:
    js_locale_kwargs['packages'] = [settings.SPECIFIC_RU_LOCALE_APP, ]

urlpatterns += [
    re_path(r'^jsi18n/$', JavaScriptCatalog.as_view(**js_locale_kwargs), name='jsi18n'),
]

# Для включения административных функций (http://.../admin)
# добавить параметр ADMIN_ENABLED  в pd/local_settings.py (!)
# и установить его в True
#
if 'ADMIN_ENABLED' in dir(settings) and settings.ADMIN_ENABLED:
    urlpatterns += [
        re_path(r'^admin/jsi18n/', JavaScriptCatalog.as_view()),
        re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        re_path(r'^admin/', admin.site.urls),
    ]

urlpatterns += [
    #
    # re_path(r'^media/(?P<path>.*)$',  'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    #
    # Здесь django.views.static.serve заменена на свою функцию
    # pd.views.media_xsendfile, которая проверяет, работаем ли мы под сервером Apache и если да,
    # то проверяем доступ к media файлу. Если проверки успешны, то Apache с mod_xsendfile
    # передает media файл клиенту.
    # Если работаем не под сервером Apache, а пока это только из ./manage.py runserver, то 
    # управление передается на django.views.static.serve, но это без проверок доступа к файлу
    #
    re_path(r'^media/(?P<path>.*)$', media_xsendfile, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += [
            re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]
    from debug_toolbar import urls as debug_urls
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_urls)),
    ]
