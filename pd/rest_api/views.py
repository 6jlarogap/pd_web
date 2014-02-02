# -*- coding: utf-8 -*-

from django.db.models.query_utils import Q

from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django.http import Http404

from django.shortcuts import render_to_response

from django.conf import settings
from serializers import CemeterySerializer

from burials.models import Cemetery, Place, Area, BurialFiles


def isObjectOwnerCheck(qs, field_name, pk):
    filter = {field_name:pk}
    return qs.filter(**filter).count()>0


@api_view(['GET'])
def api_root(request, format=None):
    """
    The entry endpoint of our API.
    """
    return Response({
        'catalog':{
            'category-list':  '/api/catalog/category/list',
            'product-list':   '/api/catalog/product/list',
        },
        'log':{
            'log-list':  '/api/log',
        },
        'geo':{
            'country-list':  reverse('country-list',  request=request),
            'region-list':   reverse('region-list',   request=request),
            'city-list':     reverse('city-list',     request=request),
            'street-list':   reverse('street-list',   request=request),
            #'location-list': reverse('location-list', request=request),
        },
        'persons':{
            'alive-person-list': '/api/alive-person',
            'dead-person-list': '/api/dead-person',
        },
        'burials':{
            'cemetery-list': '/api/cemetery', #reverse('cemetery-list', request=request),
            'area-list':     '/api/area', #reverse('area-list', request=request),
            'place-list':    '/api/place', #reverse('place-list', request=request),
            
            'grave-list':    '/api/grave', #reverse('grave-list', request=request),
            #'burial-list':    reverse('butial-list', request=request),
            'areaphoto-list':'/api/area-photo',
            'gravephoto-list':'/api/grave-photo', #reverse('gravephoto-list', request=request),
            'placephoto-list':'/api/place-photo', #reverse('gravephoto-list', request=request),
            'areapurpose-list': '/api/areapurpose', #reverse('areapurpose-list', request=request),
            # 'placesize-list': '/api/placesize',

        },
        'orders':{
            'product_category': '/api/product_category',
        },
    })
    #'cemetery-detail': reverse('cemetery-detail', request=request),



@csrf_protect
def base_page(request, id=None):
    c = {
        'STATIC_URL': settings.STATIC_URL,
        'csrf_token': get_token(request),
        'user':request.user
    }
    return render_to_response("base_angular.html", c)

