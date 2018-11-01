# coding=utf-8

import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models.query_utils import Q

from burials.models import Cemetery
 
from geo.models import Country, Street, City, Region, Location
from geo.serializers import CountrySerializer, RegionSerializer, CitySerializer, StreetSerializer, \
    LocationSerializer, LocationStaticSerializer

# REST import
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# EOF REST import


def autocomplete_countries(request):
    query = request.GET['query']
    countries = Country.objects.filter(name__icontains=query)
    return HttpResponse(json.dumps([{'value': c.name} for c in countries[:20]]), mimetype='text/javascript')

def autocomplete_regions(request):
    query = request.GET['query']
    country = request.GET['country']
    q = Q(name__icontains=query)
    if country:
        q &= Q(country__name__iexact=country)
    regions = Region.objects.filter(q)[:20]
    return HttpResponse(json.dumps([{
        'value': r.name + '/' + r.country.name, 'real_value': r.name, 'country': r.country.name
    } for r in regions]), mimetype='text/javascript')

def autocomplete_cities(request):
    query = request.GET['query']
    country = request.GET['country']
    region = request.GET['region']
    q = Q(name__icontains=query)
    if country:
        q &= Q(region__country__name__iexact=country)
    if region:
        q &= Q(region__name__iexact=region)
    cities = City.objects.filter(q)[:20]
    return HttpResponse(json.dumps([{
        'value': c.name + '/' + c.region.name + '/' + c.region.country.name,
        'real_value': c.name,
        'region': c.region.name,
        'country': c.region.country.name
    } for c in cities]), mimetype='text/javascript')

def autocomplete_streets(request):
    query = request.GET['query']
    country = request.GET['country']
    region = request.GET['region']
    city = request.GET['city']
    q = Q(name__icontains=query)
    if country:
        q &= Q(city__region__country__name__iexact=country)
    if region:
        q &= Q(city__region__name__iexact=region)
    if city:
        q &= Q(city__name__iexact=city)
    streets = Street.objects.filter(q)[:20]
    return HttpResponse(json.dumps([{
        'value': '%s/%s/%s/%s' % (s.name, s.city.name, s.city.region.name, s.city.region.country.name),
        'street': s.name,
        'city': s.city.name,
        'region': s.city.region.name,
        'country': s.city.region.country.name
    } for s in streets]), mimetype='text/javascript')

# REST API

class CountryList(generics.ListCreateAPIView):
    serializer_class = CountrySerializer
    model = Country
    paginate_by = None
    def get_queryset(self):
        queryset = Country.objects
        name = self.request.GET.get('q', None)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        return queryset.all()[0:10]


class RegionList(generics.ListCreateAPIView):
    serializer_class = RegionSerializer
    model = Region
    paginate_by = None
    
    def get_queryset(self):
        queryset = Region.objects
        name = self.request.GET.get('q', None)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        
        #country_id = self.request.GET.get('country_id')
        #if country_id:
        #    country = get_object_or_404(Country, pk=country_id)
        #    queryset = queryset.filter(country=country)
        return queryset.all()[0:10]


class CityList(generics.ListCreateAPIView):
    serializer_class = CitySerializer
    model = City
    paginate_by = None

    def get_queryset(self):
        queryset = City.objects
        name = self.request.GET.get('q', None)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        
        #region_id = self.request.GET.get('region_id')
        #if region_id:
        #    region = get_object_or_404(City, pk=region_id)
        #    queryset = queryset.filter(region=region)
        return queryset.all()[0:10]


class StreetList(generics.ListCreateAPIView):
    serializer_class = StreetSerializer
    model = Street
    paginate_by = None

    def get_queryset(self):
        queryset = Street.objects
        name = self.request.GET.get('q', None)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        
        #city_id = self.request.GET.get('city_id')
        #if region_id:
        #    city = get_object_or_404(Street, pk=city_id)
        #    queryset = queryset.filter(city=city)
        return queryset.all()[0:10]


class LocationViewSet(viewsets.ModelViewSet):
    """
    TODO: add empty field validators
    """
    model = Location
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        TODO: moved into place get/update
        """
        return self.model.objects.all()
        address_ids = [i.address.pk for i in Cemetery.objects.filter(ugh=self.request.user.profile.org, address__isnull=False).all()]
        #.distinct('address')
        return self.model.objects.filter(pk__in=address_ids).all()


class LocationStaticViewSet(LocationViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = LocationStaticSerializer




country_list = CountryList.as_view()
region_list  = RegionList.as_view()
city_list    = CityList.as_view()
street_list  = StreetList.as_view()
#location_list= LocationList.as_view()

# EOF REST API
