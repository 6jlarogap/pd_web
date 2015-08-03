# coding: utf-8

from django.conf import settings
from pd.views import get_front_end_url
from pd.utils import host_country_code

def context_processor(request):
    return {
            'global_context_PRODUCTION_SITE': settings.PRODUCTION_SITE,
            'global_context_FRONT_END_URL': get_front_end_url(request),
            'global_context_HOST_COUNTRY_CODE': host_country_code(request) or 'ru',
           }
