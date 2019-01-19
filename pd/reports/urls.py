# coding: utf-8

from django.conf.urls import url
from reports import views

urlpatterns = [
    url(r'^reports/(?P<pk>\d+)/$', views.report_view, name='report_view'),
]
