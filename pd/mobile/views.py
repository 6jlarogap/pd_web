# coding=utf-8

from django.conf import settings

from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.base import View
from django.utils.translation import ugettext as _

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse

from django.utils import simplejson
from geo.models import Location, CoordinatesModel
from burials.models import Cemetery, CemeteryCoordinates, CemeteryPhoto
from burials.models import Area
from burials.models import AreaCoordinates
from burials.models import Place
from burials.models import PlaceStatus
from burials.models import Grave
from burials.models import PlacePhoto
from burials.models import Burial
from persons.models import DeadPerson
from persons.models import BasePerson
from users.models import PermitIfUgh
from logs.models import write_log, Log, LogOperation
from pd.models import UnclearDate
from pd.utils import utc2local, get_image

from django.utils.dateparse import parse_datetime
from django.core.files.base import ContentFile
from django.http import Http404
from django.db import IntegrityError, transaction
from django.db.models import Q
from datetime import datetime
from decimal import Decimal

import os
from axmlparserpy import apk

from StringIO import StringIO
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException

from serializers import BaseSerializer, CoordinatesSerializer, CemeteryWithNestedObjectSerializer, \
    AreaSerializer, AreaWithNestedObjectSerializer, RegionSerializer, CitySerializer, StreetSerializer, CountrySerializer, LocationSerializer, \
    BasePersonSerializer, AlivePersonSerializer, PlaceWithNestedObjectSerializer, GraveSerializer, BurialSerializer, \
    PlacePhotoSerializer, CemeteryPhotoSerializer

from serializers import PlaceSerializer
from rest_api.fields import DateTimeUtcField

templateDateTime = '%Y-%m-%dT%H:%M:%S.%f'
    
class CustomException(APIException):
    status_code = 500
    default_detail = 'Custom Exception'
    def __init__(self, detail = None, status=status_code):
        self.status_code = status
        if detail :
            self.detail = detail    
        else :
            self.detail = self.default_detail
        
class ApiCemeteryList(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request) :
        queryCemetery = Q(
            ugh=request.user.profile.org,
            pk__in=[c.pk for c in Cemetery.editable_ugh_cemeteries(request.user)],
        )
        listCemetery = Cemetery.objects.filter(queryCemetery).distinct().order_by('id')
        serializer = CemeteryWithNestedObjectSerializer(listCemetery)
        return Response(serializer.data)
        
cemetery_list = ApiCemeteryList.as_view()

class ApiCemeteryUpload(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request) :
        return render_to_response('mobile_upload_cemetery.html', {'message': _(u"Загрузите название кладбища:")})

    @transaction.commit_on_success
    def post(self, request) :
        org = request.user.profile.org
        listInsertedCemetery = []
        listGPS = [] 
        cemeteryId = int(request.POST['cemeteryId'])
        cemeteryName = request.POST['cemeteryName']
        gpsJSON = request.POST.get('gps')
        square = None
        dtCreated = None
        if request.POST.get('square') :
            square = request.POST['square']
        if request.POST.get('dt_created') :
            dtCreated = datetime.strptime(request.POST['dt_created'], templateDateTime)
            dtCreated = utc2local(dtCreated)
        isGPSChange = False
        if gpsJSON :
            isGPSChange = True
            stream = StringIO(gpsJSON)
            data = JSONParser().parse(stream)
            serializer = CoordinatesSerializer(data=data)
            isValid = serializer.is_valid()            
            for obj in serializer.object:
                listGPS.append(obj)
        cem = None
        try:
            prevCem = Cemetery.objects.get(pk = cemeteryId)
            if prevCem.name != cemeteryName or prevCem.square != square :
                prevCem.name = cemeteryName
                prevCem.square = square
                prevCem.save()
            cem = prevCem
        except Cemetery.DoesNotExist:
            prevCem = None
            cem = Cemetery(name = cemeteryName, square = square, creator = request.user, ugh = org, dt_created = dtCreated)
            cem.save()
            write_log(request, cem, _(u"Кладбище '%s' создано через мобильное приложение") % cem.name)
            if request.user.profile.is_registrator():
                request.user.profile.cemeteries.add(cem)
                log_mes = _(u"Добавлен доступ к кладбищу: '%s'") % cem.name
                user_mes=_(u'Изменены данные пользователя %(fio)s (%(username)s)') % dict(
                    fio=request.user.profile,
                    username=request.user.username,
                )
                write_log(request, request.user.profile.org, u"%s\n%s" % (
                    user_mes,
                    log_mes,
                ))
                write_log(request, request.user.profile, log_mes)
            listInsertedCemetery.append(cem)
        if isGPSChange == True :
            CemeteryCoordinates.objects.filter(cemetery__pk = cem.pk).delete()
            for gps in listGPS:
                cemeteryCoordinates = CemeteryCoordinates(gps)
                cemeteryCoordinates.pk = None
                cemeteryCoordinates.cemetery = cem
                cemeteryCoordinates.lat = gps.lat
                cemeteryCoordinates.lng = gps.lng
                cemeteryCoordinates.angle_number = gps.angle_number
                cemeteryCoordinates.save()                 
        serializer = CemeteryWithNestedObjectSerializer(listInsertedCemetery)        
        return Response(serializer.data)
        
