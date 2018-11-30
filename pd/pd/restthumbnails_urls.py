from django.conf import settings
from django.conf.urls import patterns, url

from restthumbnails.defaults import URL_REGEX
from pd.views import OurThumbnailView


urlpatterns = patterns('',
    url(regex=URL_REGEX,
        view=OurThumbnailView.as_view(),
        name="get_thumbnail"))
