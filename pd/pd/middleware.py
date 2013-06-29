from django.http import HttpResponseRedirect
from django.conf import settings
import re

EXEMPT_URLS = [re.compile(re.escape(settings.LOGIN_URL.lstrip('/')), flags=re.I)]
login_exempt_urls = 'favicon.ico'
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    login_exempt_urls += ' ' + settings.LOGIN_EXEMPT_URLS
EXEMPT_URLS += [re.compile(re.escape(expr.lstrip('/')), flags=re.I) \
                    for expr in login_exempt_urls.split()]

class LoginRequiredMiddleware:

    def process_request(self, request):
        if not request.user.is_authenticated():
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in EXEMPT_URLS):
                next = '' if not path or EXEMPT_URLS[0].match(path) else '?next='+request.build_absolute_uri()
                return HttpResponseRedirect(settings.LOGIN_URL+next)
