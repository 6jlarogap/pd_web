from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^halls/edit/$', views.halls_edit_view, name='halls_edit'),
    url(r'^halls/timetable/$', views.halls_timetable_view, name='halls_timetable'),
    url(r'^halls/time/$', views.halls_time_view, name='halls_time'),
    url(r'^halls/(?P<pk>\d+)/time/edit/$', views.halls_time_edit_view, name='halls_time_edit'),
]
