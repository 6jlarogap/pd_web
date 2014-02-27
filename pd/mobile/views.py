# coding=utf-8
from django.shortcuts import render_to_response
from django.views.generic.base import View
from django.utils.translation import ugettext as _

from burials.views import UGHRequiredMixin

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse

from django.utils import simplejson
from burials.models import Cemetery
from burials.models import CemeteryCoordinates
from burials.models import Area
from burials.models import AreaCoordinates
from burials.models import Place
from burials.models import PlaceStatus
from burials.models import Grave
from burials.models import GravePhoto
from burials.models import PlacePhoto
from burials.models import Burial
from persons.models import DeadPerson
from persons.models import BasePerson
from users.models import Profile
from users.models import Org
from logs.models import write_log
from django.core import serializers

from cStringIO import StringIO
from django.utils.dateparse import parse_datetime
from django.core.files.base import ContentFile
from django.http import Http404
from django.db.models import Q
from datetime import datetime
from decimal import Decimal


class MobileGetCemetery(UGHRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        argCemeteryId = request.GET.get('cemeteryId', None)
        argSyncDateUnix = request.GET.get('syncDate', None)        
        queryCemetery = Q(ugh = request.user.profile.org)
        queryCemeteryCoordinates = Q(cemetery__ugh = request.user.profile.org)
        if argCemeteryId :
            queryCemetery &= Q(pk = argCemeteryId)
            queryCemeteryCoordinates &= Q(cemetery__pk = argCemeteryId)
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryCemetery &= Q(dt_modified__gte = argSyncDate)
            queryCemeteryCoordinates &= Q(cemetery__dt_modified__gte = argSyncDate)
        listCemetery = Cemetery.objects.filter(queryCemetery).order_by('id')
        listCemeteryCoordinates = CemeteryCoordinates.objects.filter(queryCemeteryCoordinates).order_by('cemetery')
        all_objects = list(listCemetery) + list(listCemeteryCoordinates)        
        data = serializers.serialize("json", all_objects, fields=('name', 'cemetery', 'angle_number', 'lat', 'lng'))
        return HttpResponse(data, mimetype='application/json')   
        
mobile_get_cemetery = MobileGetCemetery.as_view()

class MobileGetArea(UGHRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        argSyncDateUnix = request.GET.get('syncDate', None) 
        argCemeteryId = request.GET.get('cemeteryId', None)
        argAreaId = request.GET.get('areaId', None)        
        queryArea = Q(cemetery__ugh = request.user.profile.org)
        queryAreaCoordinates = Q(area__cemetery__ugh = request.user.profile.org)
        if argCemeteryId :
            queryArea &= Q(cemetery__pk = argCemeteryId)
            queryAreaCoordinates &= Q(area__cemetery__pk = argCemeteryId)
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryArea &= Q(dt_modified__gte = argSyncDate)
            queryAreaCoordinates &= Q(area__dt_modified__gte = argSyncDate)
        if argAreaId :
            queryArea &= Q(pk = argAreaId)
            queryAreaCoordinates &= Q(area__pk = argAreaId)
        listArea = Area.objects.filter(queryArea).order_by('cemetery', 'id')
        listAreaCoordinates = AreaCoordinates.objects.filter(queryAreaCoordinates).order_by('area')
        all_objects = list(listArea) + list(listAreaCoordinates)
        data = serializers.serialize("json", all_objects, fields=('cemetery','name', 'area', 'angle_number', 'lat', 'lng'))
        return HttpResponse(data, mimetype='application/json')
                
mobile_get_area = MobileGetArea.as_view()

class MobileGetPlace(UGHRequiredMixin, View):
    def get(self, request, *args, **kwargs):
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
        
        data = serializers.serialize("json", listPlace, fields=('cemetery','area','row','place','oldplace', 'place_width', 'place_length', \
            'dt_wrong_fio', 'dt_military', 'dt_size_violated', 'dt_unowned','dt_unindentified'))     
        return HttpResponse(data, mimetype='application/json')
        
mobile_get_place = MobileGetPlace.as_view()

class MobileGetGrave(UGHRequiredMixin, View):
    def get(self, request, *args, **kwargs):
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
        
        data = serializers.serialize("json", listGrave, fields=('place','grave_number','is_military','is_wrong_fio'))
        return HttpResponse(data, mimetype='application/json')
        
mobile_get_grave = MobileGetGrave.as_view()

class MobileGetBurial(UGHRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        argSyncDateUnix = request.GET.get('syncDate', None) 
        argGraveId = request.GET.get('graveId', None)
        argCemeteryId = request.GET.get('cemeteryId', None)
        argAreaId = request.GET.get('areaId', None)
        
        queryBurial = Q(grave__place__cemetery__ugh = request.user.profile.org)
        if argCemeteryId :
            queryBurial &= Q(grave__place__cemetery__pk = argCemeteryId)
        if argAreaId :
            queryBurial &= Q(grave__place__area__pk = argAreaId)
        if argGraveId :
            queryBurial &= Q(grave__pk = argGraveId)
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryBurial &= Q(dt_modified__gte = argSyncDate)        
        listBurial = Burial.objects.filter(queryBurial).order_by('id')

        queryPerson = Q(deadperson__burial__cemetery__ugh=request.user.profile.org)
        if argGraveId :
            queryPerson &= Q(deadperson__burial__grave__pk=argGraveId) 
        if argCemeteryId :
            queryPerson &= Q(deadperson__burial__cemetery__pk=argCemeteryId)
        if argAreaId :
            queryPerson &= Q(deadperson__burial__area__pk = argAreaId)
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryBurial &= Q(deadperson__burial__dt_modified__gte = argSyncDate)
        listPerson = BasePerson.objects.filter(queryPerson)
                
        all_objects = list(listBurial) + list(listPerson)
        data = serializers.serialize("json", all_objects, fields=('grave', 'fact_date', 'deadman', 'first_name', 'last_name', 'middle_name', 'burial_container'))
        return HttpResponse(data, mimetype='application/json')
        
mobile_get_burial = MobileGetBurial.as_view()

@csrf_exempt
def mobile_upload_gravephoto(request):
    if request.method == 'POST':
        graveId = request.POST['grave']
        lat = request.POST['lat']
        lng = request.POST['lng'] 
        data = ""
        listPhoto = []
        try:
            grave = Grave.objects.get(id = graveId)            
            photo_content = ContentFile(request.FILES['photo'].read())
            photo = GravePhoto(grave=grave, lat = lat, lng = lng, comment = '', creator = request.user)
            photo.save()
            photo.bfile.save(request.FILES['photo'].name, photo_content)            
            if lat and lat :
                grave.lat = lat
                grave.lng = lng
                grave.save()
            listPhoto.append(photo)
            data = serializers.serialize("json", listPhoto, fields=('grave','lat','lng'))
            return HttpResponse(data, mimetype='application/json')
        except Grave.DoesNotExist:
            grave = None
            raise Http404
    return render_to_response('mobile_upload_gravephoto.html', {'message': _(u"Загрузите фотографию к могиле:")})
    
@csrf_exempt
def mobile_upload_placephoto(request):
    if request.method == 'POST':
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
            data = serializers.serialize("json", listPhoto, fields=('place','lat','lng'))
            return HttpResponse(data, mimetype='application/json')
        except Place.DoesNotExist:
            place = None
            raise Http404
    return render_to_response('mobile_upload_placephoto.html', {'message': _(u"Загрузите фотографию к месту:")})
	
@csrf_exempt
def mobile_remove_gravephoto(request):
    if request.method == 'POST':
        gravePhotoId = request.POST['gravePhotoId']
        try :
            gravePhoto = GravePhoto.objects.get(id = gravePhotoId)
            gravePhoto.delete()
            return HttpResponse("Ok", mimetype='application/json')
        except GravePhoto.DoesNotExist:
            return HttpResponse("Ok", mimetype='application/json')                
    return render_to_response('mobile_remove_photo.html', {'message': _(u"Удалить фотографию к могиле:")})
    
@csrf_exempt
def mobile_remove_placephoto(request):
    if request.method == 'POST':
        placePhotoId = request.POST['placePhotoId']
        try :
            placePhoto = PlacePhoto.objects.get(id = placePhotoId)
            placePhoto.delete()
            return HttpResponse("Ok", mimetype='application/json')
        except PlacePhoto.DoesNotExist:
            return HttpResponse("Ok", mimetype='application/json')                
    return render_to_response('mobile_remove_placephoto.html', {'message': _(u"Удалить фотографию к месту:")})
    
@csrf_exempt
def mobile_upload_cemetery(request):    
    org = request.user.profile.org    
    if request.method == 'POST':
        listInsertedCemetery = []
        listGPS = [] 
        cemeteryId = int(request.POST['cemeteryId'])
        cemeteryName = request.POST['cemeteryName']
        gpsJSON = request.POST['gps']
        isGPSChange = False
        if gpsJSON :
            isGPSChange = True
            gpsGenerator = serializers.deserialize("json", gpsJSON)                       
            for obj in gpsGenerator:
                listGPS.append(obj.object)        
        cem = None
        try:
            prevCem = Cemetery.objects.get(pk = cemeteryId)
            if prevCem.name != cemeteryName :
                prevCem.name = cemeteryName
                prevCem.save()
            cem = prevCem
        except Cemetery.DoesNotExist:
            prevCem = None
            cem = Cemetery(name = cemeteryName, creator = request.user, ugh = org)
            cem.save()
            listInsertedCemetery.append(cem)
        if isGPSChange == True :
            CemeteryCoordinates.objects.filter(cemetery__pk = cem.pk).delete()
            for gps in listGPS:
                gps.pk = None
                gps.cemetery = cem
                gps.save()                 
            all_objects = list(listInsertedCemetery) + list(listGPS)
        else :
            all_objects = list(listInsertedCemetery)
        data = serializers.serialize("json", all_objects, fields=('name', 'cemetery', 'angle_number', 'lat', 'lng'))        
        return HttpResponse(data, mimetype='application/json')
    return render_to_response('mobile_upload_cemetery.html', {'message': _(u"Загрузите название кладбища:")})
    
@csrf_exempt
def mobile_upload_area(request):    
    if request.method == 'POST':
        listInsertedArea = []
        listGPS = []
        areaName = request.POST['areaName']
        areaId = int(request.POST['areaId'])
        cemeteryId = int(request.POST['cemeteryId'])
        gpsJSON = request.POST['gps']
        isGPSChange = False
        if gpsJSON :
            isGPSChange = True
            gpsGenerator = serializers.deserialize("json", gpsJSON)                       
            for obj in gpsGenerator:
                listGPS.append(obj.object)
        area = None
        try:
            cemetery = Cemetery.objects.get(pk = cemeteryId)
            prevArea = Area.objects.get(pk = areaId)
            if prevArea.name != areaName or prevArea.cemetery != cemetery :
                prevArea.name = areaName
                prevArea.cemetery = cemetery                
                prevArea.save()
            area = prevArea
        except Cemetery.DoesNotExist:
            raise Http404
        except Area.DoesNotExist:
            prevArea = None
            area = Area(cemetery = cemetery, name = areaName)            
            area.save()
            listInsertedArea.append(area)
        if isGPSChange == True :
            AreaCoordinates.objects.filter(area__pk = area.pk).delete()
            for gps in listGPS:
                gps.pk = None
                gps.area = area
                gps.save()               
            all_objects = list(listInsertedArea) + list(listGPS)
        else :
            all_objects = list(listInsertedArea)
        data = serializers.serialize("json", all_objects, fields=('cemetery','name', 'area', 'angle_number', 'lat', 'lng'))
        return HttpResponse(data, mimetype='application/json')        
    return render_to_response('mobile_upload_area.html', {'message': _(u"Загрузите название участка:")})


@csrf_exempt
def mobile_upload_place(request):
    if request.method == 'POST':
        rowName = request.POST['rowName']
        placeName = request.POST['placeName']
        oldPlaceName = request.POST['oldPlaceName']
        areaId = int(request.POST['areaId'])
        placeId = int(request.POST['placeId'])
        placeLength = None
        placeWidth = None
        dtWrongFio = None
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
                (prevPlace.dt_military is None) != (dtMilitary is None) or (prevPlace.dt_size_violated is None) != (dtSizeViolated is None) or \
                (prevPlace.dt_unowned is None) != (dtUnowned is None) or (prevPlace.dt_unindentified is None) != (dtUnindentified is None) :
                if (prevPlace.oldplace or "") != oldPlaceName :
                    write_log(request, prevPlace, _(u'Переименование места (place=%s, oldplace=%s) в (place=%s, oldplace=%s)' % (prevPlace.place, prevPlace.oldplace, placeName, oldPlaceName)))
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
                    write_log(request, prevPlace, _(u'Переименование места (place=%s, oldplace=%s) в (place=%s, oldplace=%s)' % (prevPlace.place, prevPlace.oldplace, placeName, oldPlaceName)))
                    prevPlace.oldplace = oldPlaceName
                prevPlace.place = placeName
                prevPlace.row = rowName
                prevPlace.place_length = placeLength
                prevPlace.place_width = placeWidth
                if (prevPlace.dt_wrong_fio is None) != (dtWrongFio is None) :
                    prevPlace.dt_wrong_fio = dtWrongFio
                if (prevPlace.dt_military is None) != (dtMilitary is None) :
                    prevPlace.dt_military = dtMilitary
                if (prevPlace.dt_size_violated is None) != (dtSizeViolated is None) :
                    prevPlace.dt_size_violated = dtSizeViolated
                if (prevPlace.dt_unowned is None) != (dtUnowned is None) :
                    prevPlace.dt_unowned = dtUnowned
                if (prevPlace.dt_unindentified is None) != (dtUnindentified is None) :
                    prevPlace.dt_unindentified = dtUnindentified
                prevPlace.save()
                place = prevPlace                
            else :
                place = Place(cemetery = area.cemetery, area = area, place = placeName, row = rowName, oldplace = oldPlaceName, place_length = placeLength, place_width = placeWidth, \
                    dt_wrong_fio = dtWrongFio, dt_military = dtMilitary, dt_size_violated = dtSizeViolated, dt_unowned = dtUnowned, dt_unindentified = dtUnindentified)  
                place.save()
            listPlaceForResponse.append(place)
        
        data = serializers.serialize("json", listPlaceForResponse, fields=('cemetery', 'area', 'row', 'place', 'oldplace', 'place_length', 'place_width', \
            'dt_wrong_fio', 'dt_military', 'dt_size_violated', 'dt_unowned','dt_unindentified'))
        return HttpResponse(data, mimetype='application/json')
    return render_to_response('mobile_upload_place.html', {'message': _(u"Загрузите название места:")})
    
@csrf_exempt
def mobile_upload_grave(request):    
    if request.method == 'POST':
        graveName = request.POST['graveName']
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
            if prevGrave.grave_number != graveName or prevGrave.place != place or prevGrave.is_wrong_fio != isWrongFIO or prevGrave.is_military != isMilitary:
                prevGrave.grave_number = graveName
                prevGrave.place = place
                prevGrave.is_military = isMilitary
                prevGrave.is_wrong_fio = isWrongFIO
                prevGrave.save()
        except Place.DoesNotExist:
            raise Http404            
        except Grave.DoesNotExist:
            prevGrave = None
            grave = Grave(place = place, grave_number = graveName, is_military = isMilitary, is_wrong_fio = isWrongFIO)
            grave.save()
            write_log(request, grave, _(u"Могила '%s' создана через мобильное приложение") % graveName )
            listInsertedGrave.append(grave)
        data = serializers.serialize("json", listInsertedGrave, fields=('place','grave_number','is_military','is_wrong_fio'))
        return HttpResponse(data, mimetype='application/json')
    return render_to_response('mobile_upload_grave.html', {'message': _(u"Загрузите название могилы:")})