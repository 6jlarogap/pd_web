from django.conf.urls import url
from import_burials import views

urlpatterns = [
    url(r'^import/$', views.import_forms, name='import_forms'),
    url(r'^import/orgs/$', views.import_orgs, name='import_orgs'),
    url(r'^import/burials/$', views.import_burials, name='import_burials'),
    url(r'^import/kaluga/$', views.import_kaluga, name='import_kaluga'),
    url(r'^import/minsk/$', views.import_minsk, name='import_minsk'),
    url(r'^import/burials_minsk/$', views.import_burials_minsk, name='import_burials_minsk'),
    url(r'^import/services/$', views.import_services, name='import_services'),
    url(r'^import/orders/$', views.import_orders, name='import_orders'),
    url(r'^import/banks/$', views.import_banks, name='import_banks'),
    url(r'^import/docs/$', views.import_docs, name='import_docs'),
    url(r'^import/dcs/$', views.import_dcs, name='import_dcs'),
]
