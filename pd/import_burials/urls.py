from django.urls import re_path
from import_burials import views

urlpatterns = [
    re_path(r'^import/minsk/$', views.import_minsk, name='import_minsk'),
    re_path(r'^import/burials_minsk/$', views.import_burials_minsk, name='import_burials_minsk'),
]