cemetery_upload = ApiCemeteryUpload.as_view()
        
class ApiMobileCemeteryPhoto(APIView):
    permission_classes = (PermitIfUgh,)
    parser_classes = (MultiPartParser, JSONParser, )

    def get_cemetery(self, pk):
        return get_object_or_404(Cemetery, pk=pk, ugh=self.request.user.profile.org)

    def response(self, cemetery):
        return Response(
            status=200,
            data=[ CemeteryPhotoSerializer(photo).data \
                   for photo in CemeteryPhoto.objects.filter(cemetery=cemetery)
        ])

    def remove_photos(self, cemetery):
        count = 0
        for old_photo in CemeteryPhoto.objects.filter(cemetery=cemetery):
            count += 1
            old_photo.delete()
        return count

    def get(self, request, pk):
        cemetery = self.get_cemetery(pk)
        return self.response(cemetery)

    def post(self, request, pk):
        cemetery = self.get_cemetery(pk)
        photo = request.FILES.get('photo')
        if photo:
            if photo.size > CemeteryPhoto.MAX_PHOTO_SIZE * 1024 * 1024:
                raise CustomException(
                    detail=_(u"Размер фото превышает %d Мб") % CemeteryPhoto.MAX_PHOTO_SIZE,
                    status=400,
               )
            if not get_image(photo):
                raise CustomException(
                    detail=_(u"Загруженное фото не является изображением"),
                    status=400,
                )
        else:
            raise CustomException(
                detail=_(u"Нет загружаемого фото (photo)"),
                status=400,
                )
        try:
            lat = float(request.POST.get('lat', ''))
            lng = float(request.POST.get('lng', ''))
        except ValueError:
            lat = lng = None
        self.remove_photos(cemetery)
        photo = CemeteryPhoto.objects.create(
            cemetery=cemetery,
            photo=photo,
            creator=request.user,
            lat=lat,
            lng=lng,
        )
        if lat is not None and lng is not None:
            if not cemetery.address:
                cemetery.address = Location.objects.create(gps_x=lng, gps_y=lat)
                cemetery.save()
            else:
                Location.objects.filter(
                    pk=cemetery.address.pk).update(gps_x=lng, gps_y=lat)
        write_log(
            request,
            cemetery,
            _(u"Фото кладбища: %s") % request.build_absolute_uri(photo.photo.url),
        )
        return self.response(cemetery)

    def delete(self, request, pk):
        cemetery = self.get_cemetery(pk)
        count = self.remove_photos(cemetery)
        if count:
            write_log(
                request,
                cemetery,
                _(u"Фото кладбища удалено"),
            )
        return self.response(cemetery)

