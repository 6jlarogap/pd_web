# coding=utf-8

import json
import iso8601

from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.views.generic.base import View
from django.utils.translation import ugettext as _

from persons.models import DeadPerson, AlivePerson, BasePerson, DocumentSource, Phone, \
                           CustomPlace, CustomPerson
from serializers import AlivePersonSerializer, DeadPersonSerializer, PhoneSerializer

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from burials.models import Place 
from logs.models import write_log
from users.models import PermitIfCabinet
from geo.models import Location


class AutocompleteFIO(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']

        fio = [f.strip('.') for f in query.split(' ')]
        q = Q()
        if len(fio) > 2:
            q &= Q(middle_name__istartswith=fio[2])
        if len(fio) > 1:
            q &= Q(first_name__istartswith=fio[1])
        if len(fio) > 0:
            q &= Q(last_name__istartswith=fio[0])

        persons = DeadPerson.objects.filter(q).distinct('last_name', 'first_name', 'middle_name')
        return HttpResponse(json.dumps([{'value': unicode(c)} for c in persons[:20]]), mimetype='text/javascript')

autocomplete_fio = AutocompleteFIO.as_view()

class AutocompleteFirstName(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']
        first_names = BasePerson.objects.filter(first_name__istartswith=query).order_by('first_name').distinct('first_name')
        return HttpResponse(json.dumps([{'value': c.first_name} for c in first_names[:20]]), mimetype='text/javascript')

autocomplete_first_name = AutocompleteFirstName.as_view()

class AutocompleteMiddleName(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']
        middle_names = BasePerson.objects.filter(middle_name__istartswith=query).order_by('middle_name').distinct('middle_name')
        return HttpResponse(json.dumps([{'value': c.middle_name} for c in middle_names[:20]]), mimetype='text/javascript')

autocomplete_middle_name = AutocompleteMiddleName.as_view()

class AutocompleteAlive(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']

        fio = [f.strip('.') for f in query.split(' ')]
        q = Q()
        if len(fio) > 2:
            q &= Q(middle_name__istartswith=fio[2])
        if len(fio) > 1:
            q &= Q(first_name__istartswith=fio[1])
        if len(fio) > 0:
            q &= Q(last_name__istartswith=fio[0])

        persons = AlivePerson.objects.filter(q).distinct('last_name', 'first_name', 'middle_name')
        return HttpResponse(json.dumps([{'value': unicode(c)} for c in persons[:20]]), mimetype='text/javascript')

autocomplete_alive = AutocompleteAlive.as_view()

class AutocompleteDocSources(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']
        dcs = DocumentSource.objects.filter(name__icontains=query)
        return HttpResponse(json.dumps([{'value': unicode(c)} for c in dcs[:20]]), mimetype='text/javascript')

autocomplete_docsources = AutocompleteDocSources.as_view()


class AlivePersonViewSet(viewsets.ModelViewSet):
    model = AlivePerson
    serializer_class = AlivePersonSerializer
    permission_classes = (IsAuthenticated,)

    #def get_queryset(self):
    #    # TODO: perfomance issue
    #    responcible_ids = [i.responsible.pk for i in Place.objects.filter(cemetery__ugh=self.request.user.profile.org, responsible__isnull=False).all()]
    #    #.distinct('responsible')
    #    return self.model.objects.filter(pk__in=responcible_ids).all()

    def pre_save(self, object):
        if object.pk:
            old_obj = self.model.objects.get(pk=object.pk)
            write_log(self.request, object, _(u'Ответственный изменен с "%s" на "%s"') % (old_obj,object))
        else:
            write_log(self.request, object, _(u'Ответственный создан'))


class DeadPersonViewSet(viewsets.ModelViewSet):
    model = DeadPerson
    serializer_class = DeadPersonSerializer
    permission_classes = (IsAuthenticated,)



class PhoneViewSet(viewsets.ModelViewSet):
    model = Phone
    serializer_class = PhoneSerializer
    permission_classes = (IsAuthenticated,)

    #def get_queryset(self):
    #    # TODO: perfomance issue
    #    responcible_ids = [i.responsible.pk for i in Place.objects.filter(cemetery__ugh=self.request.user.profile.org, responsible__isnull=False).all()]
    #    #.distinct('responsible')
    #    return self.model.objects.filter(pk__in=responcible_ids).all()

    def pre_save(self, object):
        if object.pk:
            old_obj = self.model.objects.get(pk=object.pk)
            write_log(self.request, object, _(u'Телефон изменен с "%s" на "%s"') % (old_obj,object))
        else:
            write_log(self.request, object, _(u'Телефон создан'))

class ApiPlacesView(APIView):
    permission_classes = (PermitIfCabinet,)

    def post(self, request):
        """
        Создать CustomPlace with CustomBurials

        Входные данные:
        {
            "address": "Строка адреса",
            "location": {
                "longitude": 54.12331,
                "latitude": 28.54334
            },
            "deadmens": [
                {
                    "lastname": "Петров",
                    "firstname": "Петр",
                    "middlename": "Петрович",
                    "birthDate": "1995-01-02T21:00:00.000Z",
                    "deathDate": "2014-05-10T21:00:00.000Z"
                },
                {
                    "lastname": "Иванов",
                    "firstname": "Иван",
                    "middlename": "Иванович",
                    "birthDate": "1995-07-02T21:00:00.000Z",
                    "deathDate": "2013-05-09T21:00:00.000Z"
                }
            ]
        }
        """
        deadmen = request.DATA.get('deadmens')
        if deadmen:
            address = None
            location = request.DATA.get('location')
            addr_str = request.DATA.get('address')
            if addr_str or location:
                address = Location.objects.create(
                    addr_str=addr_str or '',
                    gps_x=location and location['longitude'] or None,
                    gps_y=location and location['latitude'] or None,
                )
            place = CustomPlace.objects.create(user=request.user,address=address)
            for deadman in deadmen:
                CustomPerson.objects.create(
                    last_name=deadman.get('lastname') or '',
                    first_name=deadman.get('firstname') or '',
                    middle_name=deadman.get('middlename') or '',
                    is_dead=True,
                    birth_date=deadman.get('birthDate') and iso8601.parse_date(deadman['birthDate']) or None,
                    death_date=deadman.get('deathDate') and iso8601.parse_date(deadman['deathDate']) or None,
                )
        else:
            return Response({"status": "error", "message": "No deadmen in input data"}, 400)
        return Response({"status": "success"}, 200)

api_places = ApiPlacesView.as_view()
