from django.http import HttpResponseRedirect
from django.conf import settings
import re


exempt_urls = [re.compile(re.escape(url.lstrip('/')), flags=re.I) \
                for url in (settings.LOGIN_URL,
                            settings.REGISTER_URL,
                            'favicon.ico',
                           )
              ]

class LoginRequiredMiddleware:

    def process_request(self, request):
        if not request.user.is_authenticated():
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in exempt_urls):
                next = '' if not path or exempt_urls[0].match(path) else '?next='+request.build_absolute_uri()
                return HttpResponseRedirect(settings.LOGIN_URL+next)