cemetery_photo = ApiMobileCemeteryPhoto.as_view()

class ApiAreaList(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) : 
        argSyncDateUnix = request.GET.get('syncDate', None) 
        argCemeteryId = request.GET.get('cemeteryId', None)
        argAreaId = request.GET.get('areaId', None)        
        queryArea = Q(cemetery__ugh = request.user.profile.org)
        if argCemeteryId :
            queryArea &= Q(cemetery__pk = argCemeteryId)            
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryArea &= Q(dt_modified__gte = argSyncDate)            
        if argAreaId :
            queryArea &= Q(pk = argAreaId)            
        listArea = Area.objects.filter(queryArea).order_by('cemetery', 'id')
        serializer = AreaWithNestedObjectSerializer(listArea)
        return Response(serializer.data)
        
area_list = ApiAreaList.as_view()

class ApiAreaUpload(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request) : 
        return render_to_response('mobile_upload_area.html', {'message': _(u"Загрузите название участка:")})

    @transaction.commit_on_success
    def post(self, request) : 
        listInsertedArea = []
        listGPS = []
        areaName = request.POST['areaName']
        # isOverwrite:
        # если такой участок внутри кладбища существует, то
        # ищем его среди существующих, а если нет такого, то создаём.
        # Т.е. при опции от клиента: грузить в существующий участок,
        # если такой существует
        isOverwrite = int(request.POST.get('isOverwrite', '0'))
        areaId = int(request.POST['areaId'])
        cemeteryId = int(request.POST['cemeteryId'])
        gpsJSON = request.POST['gps']
        square = request.POST.get('square') or None
        dtCreated = None
        if request.POST.get('dt_created') :
            dtCreated = datetime.strptime(request.POST['dt_created'], templateDateTime)
            dtCreated = utc2local(dtCreated)
        isGPSChange = False
        if gpsJSON :
            isGPSChange = True
            stream = StringIO(gpsJSON)
            data = JSONParser().parse(stream)
            serializer = CoordinatesSerializer(data=data)
            isValid = serializer.is_valid()            
            for obj in serializer.object:
                listGPS.append(obj)
        area = None
        try:
            cemetery = Cemetery.objects.get(pk = cemeteryId)
            prevArea = Area.objects.get(pk = areaId)
            if prevArea.name != areaName or prevArea.cemetery != cemetery or prevArea.square != square :
                prevArea.name = areaName
                prevArea.cemetery = cemetery
                prevArea.square = square
                prevArea.save()
            area = prevArea
        except Cemetery.DoesNotExist:
            raise Http404
        except Area.DoesNotExist:
            prevArea = None
            msg_created = _(u"Участок '%s' создан через мобильное приложение") % areaName
            if isOverwrite:
                area, created_ = Area.objects.get_or_create(
                    cemetery=cemetery,
                    name=areaName,
                    defaults=dict(
                        square=square,
                        dt_created=dtCreated
                ))
                if created_:
                    write_log(request, area, msg_created)
                else:
                    if square:
                        area.square = square
                        area.save()
            else:
                try:
                    area = Area.objects.create(
                        cemetery=cemetery,
                        name=areaName,
                        square=square,
                        dt_created=dtCreated,
                    )
                    write_log(request, area, msg_created)
                except IntegrityError:
                    transaction.rollback()
                    return Response(
                        status=400,
                        data=dict(status='error', message=_(u"Такой участок уже существует")),
                    )
            listInsertedArea.append(area)
        if isGPSChange == True :
            AreaCoordinates.objects.filter(area__pk = area.pk).delete()
            for gps in listGPS:
                areaCoordinates = AreaCoordinates(gps)
                areaCoordinates.pk = None
                areaCoordinates.area = area
                areaCoordinates.lat = gps.lat
                areaCoordinates.lng = gps.lng
                areaCoordinates.angle_number = gps.angle_number
                areaCoordinates.save()                 
        serializer = AreaWithNestedObjectSerializer(listInsertedArea)
        return Response(serializer.data)

