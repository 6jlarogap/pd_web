# coding: utf-8

import os
from django.conf import settings
from pd.views import get_front_end_url
from pd.utils import host_country_code

from users.models import Org

def context_processor(request):
    return {
            'global_context_PRODUCTION_SITE': settings.PRODUCTION_SITE,
            'global_context_FRONT_END_URL': get_front_end_url(request),
            'global_context_DEADMAN_IDENT_NUMBER_ALLOW': settings.DEADMAN_IDENT_NUMBER_ALLOW,
            'global_context_CREATE_CABINET_ALLOW': settings.CREATE_CABINET_ALLOW,
            'global_context_REDIRECT_LOGIN_TO_FRONT_END': settings.REDIRECT_LOGIN_TO_FRONT_END,
            'global_context_DEATH_CERTIFICATE_REQUIRED': settings.DEATH_CERTIFICATE_REQUIRED,
            'global_context_HOST_COUNTRY_CODE': host_country_code(request) or 'ru',
            'global_context_MOBILEKEEPER_URL': request.build_absolute_uri(
                os.path.join(
                    settings.MEDIA_URL,
                    settings.MOBILEKEEPER_MEDIA_PATH,
             )),
            'global_context_ARE_LORUS_IN_SYSTEM': Org.objects.filter(type=Org.PROFILE_LORU).exists(),
           }
