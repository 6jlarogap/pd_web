# coding=utf-8

import json

from django.db import transaction, IntegrityError
from django.db.models.query_utils import Q
from django.http import Http404, HttpResponse
from django.views.generic.base import View
from django.utils.translation import ugettext as _

from persons.models import DeadPerson, AlivePerson, BasePerson, DocumentSource, Phone, \
                           CustomPlace, CustomPerson, MemoryGallery
from persons.serializers import AlivePersonSerializer, DeadPersonSerializer, PhoneSerializer, \
                                CustomPlaceSerializer, CustomPersonSerializer

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser

from pd.models import UnclearDate, SafeDeleteMixin
from burials.models import Place 
from logs.models import write_log
from users.models import PermitIfCabinet
from orders.models import ResultFile
from geo.models import Location

from pd.utils import utcisoformat
from pd.views import ServiceException


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

class ApiClientCustomplacesMixin(object):

    def get_object(self, pk):
        try:
            customplace = CustomPlace.objects.get(pk=pk)
        except CustomPlace.DoesNotExist:
            raise Http404
        return customplace

    def create_deadmen(self, deadmen, customplace):
        if deadmen is not None:
            for deadman in deadmen:
                try:
                    CustomPerson.objects.create(
                        customplace=customplace,
                        last_name=deadman.get('lastname') or '',
                        first_name=deadman.get('firstname') or '',
                        middle_name=deadman.get('middlename') or '',
                        is_dead=True,
                        birth_date=deadman.get('birthDate') and UnclearDate.from_str_safe(deadman['birthDate']) or None,
                        death_date=deadman.get('deathDate') and UnclearDate.from_str_safe(deadman['deathDate']) or None,
                    )
                except ValueError:
                    raise ServiceException("Invalid death or birth date")