area_upload = ApiAreaUpload.as_view()

class ApiPlaceList(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) : 
        argSyncDateUnix = request.GET.get('syncDate', None) 
        argAreaId = request.GET.get('areaId', None)
        argCemeteryId = request.GET.get('cemeteryId', None)        
        queryPlace = Q(cemetery__ugh = request.user.profile.org)
        if argCemeteryId :
            queryPlace &= Q(cemetery__pk = argCemeteryId)
        if argAreaId :
            queryPlace &= Q(area__pk = argAreaId)
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryPlace &= Q(dt_modified__gte = argSyncDate)        
        listPlace = Place.objects.filter(queryPlace).order_by('cemetery', 'area', 'id')
        serializer = PlaceWithNestedObjectSerializer(listPlace)
        return Response(serializer.data)

place_list = ApiPlaceList.as_view()

class PlaceUploadMixin(object):

    def get_place_parms(self, request, do_put=False):
        parms = dict(
            placeWidth='place_width',
            placeLength='place_length',
            dtWrongFio='dt_wrong_fio',
            dtFree='dt_free',
            dtMilitary='dt_military',
            dtSizeViolated='dt_size_violated',
            dtUnowned='dt_unowned',
            dtUnindentified='dt_unindentified',
        )
        if do_put:
            # При правке места могут исправляться:
            parms.update(dict(
                placeName='place',
                rowName='row',
            ))
        else:
            # При отправке нового места (и только!) приходит dtCreated
            parms.update(dict(
                dtCreated='dt_created',
            ))
        result = dict()
        for k in parms:
            if k in request.DATA:
                result[parms[k]] = request.DATA[k]
        ps = PlaceSerializer(Place(**result))
        for f in result:
            if isinstance(ps.fields[f], DateTimeUtcField):
                result[f] = ps.fields[f].from_native(ps.data[f])
        return result

    def response_already_exists(self):
        return Response(
            status=400,
            data=dict(
                message=_(u"Такое место уже существует"),
                code='place_already_exists'
        ))

class ApiMobileAreaPlaces(PlaceUploadMixin, APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request, area_id):
        area = get_object_or_404(
            Area,
            pk=area_id,
            cemetery__ugh = request.user.profile.org,
        )
        q = Q(area=area)
        argSyncDateUnix = request.GET.get('syncDate')
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            q &= Q(dt_modified__gte = argSyncDate)
        listPlace = Place.objects.filter(q).order_by('cemetery', 'area', 'id')
        serializer = PlaceSerializer(listPlace)
        return Response(data=serializer.data, status=200)

    @transaction.commit_on_success
    def post(self, request, area_id):
        area = get_object_or_404(
            Area,
            pk=area_id,
            cemetery__ugh = request.user.profile.org,
        )
        cemetery = area.cemetery
        placeName = request.DATA.get('placeName')
        if not placeName and cemetery.places_algo in (
            Cemetery.PLACE_BURIAL_ACCOUNT_NUMBER,
            Cemetery.PLACE_MANUAL
           ):
            return Response(
                status=400,
                data = dict(
                    message=_(u'Не задан номер места. Автоматическая расстановка новых мест на этом кладбище не предусмотрена'),
                    code='no_placeName_no_placeAlgo',
            ))
        place_key_parms = dict(
            cemetery=cemetery,
            area=area,
            row=request.DATA.get('rowName') or '',
            place=placeName, 
        )
        place_defaults = self.get_place_parms(request)
        place_defaults['is_invent'] = True
        place, created_ = Place.objects.get_or_create(
            defaults=place_defaults,
            **place_key_parms
        )
        if created_:
            print "Place created by MobileKeeper, id = %s" % place.pk
            logrec = write_log(request, place, operation=LogOperation.PLACE_CREATED_MOBILE)
            if 'dt_created' in place_defaults:
                Log.objects.filter(pk=logrec.pk).update(dt=place.dt_created)
                print " - got dt_created, %s" % place.dt_created
            else:
                print " - !!! no dt_created in input data"
        elif int(request.GET.get('isOverwrite', '0')) and request.DATA.get('placeName'):
            del place_defaults['is_invent']
            if 'dt_created' in place_defaults:
                del place_defaults['dt_created']
            do_save = False
            for f in place_defaults:
                if place_defaults[f] != getattr(place, f):
                    setattr(place, f, place_defaults[f])
                    do_save = True
            if do_save:
                place.save()
                write_log(
                    request,
                    place,
                    _(u"Место изменено через мобильное приложение при выгрузке места"),
                )
        else:
            return self.response_already_exists()
        return Response(data=PlaceSerializer(place).data)

