# coding: utf-8

from django.conf import settings
from pd.views import get_front_end_url

def context_processor(request):
    return {
            'global_context_PRODUCTION_SITE': settings.PRODUCTION_SITE,
            'global_context_FRONT_END_URL': get_front_end_url(request),
            'global_context_DEADMAN_IDENT_NUMBER_ALLOW': settings.DEADMAN_IDENT_NUMBER_ALLOW,
            'global_context_CREATE_CABINET_ALLOW': settings.CREATE_CABINET_ALLOW,
            'global_context_REDIRECT_LOGIN_TO_FRONT_END': settings.REDIRECT_LOGIN_TO_FRONT_END,
           }
