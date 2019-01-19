from django.conf.urls import url

from restthumbnails.defaults import URL_REGEX
from pd.views import OurThumbnailView

urlpatterns = [
    url(regex=URL_REGEX,
        view=OurThumbnailView.as_view(),
        name="get_thumbnail")
]
