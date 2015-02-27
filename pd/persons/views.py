# coding=utf-8

import json
import re

from django.db import transaction, IntegrityError
from django.db.models.query_utils import Q
from django.http import Http404, HttpResponse
from django.views.generic.base import View
from django.utils.translation import ugettext as _

from persons.models import DeadPerson, AlivePerson, BasePerson, DocumentSource, Phone, \
                           CustomPlace, CustomPerson, MemoryGallery
from persons.serializers import AlivePersonSerializer, DeadPersonSerializer, PhoneSerializer, \
                                CustomPlaceDetailSerializer, CustomPlaceListSerializer, \
                                CustomPlaceEditSerializer, \
                                CustomPersonSerializer, CustomPerson2Serializer, \
                                CustomPerson3Serializer, \
                                MemoryGallerySerializer, MemoryGallery2Serializer
from orders.serializers import OrderSerializer

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser

from pd.models import UnclearDate, SafeDeleteMixin
from burials.models import Place, PlacePhoto
from logs.models import write_log
from users.models import PermitIfCabinet, user_dict
from orders.models import Order, ResultFile
from geo.models import Location

from pd.utils import utcisoformat, get_image, is_video
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

class ApiClientPlacesMixin(object):

    def get_customplace(self, pk):
        try:
            customplace = CustomPlace.objects.get(pk=pk)
        except CustomPlace.DoesNotExist:
            raise Http404
        if customplace.user and customplace.user != self.request.user:
            raise Http404
        return customplace

    def check_life_dates(self, instance=None):
        birth_date = self.request.DATA.get('birthDate') or self.request.DATA.get('dob')
        death_date = self.request.DATA.get('deathDate') or self.request.DATA.get('dod')
        message = UnclearDate.check_safe_str(birth_date, check_today=True)
        if message:
            return _(u"Дата рождения: %s") % message
        message = UnclearDate.check_safe_str(death_date, check_today=True)
        if message:
            return _(u"Дата смерти: %s") % message
        msg_dates = _(u"Дата смерти раньше даты рождения")
        if birth_date and death_date and birth_date > death_date:
            return msg_dates
        if instance:
            if birth_date and not death_date and instance.death_date and birth_date > instance.death_date.str_safe():
                return msg_dates
            if not birth_date and death_date and instance.birth_date and instance.birth_date.str_safe() > death_date:
                return msg_dates
        return ""

