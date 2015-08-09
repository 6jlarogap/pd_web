# coding=utf-8
from django.shortcuts import render_to_response
from django.views.generic.base import View
from django.utils.translation import ugettext as _

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse

from django.utils import simplejson
from geo.models import CoordinatesModel
from burials.models import Cemetery
from burials.models import CemeteryCoordinates
from burials.models import Area
from burials.models import AreaCoordinates
from burials.models import Place
from burials.models import PlaceStatus
from burials.models import Grave
from burials.models import PlacePhoto
from burials.models import Burial
from persons.models import DeadPerson
from persons.models import BasePerson
from users.models import Profile
from users.models import Org
from logs.models import write_log
from pd.models import UnclearDate

from django.utils.dateparse import parse_datetime
from django.core.files.base import ContentFile
from django.http import Http404
from django.db.models import Q
from datetime import datetime
from decimal import Decimal

from StringIO import StringIO
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException

from serializers import BaseSerializer, CoordinatesSerializer, CemeterySerializer, CemeteryWithNestedObjectSerializer, \
    AreaSerializer, AreaWithNestedObjectSerializer, RegionSerializer, CitySerializer, StreetSerializer, CountrySerializer, LocationSerializer, \
    BasePersonSerializer, AlivePersonSerializer, PlaceWithNestedObjectSerializer, GraveSerializer, BurialSerializer, \
    PlacePhotoSerializer
    
class CustomException(APIException):
    status_code = 500
    default_detail = 'Custom Exception'
    def __init__(self, detail = None):
        if detail :
            self.detail = detail    
        else :
            self.detail = self.default_detail
        
class ApiCemeteryList(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) :
        queryCemetery = Q(ugh = request.user.profile.org)
        listCemetery = Cemetery.objects.filter(queryCemetery).order_by('id')                      
        serializer = CemeteryWithNestedObjectSerializer(listCemetery)
        return Response(serializer.data)
        
cemetery_list = ApiCemeteryList.as_view()

class ApiCemeteryUpload(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) :
        return render_to_response('mobile_upload_cemetery.html', {'message': _(u"Загрузите название кладбища:")})
    def post(self, request) :
        org = request.user.profile.org
        listInsertedCemetery = []
        listGPS = [] 
        cemeteryId = int(request.POST['cemeteryId'])
        cemeteryName = request.POST['cemeteryName']
        gpsJSON = request.POST['gps']
        square = None
        if request.POST['square'] :
            square = request.POST['square']
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
            cem = Cemetery(name = cemeteryName, square = square, creator = request.user, ugh = org)
            cem.save()
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
    def post(self, request) : 
        listInsertedArea = []
        listGPS = []
        areaName = request.POST['areaName']
        areaId = int(request.POST['areaId'])
        cemeteryId = int(request.POST['cemeteryId'])
        gpsJSON = request.POST['gps']
        square = None
        if request.POST['square'] :
            square = request.POST['square']
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
            area = Area(cemetery = cemetery, name = areaName, square = square)            
            area.save()
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

