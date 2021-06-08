from django.urls import re_path
from reports import views

urlpatterns = [
    re_path(r'^reports/(?P<pk>\d+)/$', views.report_view, name='report_view'),
]