class ApiClientCustomplacesView(ApiClientCustomplacesMixin, APIView):
    """
    Создать CustomPlace (post) with CustomBurials или вернуть массив CustomPlaces (get)

    CustomPlace:
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
    permission_classes = (PermitIfCabinet,)
    
    @transaction.commit_on_success
    def post(self, request):
        deadmen = request.DATA.get('deadmens')
        address = None
        location = request.DATA.get('location')
        addr_str = request.DATA.get('address')
        if addr_str or location:
            address = Location.objects.create(
                addr_str=addr_str or '',
                gps_x=location and location['longitude'] or None,
                gps_y=location and location['latitude'] or None,
            )
        customplace = CustomPlace.objects.create(user=request.user,address=address)
        try:
            self.create_deadmen(deadmen, customplace)
        except ServiceException as excpt:
            transaction.rollback()
            return Response({"status": "error", "message": excpt.message}, 400)
        return Response({"status": "success"}, 200)

    def get(self, request):
        data = []
        for p in CustomPlace.objects.filter(user=request.user, place__isnull=True).order_by('pk'):
            place=dict(
                id=p.pk,
                address=p.address and unicode(p.address) or None,
                location=p.address and dict(
                    longitude=p.address.gps_x,
                    latitude=p.address.gps_y,
                ) or None,
            )
            deadmen=[]
            for d in CustomPerson.objects.filter(customplace=p).order_by('pk'):
                deadman = dict(
                    id=d.pk,
                    lastname=d.last_name,
                    firstname=d.first_name,
                    middlename=d.middle_name,
                    birthDate=d.birth_date and d.birth_date.str_safe() or None,
                    deathDate=d.death_date and d.death_date.str_safe() or None,
                )
                deadmen.append(deadman)
            place['deadmens'] = deadmen
            data.append(place)
        return Response(data, 200)

api_client_customplaces = ApiClientCustomplacesView.as_view()

class ApiClientPlacesView(APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request):
        return Response(
            data=[CustomPlaceSerializer(customplace,context=dict(request=request)).data \
                  for customplace in CustomPlace.objects.filter(user=request.user).order_by('pk')],
            status=200,
        )

api_client_places = ApiClientPlacesView.as_view()

class ApiClientCustomplacesDetailView(ApiClientCustomplacesMixin, SafeDeleteMixin, APIView):
    """
    Edit or delete CustomPlace
    """
    permission_classes = (PermitIfCabinet,)

    @transaction.commit_on_success
    def put(self, request, pk):
        customplace = self.get_object(pk=pk)
        location = request.DATA.get('location')
        addr_str = request.DATA.get('address')
        if addr_str or location:
            address = Location.objects.get(pk=customplace.address.pk) if customplace.address else Location()
            fields=dict()
            if addr_str is not None:
                fields['addr_str'] = addr_str
            if location is not None:
                fields['gps_x'] = location['longitude']
                fields['gps_y'] = location['latitude']
            for f in fields:
                setattr(address, f, fields[f])
            address.save()
        deadmen = request.DATA.get('deadmens')
        if deadmen is not None:
            CustomPerson.objects.filter(customplace=customplace).delete()
            try:
                self.create_deadmen(deadmen, customplace)
            except ServiceException as excpt:
                transaction.rollback()
                return Response({"status": "error", "message": excpt.message}, 400)
        return Response({"status": "success"}, 200)

    @transaction.commit_on_success
    def delete(self, request, pk):
        customplace = self.get_object(pk=pk)
        self.safe_delete('address', customplace)
        CustomPerson.objects.filter(customplace=customplace).delete()
        try:
            customplace.delete()
        except IntegrityError:
            transaction.rollback()
            return Response({"status": "error", "message": _(u"На это место оформлен заказ, удалять нельзя")}, 400)
        return Response({"status": "success"}, 200)

api_client_customplaces_detail = ApiClientCustomplacesDetailView.as_view()

class ApiClientPlacesDetailView(ApiClientCustomplacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        return Response(
            data=CustomPlaceSerializer(self.get_object(pk),context=dict(request=request)).data,
            status=200,
        )

api_client_places_detail = ApiClientPlacesDetailView.as_view()

class ApiCustompersonMixin(object):

    def get_object(self, pk):
        try:
            customperson = CustomPerson.objects.get(pk=pk)
        except CustomPerson.DoesNotExist:
            raise Http404
        return customperson

class ApiMemoryGalleryMixin(object):

    def gallery_dict(self, m, request):
        return {
            'type': m.type,
            'text': m.text,
            'mediaContent': m.bfile and request.build_absolute_uri(m.bfile.url) or None,
            'eventDate': m.event_date and UnclearDate.str_safe(m.event_date) or None,
            'createdAt': utcisoformat(m.date_of_creation),
        }

class ApiCustompersonMemoryView(ApiCustompersonMixin, ApiMemoryGalleryMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        customperson = self.get_object(pk)
        data = {
            'photo': None,
            'lasttname' : customperson.last_name,
            'firstname' : customperson.first_name,
            'middlename' : customperson.middle_name,
            'dob' : customperson.birth_date and customperson.birth_date.str_safe() or None,
            'dod' : customperson.death_date and customperson.death_date.str_safe() or None,
            'commonText': customperson.memory_text,
        }
        gallery = []
        for m in MemoryGallery.objects.filter(customperson=customperson):
            item = self.gallery_dict(m, request)
            gallery.append(item)
        data['gallery'] = gallery
        return Response(data, 200)
        
    def patch(self, request, pk):
        customperson = self.get_object(pk)
        mapping = dict(
           lastname='last_name',
           firstname='first_name',
           middlename='middle_name',
           commonText='memory_text',
        )
        fields = dict()
        for f in mapping:
            got = request.DATA.get(f)
            if got is not None:
                fields[mapping[f]] = got
        if fields:
            for f in fields:
                setattr(customperson, f, fields[f])
            customperson.save()
        return Response({"status": "success"}, 200)

api_customperson_memory = ApiCustompersonMemoryView.as_view()

class ApiCustompersonMemoryGalleryView(ApiCustompersonMixin, ApiMemoryGalleryMixin, APIView):
    permission_classes = (PermitIfCabinet,)
    parser_classes = (MultiPartParser,)
    
    def get(self, request, pk):
        customperson = self.get_object(pk)

        offset = self.request.GET.get('offset') and int(self.request.GET.get('offset'))
        limit = self.request.GET.get('limit') and int(self.request.GET.get('limit'))
        filter = MemoryGallery.objects.filter(customperson=customperson)
        if offset and limit:
            filter = filter[offset:offset+limit]
        elif offset:
            filter = filter[offset:]
        elif limit:
            filter = filter[:limit]

        data = []
        for m in filter:
            item = self.gallery_dict(m, request)
            item['createdBy'] = {
                    'id': request.user.pk,
                    'lastname': m.creator.customerprofile.user_last_name,
                    'firstname': m.creator.customerprofile.user_first_name,
                    'middlename': m.creator.customerprofile.user_middle_name,
                 }
            data.append(item)
        return Response(data, 200)


    def post(self, request, pk):
        customperson = self.get_object(pk)
        fields = {
            'customperson': customperson,
            'type': request.DATA.get('type'),
            'text': request.DATA.get('text'),
            'event_date': request.DATA.get('eventDate') and UnclearDate.from_str_safe(request.DATA['eventDate']) or None,
            'creator': request.user,
        }
        file_ = request.FILES.get('mediaContent')
        if file_:
            fields['bfile'] = file_
        MemoryGallery.objects.create(**fields)
        return Response({"status": "success"}, 200)

api_customperson_memory_gallery = ApiCustompersonMemoryGalleryView.as_view()

class ApiClientPlacesDeadmansView(ApiClientCustomplacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        return Response(
            data=[CustomPersonSerializer(customperson).data \
                  for customperson in CustomPerson.objects.filter(customplace=self.get_object(pk))],
            status=200,
        )

api_client_places_deadmans = ApiClientPlacesDeadmansView.as_view()

class ApiClientPlacesDeadmansDetailView(ApiClientCustomplacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def put(self, request, pk, deadman_pk):
        customplace=self.get_object(pk)
        try:
            customperson=CustomPerson.objects.get(customplace=customplace,pk=deadman_pk)
        except CustomPerson.DoesNotExist:
            raise Http404
        serializer = CustomPersonSerializer(
            customperson,
            data=request.DATA,
            context=dict(request=request),
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

api_client_places_deadmans_detail = ApiClientPlacesDeadmansDetailView.as_view()