class ApiPlaceUpload(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request) : 
        return render_to_response('mobile_upload_place.html', {'message': _(u"Загрузите название места:")})    
    def post(self, request) : 
        rowName = request.POST['rowName']
        placeName = request.POST['placeName']
        oldPlaceName = request.POST['oldPlaceName']
        areaId = int(request.POST['areaId'])
        placeId = int(request.POST['placeId'])
        placeLength = None
        placeWidth = None
        dtWrongFio = None
        dtFree = None
        dtMilitary = None
        dtSizeViolated = None
        dtUnowned = None
        dtUnindentified = None        
        if request.POST['placeLength'] :
            placeLength = Decimal(request.POST['placeLength'])
        if request.POST['placeWidth'] :
            placeWidth = Decimal(request.POST['placeWidth'])
        templateDateTime = '%Y-%m-%dT%H:%M:%S.%f'
        if request.POST['dtWrongFio'] :
            dtWrongFio = datetime.strptime(request.POST['dtWrongFio'], templateDateTime)
        if request.POST['dtMilitary'] :
            dtMilitary = datetime.strptime(request.POST['dtMilitary'], templateDateTime)
        if request.POST['dtFree'] :
            dtFree = datetime.strptime(request.POST['dtFree'], templateDateTime)
        if request.POST['dtSizeViolated'] :
            dtSizeViolated = datetime.strptime(request.POST['dtSizeViolated'], templateDateTime)
        if request.POST['dtUnowned'] :
            dtUnowned = datetime.strptime(request.POST['dtUnowned'], templateDateTime)
        if request.POST['dtUnindentified'] :
            dtUnindentified = datetime.strptime(request.POST['dtUnindentified'], templateDateTime)
        user = request.user
        listPlaceForResponse = []
        try:
            area = Area.objects.get(pk = areaId)
            prevPlace = Place.objects.get(pk = placeId)
            if (prevPlace.place or "") != placeName or (prevPlace.oldplace or "") != oldPlaceName or (prevPlace.row or "") != rowName or prevPlace.area != area or \
                prevPlace.place_length != placeLength or prevPlace.place_width != placeWidth or (prevPlace.dt_wrong_fio is None) != (dtWrongFio is None) or \
                (prevPlace.dt_military is None) != (dtMilitary is None) or (prevPlace.dt_free is None) != (dtFree is None) or \
                (prevPlace.dt_size_violated is None) != (dtSizeViolated is None) or \
                (prevPlace.dt_unowned is None) != (dtUnowned is None) or (prevPlace.dt_unindentified is None) != (dtUnindentified is None) :
                if (prevPlace.oldplace or "") != oldPlaceName :
                    write_log(
                        request,
                        prevPlace,
                        _(u'Переименование места (place=%(prev_place)s, oldplace=%(prev_oldplace)s) '
                          u'в (place=%(new_place)s, oldplace=%(new_oldplace)s)') % dict(
                            prev_place=prevPlace.place,
                            prev_oldplace=prevPlace.oldplace,
                            new_place=placeName,
                            new_oldplace=oldPlaceName
                    ))
                    prevPlace.oldplace = oldPlaceName
                prevPlace.place = placeName
                prevPlace.row = rowName
                prevPlace.area = area
                prevPlace.cemetery = area.cemetery
                prevPlace.place_length = placeLength
                prevPlace.place_width = placeWidth
                if (prevPlace.dt_wrong_fio is None) != (dtWrongFio is None) :
                    prevPlace.dt_wrong_fio = dtWrongFio
                if (prevPlace.dt_military is None) != (dtMilitary is None) :
                    prevPlace.dt_military = dtMilitary
                if (prevPlace.dt_free is None) != (dtFree is None) :
                    prevPlace.dt_free = dtFree
                if (prevPlace.dt_size_violated is None) != (dtSizeViolated is None) :
                    prevPlace.dt_size_violated = dtSizeViolated
                if (prevPlace.dt_unowned is None) != (dtUnowned is None) :
                    prevPlace.dt_unowned = dtUnowned
                if (prevPlace.dt_unindentified is None) != (dtUnindentified is None) :
                    prevPlace.dt_unindentified = dtUnindentified
                prevPlace.save()                
            place = prevPlace    
        except Area.DoesNotExist:
            raise Http404
        except Place.DoesNotExist:
            prevPlace = None            
            listFilterByName = Place.objects.filter(cemetery__ugh = user.profile.org, area = area, place = placeName, row = rowName)
            if len(list(listFilterByName)) > 0 :
                prevPlace = listFilterByName[0]                
            else :
                if (oldPlaceName or "") != "" :
                    listFilterByOldName1 = Place.objects.filter(cemetery__ugh = user.profile.org, area = area, oldplace = oldPlaceName, row = rowName)
                    if len(list(listFilterByOldName1)) > 0 :
                        prevPlace = listFilterByOldName1[0]
                    else :
                        listFilterByOldName2 = Place.objects.filter(cemetery__ugh = user.profile.org, area = area, place = oldPlaceName, row = rowName)
                        if len(list(listFilterByOldName2)) > 0 :
                            prevPlace = listFilterByOldName2[0]
            if prevPlace :
                if (prevPlace.oldplace or "") != oldPlaceName :
                    write_log(
                        request,
                        prevPlace,
                        _(u'Переименование места (place=%(prev_place)s, oldplace=%(prev_oldplace)s) '
                          u'в (place=%(new_place)s, oldplace=%(new_oldplace)s)') % dict(
                              prev_place=prevPlace.place,
                              prev_oldplace=prevPlace.oldplace,
                              new_place=placeName,
                              new_oldplace=oldPlaceName
                    ))
                    prevPlace.oldplace = oldPlaceName
                prevPlace.place = placeName
                prevPlace.row = rowName
                prevPlace.place_length = placeLength
                prevPlace.place_width = placeWidth
                if (prevPlace.dt_wrong_fio is None) != (dtWrongFio is None) :
                    prevPlace.dt_wrong_fio = dtWrongFio
                if (prevPlace.dt_military is None) != (dtMilitary is None) :
                    prevPlace.dt_military = dtMilitary
                if (prevPlace.dt_free is None) != (dtFree is None) :
                    prevPlace.dt_free = dtFree
                if (prevPlace.dt_size_violated is None) != (dtSizeViolated is None) :
                    prevPlace.dt_size_violated = dtSizeViolated
                if (prevPlace.dt_unowned is None) != (dtUnowned is None) :
                    prevPlace.dt_unowned = dtUnowned
                if (prevPlace.dt_unindentified is None) != (dtUnindentified is None) :
                    prevPlace.dt_unindentified = dtUnindentified
                prevPlace.save()
                place = prevPlace                
            else :
                place = Place(
                    cemetery = area.cemetery,
                    area = area,
                    place = placeName,
                    row = rowName,
                    oldplace = oldPlaceName,
                    place_length = placeLength,
                    place_width = placeWidth,
                    dt_wrong_fio = dtWrongFio,
                    dt_military = dtMilitary,
                    dt_free = dtFree,
                    dt_size_violated = dtSizeViolated,
                    dt_unowned = dtUnowned,
                    dt_unindentified = dtUnindentified,
                    is_invent=True,
                )
                place.save()
            listPlaceForResponse.append(place)
            
        serializer = PlaceWithNestedObjectSerializer(listPlaceForResponse)
        return Response(serializer.data)
    
