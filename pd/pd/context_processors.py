# coding: utf-8

from django.conf import settings

def context_processor(request):
   return {'global_context_PRODUCTION_SITE': settings.PRODUCTION_SITE }
