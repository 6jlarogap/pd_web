from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^halls/edit/$', views.halls_edit_view, name='halls_edit'),
    url(r'^halls/timetable/$', views.halls_timetable_view, name='halls_timetable'),
]
