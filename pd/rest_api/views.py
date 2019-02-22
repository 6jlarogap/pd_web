# -*- coding: utf-8 -*-

from django.views.generic.base import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response

class BasePageAngularView(TemplateView):
    template_name = 'base_angular.html'

base_page = BasePageAngularView.as_view()

class ApiRootView(APIView):

    def get(self, request):
        return Response(data=dict(), status=200)

api_root = ApiRootView.as_view()
