# coding=utf-8

import re
from urllib import quote_plus, unquote_plus

from django.http import HttpResponseRedirect, Http404
from django.conf import settings

from pd.views import is_url_accessible_anonymous

exempt_urls = [re.compile(re.escape(url.lstrip('/')), flags=re.I) \
                for url in (
                    settings.LOGOUT_URL,
                    settings.LOGIN_URL,
                    'favicon.ico',
                    'sitemap.xml',
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

class LoginRequiredMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):

        # Code to be executed for each request before
        # the view (and later middleware) are called.
        path = request.path_info.lstrip('/')
        if any(m.match(path) for m in exempt_urls) or is_url_accessible_anonymous(request):
            pass
        elif not request.user.is_authenticated:
            if path:
                next_ = u"?redirectUrl=%s" % quote_plus(unquote_plus(request.build_absolute_uri()))
            else:
                next_ = ''
            return HttpResponseRedirect(settings.LOGIN_URL + next_)

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response