api_mobile_area_places = ApiMobileAreaPlaces.as_view()

class ApiMobilePlace(PlaceUploadMixin, APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request, place_id):
        place = get_object_or_404(
            Place,
            pk=place_id,
            cemetery__ugh=request.user.profile.org)
        return Response(status=200, data=PlaceSerializer(place).data)

    @transaction.commit_on_success
    def put(self, request, place_id):
        place = get_object_or_404(
            Place,
            pk=place_id,
            cemetery__ugh=request.user.profile.org)
        place_fields = self.get_place_parms(request, do_put=True)
        do_save = False
        for f in place_fields:
            if place_fields[f] != getattr(place, f):
                setattr(place, f, place_fields[f])
                do_save = True
        if do_save:
            try:
                place.save()
                write_log(
                    request,
                    place,
                    _(u"Место изменено через мобильное приложение"),
                )
            except IntegrityError:
                transaction.rollback()
                return self.response_already_exists()

        return Response(status=200, data=PlaceSerializer(place).data)

api_mobile_place = ApiMobilePlace.as_view()

class ApiGraveList(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) : 
        argSyncDateUnix = request.GET.get('syncDate', None) 
        argPlaceId = request.GET.get('placeId', None)
        argCemeteryId = request.GET.get('cemeteryId', None)
        argAreaId = request.GET.get('areaId', None)        
        queryGrave = Q(place__cemetery__ugh = request.user.profile.org)
        if argCemeteryId :
            queryGrave &= Q(place__cemetery__pk = argCemeteryId)
        if argAreaId :
            queryGrave &= Q(place__area__pk = argAreaId)
        if argPlaceId :
            queryGrave &= Q(place__pk = argPlaceId)
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryGrave &= Q(dt_modified__gte = argSyncDate)        
        listGrave = Grave.objects.filter(queryGrave).order_by('id')
        serializer = GraveSerializer(listGrave)
        return Response(serializer.data)
    
grave_list = ApiGraveList.as_view()

