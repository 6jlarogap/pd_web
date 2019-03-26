from django.conf.urls import url
from import_burials import views

urlpatterns = [
    url(r'^import/minsk/$', views.import_minsk, name='import_minsk'),
    url(r'^import/burials_minsk/$', views.import_burials_minsk, name='import_burials_minsk'),
]
