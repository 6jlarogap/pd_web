# coding: utf-8

from django.conf import settings

def context_processor(request):
    result = {'global_context_PRODUCTION_SITE': settings.PRODUCTION_SITE }
    back_end_prefix = settings.BACK_END_PREFIX if settings.BACK_END_PREFIX.endswith('.') \
                                                else settings.BACK_END_PREFIX + '.'
    host = request.get_host()
    result['global_context_FRONT_END_URL'] = '/'
    if host.startswith(back_end_prefix):
        result['global_context_FRONT_END_URL'] = 'https://' if request.is_secure() else 'http://'
        # ВНИМАНИЕ: заканчиваем на '/'
        result['global_context_FRONT_END_URL'] += host[len(back_end_prefix):] + '/'
    return result