class ApiGraveUpload(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request) :
        return render_to_response('mobile_upload_grave.html', {'message': _(u"Загрузите название могилы:")})

    @transaction.commit_on_success
    def post(self, request) :
        grave_number = request.POST['grave_number']
        graveId = int(request.POST['graveId'])
        placeId = int(request.POST['placeId'])
        isWrongFIO = False
        isMilitary = False
        dtFree = None
        dtCreated = None
        if int(request.POST.get('isWrongFIO', 0)) == 1 :
            isWrongFIO = True
        if int(request.POST.get('isMilitary', 0)) == 1 :
            isMilitary = True
        if request.POST.get('dtFree') :
            dtFree = datetime.strptime(request.POST['dtFree'], templateDateTime)
            dtFree = utc2local(dtFree)
        if request.POST.get('dt_created') :
            dtCreated = datetime.strptime(request.POST['dt_created'], templateDateTime)
            dtCreated = utc2local(dtCreated)
        listInsertedGrave = []
        try:
            place = Place.objects.get(pk = placeId)
            prevGrave = Grave.objects.get(pk = graveId)
            if prevGrave.grave_number != grave_number or \
               prevGrave.place != place or \
               prevGrave.is_wrong_fio != isWrongFIO or \
               prevGrave.is_military != isMilitary or \
               (prevPlace.dt_free is None) != (dtFree is None):
                log_operation = None
                if prevGrave.dt_free and not dtFree:
                    log_operation = LogOperation.GRAVE_FREE_RESET
                elif not prevGrave.dt_free and dtFree:
                    log_operation = LogOperation.GRAVE_FREE_SET
                prevGrave.grave_number = grave_number
                prevGrave.place = place
                prevGrave.is_military = isMilitary
                prevGrave.is_wrong_fio = isWrongFIO
                prevGrave.dt_free = dtFree
                prevGrave.save()
                if log_operation:
                    write_log(request, prevGrave, operation=log_operation)
        except Place.DoesNotExist:
            raise Http404            
        except Grave.DoesNotExist:
            prevGrave = None            
            grave = Grave(
                place = place,
                grave_number = place.get_graves_count() + 1,
                is_military = isMilitary,
                is_wrong_fio = isWrongFIO,
                dt_created = dtCreated,
                dt_free = dtFree,
            )
            grave.save()
            write_log(request, place, _(u"Могила '%s' создана через мобильное приложение") % grave.grave_number )
            listInsertedGrave.append(grave)            
        serializer = GraveSerializer(listInsertedGrave)
        return Response(serializer.data)
    
grave_upload = ApiGraveUpload.as_view()

class ApiBurialList(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) :
        argSyncDateUnix = request.GET.get('syncDate', None) 
        argGraveId = request.GET.get('graveId', None)
        argCemeteryId = request.GET.get('cemeteryId', None)
        argAreaId = request.GET.get('areaId', None)
        argStatus = request.GET.get('status', None)        
        queryBurial = Q(cemetery__ugh = request.user.profile.org)
        if argCemeteryId :
            queryBurial &= Q(cemetery__pk = argCemeteryId)
        if argAreaId :
            queryBurial &= Q(area__pk = argAreaId)
        if argGraveId :
            queryBurial &= Q(grave__pk = argGraveId)
        if argStatus :
            queryBurial &= Q(status = argStatus)
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryBurial &= Q(dt_modified__gte = argSyncDate)        
        listBurial = Burial.objects.filter(queryBurial).order_by('id')
        serializer = BurialSerializer(listBurial)
        return Response(serializer.data)

burial_list = ApiBurialList.as_view()

class ApiBindBurialGrave(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) :
        return render_to_response('mobile_bind_burial_grave.html', {'message': _(u"Загрузите захоронение:")})
    def post(self, request) :
        graveId = int(request.POST['graveId'])
        burialId = int(request.POST['burialId'])
        if request.POST.get('factDate') :
            factDate = datetime.strptime(request.POST['factDate'], templateDateTime)
            factUnclearDate = UnclearDate(year = factDate.year, month = factDate.month, day = factDate.day)       
        try:
            grave = Grave.objects.get(pk = graveId)
            burial = Burial.objects.get(pk = burialId)
            if burial.status != Burial.STATUS_APPROVED :
                raise CustomException(detail = _(u"Привязать данное захоронение невозможно к могиле."))
            burial.place_number = grave.place.place
            burial.grave_number = grave.grave_number
            burial.row = grave.place.row
            burial.area = grave.place.area
            burial.cemetery = grave.place.cemetery
            burial.ugh = grave.place.cemetery.ugh
            burial.changed_by = request.user
            burial.fact_date = factUnclearDate
            burial.save()
            burial.close(request=request)
            write_log(
                request,
                burial,
                operation=LogOperation.BURIAL_TO_GRAVE_MOBILE,
                msg=_(u"Могила: %(grave_name)s\nФакт. дата: %(fact_date)s") % dict(
                    grave_name=grave.full_name(),
                    fact_date=burial.fact_date,
            ))
        except Grave.DoesNotExist:
            raise Http404            
        except Burial.DoesNotExist:
            raise Http404
        return Response()
    
