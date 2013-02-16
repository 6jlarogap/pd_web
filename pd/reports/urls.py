# coding: utf-8

from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('reports.views',
    url(r'^reports/(?P<pk>\d+)/$', 'report_view', name='report_view'),
)
