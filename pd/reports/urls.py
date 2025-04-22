from django.urls import re_path
from reports import views

urlpatterns = [
    re_path(r'^reports/(?P<pk>[0-9]+)/$', views.report_view, name='report_view'),
]
