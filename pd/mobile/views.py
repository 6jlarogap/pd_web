# coding=utf-8

from django.shortcuts import render_to_response
from django.views.generic.base import View
from django.utils.translation import ugettext as _

from burials.views import LoginRequiredMixin

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse

from django.utils import simplejson
from burials.models import Cemetery
from burials.models import Area
from burials.models import Place
from burials.models import Grave
from burials.models import GravePhoto
from users.models import Profile
from users.models import Org
from django.core import serializers

from cStringIO import StringIO
from django.utils.dateparse import parse_datetime
from django.core.files.base import ContentFile
from django.http import Http404

class MobileGetCemetery(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):        
        user = request.user
        listCemetery = Cemetery.objects.filter(ugh = user.profile.org).order_by('id')
        data = serializers.serialize("json", listCemetery, fields=('name'))
        return HttpResponse(data, mimetype='application/json')      
        
mobile_get_cemetery = MobileGetCemetery.as_view()

class MobileGetArea(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        argCemeteryId = request.GET.get('cemeteryId', None)
        user = request.user
        if argCemeteryId :
            listArea = Area.objects.filter(cemetery__ugh = user.profile.org).filter(cemetery_id = argCemeteryId).order_by('cemetery', 'id')
        else :
            listArea = Area.objects.filter(cemetery__ugh = user.profile.org).order_by('cemetery', 'id')
        data = serializers.serialize("json", listArea, fields=('cemetery','name'))
        return HttpResponse(data, mimetype='application/json')
                
mobile_get_area = MobileGetArea.as_view()

class MobileGetPlace(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        argAreaId = request.GET.get('areaId', None)
        user = request.user
        if argAreaId :
            listPlace = Place.objects.filter(cemetery__ugh = user.profile.org).filter(area_id = argAreaId).order_by('cemetery', 'area', 'id')
        else :
            listPlace = Place.objects.filter(cemetery__ugh = user.profile.org).order_by('cemetery', 'area', 'id')        
        data = serializers.serialize("json", listPlace, fields=('cemetery','area','row','place'))       
        return HttpResponse(data, mimetype='application/json')
        
mobile_get_place = MobileGetPlace.as_view()

class MobileGetGrave(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        argPlaceId = request.GET.get('placeId', None)
        user = request.user
        if argPlaceId :
            listGrave = Grave.objects.all().filter(place__cemetery__ugh = user.profile.org).filter(place_id = argPlaceId).order_by('id')
        else :
            listGrave = Grave.objects.all().filter(place__cemetery__ugh = user.profile.org).order_by('id')
        data = serializers.serialize("json", listGrave, fields=('place','grave_number'))
        return HttpResponse(data, mimetype='application/json')
        
mobile_get_grave = MobileGetGrave.as_view()

@csrf_exempt
def mobile_upload_photo(request):
    if request.method == 'POST':
        result = ""
        graveId = request.POST['grave']
        lat = request.POST['lat']
        lng = request.POST['lng']        
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
            result = "Ok"
        except Grave.DoesNotExist:
            grave = None
            raise Http404
        return HttpResponse(result, mimetype='application/json')
    return render_to_response('mobile_upload_photo.html', {'message': _(u"Загрузите фотографию к могиле:")})
    
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
        areaId = int(request.POST['areaId'])
        placeId = int(request.POST['placeId'])
        listInsertedPlace = []
        try:
            area = Area.objects.get(pk = areaId)
            prevPlace = Place.objects.get(pk = placeId)
            if prevPlace.place != placeName or prevPlace.row != rowName or prevPlace.area != area:
                prevPlace.place = placeName
                prevPlace.row = rowName
                prevPlace.area = area
                prevPlace.cemetery = area.cemetery
                prevPlace.save()
        except Area.DoesNotExist:
            raise Http404
        except Place.DoesNotExist:
            prevPlace = None
            place = Place(cemetery = area.cemetery, area = area, place = placeName, row = rowName)  
            place.save()
            listInsertedPlace.append(place)                                    
        data = serializers.serialize("json", listInsertedPlace, fields=('cemetery','area','row','place'))
        return HttpResponse(data, mimetype='application/json')
    return render_to_response('mobile_upload_place.html', {'message': _(u"Загрузите название места:")})
    
@csrf_exempt
def mobile_upload_grave(request):    
    if request.method == 'POST':
        graveName = request.POST['graveName']
        graveId = int(request.POST['graveId'])
        placeId = int(request.POST['placeId'])
        listInsertedGrave = []
        try:
            place = Place.objects.get(pk = placeId)
            prevGrave = Grave.objects.get(pk = graveId)
            if prevGrave.grave_number != graveName or prevGrave.place != place:
                prevGrave.grave_number = graveName
                prevGrave.place = place
                prevGrave.save()
        except Place.DoesNotExist:
            raise Http404            
        except Grave.DoesNotExist:
            prevGrave = None
            grave = Grave(place = place, grave_number = graveName)
            grave.save()
            listInsertedGrave.append(grave)
        data = serializers.serialize("json", listInsertedGrave, fields=('place','grave_number'))
        return HttpResponse(data, mimetype='application/json')
    return render_to_response('mobile_upload_grave.html', {'message': _(u"Загрузите название могилы:")})