place_upload = ApiPlaceUpload.as_view()

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
    def post(self, request) :
        grave_number = request.POST['grave_number']
        graveId = int(request.POST['graveId'])
        placeId = int(request.POST['placeId'])
        isWrongFIO = False
        isMilitary = False
        if int(request.POST['isWrongFIO']) == 1 :
            isWrongFIO = True
        if int(request.POST['isMilitary']) == 1 :
            isMilitary = True		
        listInsertedGrave = []
        try:
            place = Place.objects.get(pk = placeId)
            prevGrave = Grave.objects.get(pk = graveId)
            if prevGrave.grave_number != grave_number or prevGrave.place != place or prevGrave.is_wrong_fio != isWrongFIO or prevGrave.is_military != isMilitary:
                prevGrave.grave_number = grave_number
                prevGrave.place = place
                prevGrave.is_military = isMilitary
                prevGrave.is_wrong_fio = isWrongFIO
                prevGrave.save()
        except Place.DoesNotExist:
            raise Http404            
        except Grave.DoesNotExist:
            prevGrave = None            
            grave = Grave(place = place, grave_number = place.get_graves_count() + 1, is_military = isMilitary, is_wrong_fio = isWrongFIO)
            grave.save()
            write_log(request, grave, _(u"Могила '%s' создана через мобильное приложение") % grave.grave_number )
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
        templateDateTime = '%Y-%m-%dT%H:%M:%S.%f'
        if request.POST['factDate'] :
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
            write_log(request, burial, u"%s\n%s: %s\n%s: %s" % ((u'Захоронение сохранено'), (u'Могила'), grave.full_name(), _(u'Факт. дата'), burial.fact_date))            
            burial.close(request=request)
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
        lat = request.POST['lat']
        lng = request.POST['lng'] 
        data = ""
        listPhoto = []
        try:
            place = Place.objects.get(id = placeId)            
            photo_content = ContentFile(request.FILES['photo'].read())
            photo = PlacePhoto(place=place, lat = lat, lng = lng, comment = '', creator = request.user)
            photo.save()
            photo.bfile.save(request.FILES['photo'].name, photo_content)            
            if lat and lat :
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