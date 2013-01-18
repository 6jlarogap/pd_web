from django.http import HttpResponse
from django.utils import simplejson
from geo.models import Country, Street, City, Region

def autocomplete_countries(request):
    query = request.GET['query']
    countries = Country.objects.filter(name__istartswith=query)
    return HttpResponse(simplejson.dumps([{'value': c.name} for c in countries]), mimetype='text/javascript')

def autocomplete_regions(request):
    query = request.GET['query']
    country = request.GET['country']
    regions = Region.objects.filter(name__istartswith=query)
    if country:
        regions = regions.filter(country__name__iexact=country)
    return HttpResponse(simplejson.dumps([{'value': r.name + '/' + r.country.name, 'real_value': r.name, 'country': r.country.name} for r in regions]), mimetype='text/javascript')

def autocomplete_cities(request):
    query = request.GET['query']
    country = request.GET['country']
    region = request.GET['region']
    cities = City.objects.filter(name__istartswith=query)
    if country:
        cities = cities.filter(region__country__name__iexact=country)
    if region:
        cities = cities.filter(region__name__iexact=region)
    return HttpResponse(simplejson.dumps([{'value': c.name + '/' + c.region.name + '/' + c.region.country.name, 'real_value': c.name, 'region': c.region.name, 'country': c.region.country.name} for c in cities]), mimetype='text/javascript')

def autocomplete_streets(request):
    query = request.GET['query']
    country = request.GET['country']
    region = request.GET['region']
    city = request.GET['city']
    streets = Street.objects.filter(name__istartswith=query)
    if country:
        streets = streets.filter(city__region__country__name__iexact=country)
    if region:
        streets = streets.filter(city__region__name__iexact=region)
    if city:
        streets = streets.filter(city__name__iexact=city)
    return HttpResponse(simplejson.dumps([{
        'value': '%s/%s/%s/%s' % (s.name, s.city.name, s.city.region.name, s.city.region.country.name),
        'street': s.name,
        'city': s.city.name,
        'region': s.city.region.name,
        'country': s.city.region.country.name
    } for s in streets]), mimetype='text/javascript')