class ApiClientPlacesView(APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request):
        return Response(
            data=[CustomPlaceListSerializer(customplace,context=dict(request=request)).data \
                  for customplace in CustomPlace.objects.filter(user=request.user).order_by('pk')],
            status=200,
        )

    def post(self, request):
        serializer = CustomPlaceEditSerializer(
            data=request.DATA,
            context=dict(request=request),
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

api_client_places = ApiClientPlacesView.as_view()

class ApiClientPlacesDetailView(ApiClientPlacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        return Response(
            data=CustomPlaceDetailSerializer(self.get_customplace(pk),context=dict(request=request)).data,
            status=200,
        )

    def put(self, request, pk):
        customplace = self.get_customplace(pk)
        serializer = CustomPlaceEditSerializer(
            customplace,
            data=request.DATA,
            context=dict(request=request),
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

api_client_places_detail = ApiClientPlacesDetailView.as_view()

class ApiCustompersonMixin(object):

    def get_customperson(self, pk):
        try:
            customperson = CustomPerson.objects.get(pk=pk)
            if customperson.customplace and \
               customperson.customplace.user != self.request.user:
                raise Http404
        except CustomPerson.DoesNotExist:
            raise Http404
        return customperson

class ApiCustompersonMemoryView(ApiCustompersonMixin, ApiClientPlacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)
    parser_classes = (MultiPartParser, JSONParser, )

    def get(self, request, pk):
        customperson = self.get_customperson(pk)
        return Response(
            data=CustomPerson3Serializer(customperson, context=dict(request=request)).data,
            status=200
        )
        
    def put(self, request, pk):
        try:
            customperson = self.get_customperson(pk)
            message = self.check_life_dates(instance=customperson)
            if message:
                raise ServiceException(message)
            photo = request.FILES.get('photo')
            if photo:
                if photo.size > CustomPerson.MAX_PHOTO_SIZE * 1024 * 1024:
                    raise ServiceException(_(u"Размер фото превышает %d Мб") % CustomPerson.MAX_PHOTO_SIZE)
                if not get_image(photo):
                    raise ServiceException(_(u"Загруженное фото не является изображением"))
            serializer = CustomPerson3Serializer(
                customperson,
                data=request.DATA,
                context=dict(request=request),
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)
        except ServiceException as excpt:
            return Response(data=dict(status='error', message=excpt.message), status=400)

api_customperson_memory = ApiCustompersonMemoryView.as_view()

class ApiCustompersonMemoryGalleryView(ApiCustompersonMixin, APIView):
    permission_classes = (PermitIfCabinet,)
    parser_classes = (MultiPartParser, JSONParser, )
    
    def get(self, request, pk):
        customperson = self.get_customperson(pk)

        offset = self.request.GET.get('offset') and int(self.request.GET.get('offset'))
        limit = self.request.GET.get('limit') and int(self.request.GET.get('limit'))
        filter = MemoryGallery.objects.filter(customperson=customperson)
        if offset and limit:
            filter = filter[offset:offset+limit]
        elif offset:
            filter = filter[offset:]
        elif limit:
            filter = filter[:limit]

        return Response(
            [ MemoryGallerySerializer(gallery_item, context=dict(request=request)).data \
              for gallery_item in filter ],
            status=200,
        )

    def post(self, request, pk):
        try:
            customperson = self.get_customperson(pk)
            fields = {
                'customperson': customperson,
                'type': request.DATA.get('type'),
                'text': request.DATA.get('text'),
                'event_date': UnclearDate.from_str_safe(request.DATA.get('eventDate')),
                'creator': request.user,
            }
            file_ = request.FILES.get('mediaContent')
            if file_:
                fields['bfile'] = file_
            if not fields['type']:
                raise ServiceException(_(u'Не задан тип (type)'))
            if fields['type'] not in [type_[0] for type_ in MemoryGallery.TYPE_CHOICES]:
                raise ServiceException(_(u'Неверный тип (type)'))
            if fields['type'] != MemoryGallery.TYPE_TEXT and not file_:
                raise ServiceException(_(u'Тип (type) %s требует загружаемого файла') % fields['type'])
            if fields['type'] == MemoryGallery.TYPE_TEXT and \
               (not fields['text'] or not fields['text'].strip()):
                raise ServiceException(_(u'Тип (type) %s требует непустой текст') % fields['type'])
            if fields['type'] == MemoryGallery.TYPE_IMAGE:
                if file_.size > MemoryGallery.MAX_IMAGE_SIZE * 1024 * 1024:
                    raise ServiceException(
                        _(u"Размер изображения не должен превышать %sМб") % MemoryGallery.MAX_IMAGE_SIZE
                    )
                if not get_image(file_):
                    raise ServiceException(_(u"Прикрепленный файл не является изображением"))
            elif fields['type'] == MemoryGallery.TYPE_VIDEO:
                if not is_video(file_):
                    raise ServiceException(_(u"Загруженный файл не является видео"))
            gallery_item = MemoryGallery.objects.create(**fields)
            return Response(
                data=MemoryGallery2Serializer(gallery_item, context=dict(request=request)).data,
                status=200,
            )
        except ServiceException as excpt:
            return Response(data=dict(status='error', message=excpt.message), status=400)

api_customperson_memory_gallery = ApiCustompersonMemoryGalleryView.as_view()

class ApiClientPlacesDeadmansView(ApiClientPlacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        return Response(
            data=[CustomPersonSerializer(customperson).data \
                  for customperson in CustomPerson.objects.filter(customplace=self.get_customplace(pk))],
            status=200,
        )

    def post(self, request, pk):
        customplace=self.get_customplace(pk)
        message = self.check_life_dates()
        if message:
            return Response({"status": "error", "message": message}, 400)
        serializer = CustomPersonSerializer(
            data=request.DATA,
            context=dict(
                request=request,
                customplace=customplace,
            ),
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

api_client_places_deadmans = ApiClientPlacesDeadmansView.as_view()

class ApiClientPlacesDeadmansDetailView(ApiClientPlacesMixin, ApiCustompersonMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def put(self, request, pk, deadman_pk):
        customplace = self.get_customplace(pk)
        customperson = self.get_customperson(deadman_pk)
        if customperson.customplace and customperson.customplace != customplace:
            raise Http404
        message = self.check_life_dates()
        if message:
            return Response({"status": "error", "message": message}, 400)
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

class ApiClientDeadmansView(APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request):
        data = list()
        for pk in re.split(r'[,\s]+', request.GET.get('ids', '').strip()):
            try:
                customperson=CustomPerson.objects.get(pk=pk,customplace__user=request.user)
            except (ValueError, CustomPerson.DoesNotExist, ):
                raise Http404
            data.append(CustomPerson2Serializer(customperson).data)
        return Response(
            data=data,
            status=200,
        )

api_client_deadmans = ApiClientDeadmansView.as_view()

class ApiClientPlacesAttachmentsView(ApiClientPlacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        customplace = self.get_customplace(pk)
        gallery = [dict(
                    id=resultfile.pk,
                    title=None,
                    type=resultfile.type,
                    url=request.build_absolute_uri(resultfile.bfile.url),
                    createdAt=utcisoformat(resultfile.date_of_creation),
                    createdBy=user_dict(resultfile.creator),
                ) \
                for resultfile in ResultFile.objects.filter(
                    order__customplace=customplace,
                    ).order_by('-date_of_creation') \
                if resultfile.bfile
        ]
        if customplace.place:
            gallery += [dict(
                        id=placephoto.pk,
                        title=None,
                        type=ResultFile.TYPE_IMAGE,
                        url=request.build_absolute_uri(placephoto.bfile.url),
                        createdAt=utcisoformat(placephoto.date_of_creation),
                        createdBy=user_dict(placephoto.creator),
                    ) \
                    for placephoto in PlacePhoto.objects.filter(
                        place=customplace.place,
                        ).order_by('-date_of_creation') \
                    if placephoto.bfile
            ]
        return Response(
            data=gallery,
            status=200,
        )

api_client_places_attachments = ApiClientPlacesAttachmentsView.as_view()

class ApiClientPlacesOrdersView(ApiClientPlacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        customplace=self.get_customplace(pk)
        return Response(data=[OrderSerializer(o).data \
                              for o in Order.objects.filter(customplace=customplace) \
                        ], status=200)

api_client_places_orders = ApiClientPlacesOrdersView.as_view()
