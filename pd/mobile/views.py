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
from burials.models import Area
from burials.models import Place
from burials.models import PlaceStatus
from burials.models import Grave
from burials.models import GravePhoto
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


class MobileGetCemetery(UGHRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        argSyncDateUnix = request.GET.get('syncDate', None)        
        queryCemetery = Q(ugh = request.user.profile.org)
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryCemetery &= Q(dt_modified__gte = argSyncDate)
        listCemetery = Cemetery.objects.filter(queryCemetery).order_by('id')
        data = serializers.serialize("json", listCemetery, fields=('name'))
        return HttpResponse(data, mimetype='application/json')      
        
mobile_get_cemetery = MobileGetCemetery.as_view()

class MobileGetArea(UGHRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        argSyncDateUnix = request.GET.get('syncDate', None) 
        argCemeteryId = request.GET.get('cemeteryId', None)        
        queryArea = Q(cemetery__ugh = request.user.profile.org)
        if argCemeteryId :
            queryArea &= Q(cemetery__pk = argCemeteryId)
        if argSyncDateUnix :
            argSyncDate = datetime.fromtimestamp(int(argSyncDateUnix))
            queryArea &= Q(dt_modified__gte = argSyncDate)
        listArea = Area.objects.filter(queryArea).order_by('cemetery', 'id')
        data = serializers.serialize("json", listArea, fields=('cemetery','name'))
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
                                
        queryPlaceStatus = 'select ps.* from burials_placestatus ps inner join burials_place p on ps.place_id = p.id inner join burials_cemetery c on p.cemetery_id = c.id inner join users_org org on c.ugh_id = org.id where org.id = %d and ps.dt_created = (select max(ps2.dt_created) from burials_placestatus ps2 where ps2.place_id = ps.place_id) ' % request.user.profile.org.pk
        if argAreaId :
            queryPlaceStatus = queryPlaceStatus + ' and p.area_id = %s'% argAreaId
        if argCemeteryId :
            queryPlaceStatus = queryPlaceStatus + ' and p.cemetery_id = %s'% argCemeteryId
        if argSyncDateUnix :
            queryPlaceStatus = queryPlaceStatus + ' and extract (epoch from p.dt_modified) >= %s'% argSyncDateUnix
        listPlaceStatus = PlaceStatus.objects.raw(queryPlaceStatus) 
        
        all_objects = list(listPlace) + list(listPlaceStatus)
        data = serializers.serialize("json", all_objects, fields=('cemetery','area','row','place','oldplace','status'))     
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
        data = serializers.serialize("json", all_objects, fields=('grave', 'fact_date', 'deadman', 'first_name', 'last_name', 'middle_name'))
        return HttpResponse(data, mimetype='application/json')
        
mobile_get_burial = MobileGetBurial.as_view()

@csrf_exempt
def mobile_upload_photo(request):
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
    return render_to_response('mobile_upload_photo.html', {'message': _(u"Загрузите фотографию к могиле:")})
	
@csrf_exempt
def mobile_remove_photo(request):
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
def mobile_upload_cemetery(request):    
    org = request.user.profile.org    
    if request.method == 'POST':
        listInsertedCemetery = []
        cemeteryId = int(request.POST['cemeteryId'])
        cemeteryName = request.POST['cemeteryName']
        try:
            prevCem = Cemetery.objects.get(pk = cemeteryId)
            if prevCem.name != cemeteryName :
                prevCem.name = cemeteryName
                prevCem.save()
        except Cemetery.DoesNotExist:
            prevCem = None
            cem = Cemetery(name = cemeteryName, creator = request.user, ugh = org)
            cem.save()
            listInsertedCemetery.append(cem)
        data = serializers.serialize("json", listInsertedCemetery, fields=('name'))
        return HttpResponse(data, mimetype='application/json')
    return render_to_response('mobile_upload_cemetery.html', {'message': _(u"Загрузите название кладбища:")})
    
@csrf_exempt
def mobile_upload_area(request):    
    if request.method == 'POST':
        listInsertedArea = []
        areaName = request.POST['areaName']
        areaId = int(request.POST['areaId'])
        cemeteryId = int(request.POST['cemeteryId'])
        try:
            cemetery = Cemetery.objects.get(pk = cemeteryId)
            prevArea = Area.objects.get(pk = areaId)
            if prevArea.name != areaName or prevArea.cemetery != cemetery :
                prevArea.name = areaName
                prevArea.cemetery = cemetery                
                prevArea.save()
        except Cemetery.DoesNotExist:
            raise Http404
        except Area.DoesNotExist:
            prevArea = None
            area = Area(cemetery = cemetery, name = areaName)            
            area.save()
            listInsertedArea.append(area)
        data = serializers.serialize("json", listInsertedArea, fields=('cemetery','name'))
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
        psFoundUnowned = int(request.POST['psFoundUnowned'])
        user = request.user
        listPlaceForResponse = []
        try:
            area = Area.objects.get(pk = areaId)
            prevPlace = Place.objects.get(pk = placeId)
            if (prevPlace.place or "") != placeName or (prevPlace.oldplace or "") != oldPlaceName or (prevPlace.row or "") != rowName or prevPlace.area != area:
                if (prevPlace.oldplace or "") != oldPlaceName :
                    write_log(request, prevPlace, _(u'Переименование места (place=%s, oldplace=%s) в (place=%s, oldplace=%s)' % (prevPlace.place, prevPlace.oldplace, placeName, oldPlaceName)))
                    prevPlace.oldplace = oldPlaceName
                prevPlace.place = placeName
                prevPlace.row = rowName
                prevPlace.area = area
                prevPlace.cemetery = area.cemetery
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
                prevPlace.save()
                place = prevPlace                
            else :
                place = Place(cemetery = area.cemetery, area = area, place = placeName, row = rowName, oldplace = oldPlaceName)  
                place.save()
            listPlaceForResponse.append(place)
               
        try:
            curPlaceStatus = PlaceStatus.objects.filter(place__cemetery__ugh=request.user.profile.org, place__pk = placeId ).order_by('-dt_created')[0]
        except IndexError:
            curPlaceStatus = None        
        if psFoundUnowned == 1 :
            if curPlaceStatus :                
                if curPlaceStatus.status != PlaceStatus.PS_FOUND_UNOWNED :
                    curPlaceStatus = PlaceStatus.objects.create(place = place, status = PlaceStatus.PS_FOUND_UNOWNED, creator = request.user)
            else :
                curPlaceStatus = PlaceStatus.objects.create(place = place, status = PlaceStatus.PS_FOUND_UNOWNED, creator = request.user)
        else:
            if curPlaceStatus :
                if curPlaceStatus.status == PlaceStatus.PS_FOUND_UNOWNED :
                    curPlaceStatus = PlaceStatus.objects.create(place = place, status = PlaceStatus.PS_ACTUAL, creator = request.user)
            else :
                curPlaceStatus = PlaceStatus.objects.create(place = place, status = PlaceStatus.PS_ACTUAL, creator = request.user)
        
        listPlaceForResponse.append(curPlaceStatus)
        data = serializers.serialize("json", listPlaceForResponse, fields=('cemetery','area','row','place','oldplace','status'))
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