# -*- coding: utf-8 -*-

from django.views.generic.base import TemplateView

class BasePageAngularView(TemplateView):
    template_name = 'base_angular.html'

base_page = BasePageAngularView.as_view()
