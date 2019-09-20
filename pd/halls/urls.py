from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^halls/edit/$', views.halls_edit_view, name='halls_edit'),
]
