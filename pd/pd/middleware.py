# coding=utf-8

from django.http import HttpResponseRedirect
from django.conf import settings
import re
from pd.views import get_front_end_url


exempt_urls = [re.compile(re.escape(url.lstrip('/')), flags=re.I) \
                for url in (
                    settings.LOGOUT_URL,
                    settings.LOGIN_URL,
                    'favicon.ico',
                )
]

for regex in (settings.REGISTER_URLS_REGEX,
              settings.SUPPORT_URLS_REGEX,
              settings.ANONYMOUS_URLS_REGEX,
              # Эти URLs требуют или не требуют (для анонимного пользователя)
              # регистрации, но это устанавливается в 
              # соответствующих класссах.as_view():
              settings.API_URLS_REGEX,
             ):
    exempt_urls.append(re.compile(regex, flags=re.I))

class LoginRequiredMiddleware:

    def process_request(self, request):
        if not request.user.is_authenticated():
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in exempt_urls):
                next = '' if not path or exempt_urls[0].match(path) else '?redirectUrl='+request.build_absolute_uri()
                return HttpResponseRedirect(settings.LOGIN_URL+next)
