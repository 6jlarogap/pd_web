# coding: utf-8

from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
from django.conf import settings


from django.contrib import admin
# - django 1.7 no need - admin.autodiscover()

from rest_framework.routers import DefaultRouter
router = DefaultRouter(trailing_slash=False)



from geo.views import LocationViewSet, LocationStaticViewSet

from burials.views import CemeteryViewSet, AreaViewSet, PlaceViewSet, \
    GraveViewSet, BurialViewSet, AreaPhotoViewSet, AreaPurposeViewSet, \
    PlaceSizeViewSet, ApiOmsPlacesViewSet, ApiCatalogPlacesViewSet

from persons.views import AlivePersonViewSet, DeadPersonViewSet, PhoneViewSet 
from logs.views import LogViewSet
from orders.views import ProductCategoryViewSet, ProductsViewSet, ProductsOptViewSet, \
                         UghPublishedProductsViewSet
from users.views import auth_get_password_by_sms, \
                        api_feedback, api_auth_user, api_balance

# Burial
router.register(r'^api/log', LogViewSet)
router.register(r'^api/cemetery', CemeteryViewSet)
router.register(r'^api/area', AreaViewSet)
router.register(r'^api/place', PlaceViewSet)

router.register(r'^api/place', PlaceViewSet)
router.register(r'^api/grave', GraveViewSet)
router.register(r'^api/burial', BurialViewSet)
router.register(r'^api/area-photo', AreaPhotoViewSet)
router.register(r'^api/area-purpose', AreaPurposeViewSet)
router.register(r'^api/oms/places', ApiOmsPlacesViewSet)
router.register(r'^api/catalog/places', ApiCatalogPlacesViewSet)

router.register(r'^api/alive-person', AlivePersonViewSet)
router.register(r'^api/dead-person', DeadPersonViewSet)

router.register(r'^api/alive-person-phone', PhoneViewSet)
router.register(r'^api/placesize', PlaceSizeViewSet)

# Orders
router.register(r'^api/catalog/categories', ProductCategoryViewSet)
router.register(r'^api/catalog/products/?$', ProductsViewSet)

router.register(r'^api/loru/products', UghPublishedProductsViewSet)

router.register(r'^api/optplaces/suppliers/(?P<loru_pk>\d+)/products/?$', ProductsOptViewSet)

# Geo
router.register(r'^api/geo/location', LocationViewSet)
router.register(r'^api/geo/location/static', LocationStaticViewSet)

urlpatterns = patterns('',
    url(r'^thumb/', include('pd.restthumbnails_urls')),
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
    
    url(r'^api/feedback/?$', api_feedback),
    url(r'^api/user/?$', api_auth_user),
    url(r'^api/auth/get_password_by_sms/?$', auth_get_password_by_sms),
    
    url(r'^api/balance', api_balance),

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

# Заглушка
js_locale_packages = ('django.conf', )
if settings.SPECIFIC_RU_LOCALE_APP:
    # 'locale_by' для Беларуси
    js_locale_packages = (settings.SPECIFIC_RU_LOCALE_APP, )
js_info_dict = {
    'packages': js_locale_packages,
}

urlpatterns += patterns('',
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict, name='jsi18n'),
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

urlpatterns += patterns('',
    #
    # url(r'^media/(?P<path>.*)$',  'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    #
    # Здесь django.views.static.serve заменена на свою функцию
    # pd.views.media_xsendfile, которая проверяет, работаем ли мы под сервером Apache и если да,
    # то проверяем доступ к media файлу. Если проверки успешны, то Apache с mod_xsendfile
    # передает media файл клиенту.
    # Если работаем не под сервером Apache, а пока это только из ./manage.py runserver, то 
    # управление передается на django.views.static.serve, но это без проверок доступа к файлу
    #
    url(r'^media/(?P<path>.*)$',  'pd.views.media_xsendfile', {'document_root': settings.MEDIA_ROOT}),
)

if settings.DEBUG:
    urlpatterns += patterns('',
            url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
