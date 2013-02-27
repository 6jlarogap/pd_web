# coding=utf-8
import json

from django.http import HttpResponse

from geo.models import Country, Street, City, Region, DFiasAddrobj


def autocomplete_countries(request):
    query = request.GET['query']
    countries = Country.objects.filter(name__icontains=query)
    return HttpResponse(json.dumps([{'value': c.name} for c in countries[:20]]), mimetype='text/javascript')

def autocomplete_regions(request):
    query = request.GET['query']
    country = request.GET['country']
    regions = Region.objects.filter(name__icontains=query)
    if country:
        regions = regions.filter(country__name__iexact=country)
    return HttpResponse(json.dumps([{
        'value': r.name + '/' + r.country.name, 'real_value': r.name, 'country': r.country.name
    } for r in regions[:20]]), mimetype='text/javascript')

def autocomplete_cities(request):
    query = request.GET['query']
    country = request.GET['country']
    region = request.GET['region']
    cities = City.objects.filter(name__icontains=query)
    if country:
        cities = cities.filter(region__country__name__iexact=country)
    if region:
        cities = cities.filter(region__name__iexact=region)
    return HttpResponse(json.dumps([{
        'value': c.name + '/' + c.region.name + '/' + c.region.country.name,
        'real_value': c.name,
        'region': c.region.name,
        'country': c.region.country.name
    } for c in cities[:20]]), mimetype='text/javascript')

def autocomplete_streets(request):
    query = request.GET['query']
    country = request.GET['country']
    region = request.GET['region']
    city = request.GET['city']
    streets = Street.objects.filter(name__icontains=query)
    if country:
        streets = streets.filter(city__region__country__name__iexact=country)
    if region:
        streets = streets.filter(city__region__name__iexact=region)
    if city:
        streets = streets.filter(city__name__iexact=city)
    return HttpResponse(json.dumps([{
        'value': '%s/%s/%s/%s' % (s.name, s.city.name, s.city.region.name, s.city.region.country.name),
        'street': s.name,
        'city': s.city.name,
        'region': s.city.region.name,
        'country': s.city.region.country.name
    } for s in streets[:20]]), mimetype='text/javascript')

def autocomplete_fias(request):
    country = request.GET['country']
    region = request.GET['region']
    city = request.GET['city']
    street = request.GET['street']

    additional = (
        ('house', u'д.'),
        ('block', u'к.'),
        ('building', u'стр.'),
        ('flat', u'кв.'),
    )

    try:
        sf = DFiasAddrobj.objects.get_streets(country, region, city, street)[0]
        info_bits = unicode(sf).split(',', 1)
        info = ''
        for k,v in additional:
            if request.GET.get(k):
                info += ', %s %s' % (v, request.GET.get(k))
        info = info_bits[0] + info + ', ' + info_bits[1] + (country and (', %s' % country) or '')
        return HttpResponse(json.dumps({'ok': 1, 'id': sf.aoguid, 'info': info }), mimetype='application/json')
    except IndexError:
        return HttpResponse(json.dumps({}), mimetype='application/json')
