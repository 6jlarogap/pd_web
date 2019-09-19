from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^halls/$', views.halls_view, name='halls'),
]
