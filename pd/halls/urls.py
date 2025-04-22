from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^halls/edit/$', views.halls_edit_view, name='halls_edit'),
    re_path(r'^halls/timetable/$', views.halls_timetable_view, name='halls_timetable'),
    re_path(r'^halls/time/$', views.halls_time_view, name='halls_time'),
    re_path(r'^halls/export/$', views.halls_export_view, name='halls_export'),
    re_path(r'^halls/(?P<pk>[0-9]+)/time/edit/$', views.halls_time_edit_view, name='halls_time_edit'),
]
