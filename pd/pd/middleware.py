# coding=utf-8

from django.http import HttpResponseRedirect
from django.conf import settings
import re
from pd.views import get_front_end_url


exempt_urls = [re.compile(re.escape(url.lstrip('/')), flags=re.I) \
                for url in (settings.LOGIN_URL,
                            'favicon.ico',
                           )
              ]

for regex in (settings.REGISTER_URLS_REGEX,
              settings.SUPPORT_URLS_REGEX,
              # Эти URLs требуют регистрации, но она через tokens,
              # ! За исключение /api/signin,
              #   которая регистрации не требует, а проверяет имя/пароль
              settings.API_URLS_REGEX,
             ):
    exempt_urls.append(re.compile(regex, flags=re.I))

class LoginRequiredMiddleware:

    def process_request(self, request):
        if not request.user.is_authenticated():
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in exempt_urls):
                next = '' if not path or exempt_urls[0].match(path) else '?next='+request.build_absolute_uri()
                return HttpResponseRedirect(get_front_end_url(request)+next)
