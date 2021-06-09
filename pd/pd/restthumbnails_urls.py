from django.urls import re_path

from restthumbnails.defaults import URL_REGEX
from pd.views import OurThumbnailView

urlpatterns = [
    re_path(URL_REGEX,
        OurThumbnailView.as_view(),
        name="get_thumbnail")
]
