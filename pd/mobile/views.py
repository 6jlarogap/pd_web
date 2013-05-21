# coding=utf-8

from django.shortcuts import render_to_response
from django.views.generic.base import View
from django.utils.translation import ugettext as _

from burials.views import LoginRequiredMixin

class MobileHello(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render_to_response('simple_message.html', {'message': _(u"Привет")})

mobile_hello = MobileHello.as_view()