bind_burial_grave = ApiBindBurialGrave.as_view()

class ApiPlacePhotoList(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) :
        argSyncDateUnix = request.GET.get('syncDate', None)
        argPlaceId = request.GET.get('placeId', None)
        argCemeteryId = request.GET.get('cemeteryId', None)
        argAreaId = request.GET.get('areaId', None)        
        queryPlacePhoto = Q(place__cemetery__ugh = request.user.profile.org)
        if argCemeteryId :
            queryPlacePhoto &= Q(place__cemetery__pk = argCemeteryId)
        if argAreaId :
            queryPlacePhoto &= Q(place__area__pk = argAreaId)
        if argPlaceId :
            queryPlacePhoto &= Q(place__pk = argPlaceId)
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryPlacePhoto &= Q(dt_modified__gte = argSyncDate)        
        listPlacePhoto = PlacePhoto.objects.filter(queryPlacePhoto).order_by('id')
        serializer = PlacePhotoSerializer(listPlacePhoto)
        return Response(serializer.data)

placephoto_list = ApiPlacePhotoList.as_view()


class ApiPlacePhotoUpload(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) :
        return render_to_response('mobile_upload_placephoto.html', {'message': _(u"Загрузите фотографию к месту:")})
    def post(self, request) :
        placeId = request.POST['place']
        try:
            lat = float(request.POST.get('lat', ''))
            lng = float(request.POST.get('lng', ''))
        except ValueError:
            lat = lng = None
        # TODO: remove after changes in mobile app
        if not (lat and lng):
            lat = lng = None
        #       ----------------------------------
        dtCreated = None
        if request.POST.get('dt_created') :
            dtCreated = datetime.strptime(request.POST['dt_created'], templateDateTime)
            dtCreated = utc2local(dtCreated)
        data = ""
        listPhoto = []
        try:
            place = Place.objects.get(id = placeId)            
            photo_content = ContentFile(request.FILES['photo'].read())
            photo = PlacePhoto(place=place, lat = lat, lng = lng, comment = '', creator = request.user, dt_created = dtCreated)
            photo.save()
            photo.bfile.save(request.FILES['photo'].name, photo_content)
            write_log(request, place, _(u"Прикреплено фото: %s") % request.build_absolute_uri(photo.bfile.url))
            if lat is not None and lng is not None:
                place.lat = lat
                place.lng = lng
                place.save()
            listPhoto.append(photo)
            serializer = PlacePhotoSerializer(listPhoto)
            return Response(serializer.data)
        except Place.DoesNotExist:
            place = None
            raise Http404
    
placephoto_upload = ApiPlacePhotoUpload.as_view()

class ApiPlacePhotoDelete(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) :
        return render_to_response('mobile_remove_placephoto.html', {'message': _(u"Удалить фотографию к месту:")})
    def post(self, request) :
        placePhotoId = request.POST['placePhotoId']
        try :
            placePhoto = PlacePhoto.objects.get(id = placePhotoId)
            placePhoto.delete()
            return Response("Ok")
        except PlacePhoto.DoesNotExist:
            return Response("Ok")
    
placephoto_delete = ApiPlacePhotoDelete.as_view()

class ApiMobilekeeperVersion(APIView):

    def get(self, request):
        try:
            ap = apk.APK(os.path.join(settings.MEDIA_ROOT, settings.MOBILEKEEPER_MEDIA_PATH))
            return Response(status=200, data=dict(
                versionName=ap.get_androidversion_name(),
                versionCode=ap.get_androidversion_code(),
                url=request.build_absolute_uri(os.path.join(settings.MEDIA_URL, settings.MOBILEKEEPER_MEDIA_PATH))
            ))
        except:
            return Response(status=400, data={'status': 'error', 'message': None})

api_mobilekeeper_version = ApiMobilekeeperVersion.as_view()

