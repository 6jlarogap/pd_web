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
from burials.models import Photo
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
            photo = Photo(lat = lat, lng = lng, comment = '', creator = request.user)
            photo.save()
            photo.bfile.save(request.FILES['photo'].name, photo_content)            
            grave.photos.add(photo)
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
    listInsertedCemetery = []
    user = request.user
    profile = Profile.objects.filter(user__id = user.id)[0]
    org = Org.objects.filter(pk = profile.org.id)[0]
    const_begin_datetime = parse_datetime("2012-02-21 10:00:00")
    const_end_datetime = parse_datetime("2012-02-21 17:00:00")
    const_begin_time = const_begin_datetime.time()
    const_end_time = const_end_datetime.time()
    if request.method == 'POST':
        result = "OK"
        listCemetery = []
        listDeserializedCemetery = serializers.deserialize("json", request.FILES['cemeteryjson'])
        for deserialized_object in listDeserializedCemetery :
            listCemetery.append(deserialized_object.object)
        for cem in listCemetery :
            if cem.pk > 0 :
                try:
                    prevCem = Cemetery.objects.get(pk = cem.pk)
                    if prevCem.name != cem.name :
                        prevCem.name = cem.name
                        prevCem.save()
                except Cemetery.DoesNotExist:
                    prevCem = None
            else :
                cem.id = None
                cem.time_begin = const_begin_time
                cem.time_end = const_end_time
                cem.creator = user
                cem.ugh = org
                cem.save()
                listInsertedCemetery.append(cem)
        data = serializers.serialize("json", listInsertedCemetery, fields=('cemetery','name'))
        return HttpResponse(data, mimetype='application/json')
    return render_to_response('mobile_upload_cemetery.html', {'message': _(u"Загрузите список кладбищ(json):")})
    
@csrf_exempt
def mobile_upload_area(request):
    listInsertedArea = []
    user = request.user
    profile = Profile.objects.filter(user__id = user.id)[0]
    org = Org.objects.filter(pk = profile.org.id)[0]
    if request.method == 'POST':
        listArea = []
        listDeserializedArea = serializers.deserialize("json", request.FILES['areajson'])
        for deserialized_object in listDeserializedArea :
            listArea.append(deserialized_object.object)
        for area in listArea :
            if area.pk > 0 :
                try:
                    prevArea = Area.objects.get(pk = area.pk)
                    if prevArea.name != area.name :
                        prevArea.name = area.name
                        prevArea.save()
                except Area.DoesNotExist:
                    prevArea = None
            else :
                area.id = None
                area.save()
                listInsertedArea.append(area)
        data = serializers.serialize("json", listInsertedArea, fields=('cemetery','name'))
        return HttpResponse(data, mimetype='application/json')        
    return render_to_response('mobile_upload_area.html', {'message': _(u"Загрузите список участков(json):")})

@csrf_exempt
def mobile_upload_place(request):
    listInsertedPlace = []
    user = request.user
    profile = Profile.objects.filter(user__id = user.id)[0]
    org = Org.objects.filter(pk = profile.org.id)[0]
    if request.method == 'POST':
        listPlace = []
        listDeserializedPlace = serializers.deserialize("json", request.FILES['placejson'])
        for deserialized_object in listDeserializedPlace :
            listPlace.append(deserialized_object.object)
        for place in listPlace :
            if place.pk > 0 :
                try:
                    prevPlace = Place.objects.get(pk = place.pk)
                    if prevPlace.place != place.place or prevPlace.row != place.row :
                        prevPlace.place = place.place
                        prevPlace.row = place.row
                        prevPlace.save()
                except Place.DoesNotExist:
                    prevPlace = None
            else :
                try :
                    place.id = None
                    place.save()
                    listInsertedPlace.append(place)
                except Exception as e:
                    filteredPlaces = Place.objects.filter(cemetery=place.cemetery.pk).filter(area=place.area.pk).filter(row=place.row).filter(place=place.place)
                    if filteredPlaces :
                        listInsertedPlace.append(filteredPlaces[0])                        
        data = serializers.serialize("json", listInsertedPlace, fields=('cemetery','area','row','place'))
        return HttpResponse(data, mimetype='application/json')
    return render_to_response('mobile_upload_place.html', {'message': _(u"Загрузите список мест(json):")})
    
@csrf_exempt
def mobile_upload_grave(request):
    listInsertedGrave = []
    user = request.user
    profile = Profile.objects.filter(user__id = user.id)[0]
    org = Org.objects.filter(pk = profile.org.id)[0]
    if request.method == 'POST':
        listGrave = []
        listDeserializedGrave = serializers.deserialize("json", request.FILES['gravejson'])
        for deserialized_object in listDeserializedGrave :
            listGrave.append(deserialized_object.object)
        for grave in listGrave :
            if grave.pk > 0 :
                try:
                    prevGrave = Grave.objects.get(pk = grave.pk)
                    if prevGrave.grave_number != grave.grave_number :
                        prevGrave.grave_number = grave.grave_number
                        prevGrave.save()
                except Grave.DoesNotExist:
                    prevGrave = None
            else :
                grave.id = None
                grave.save()
                listInsertedGrave.append(grave)
        data = serializers.serialize("json", listInsertedGrave, fields=('place','grave_number'))
        return HttpResponse(data, mimetype='application/json')
    return render_to_response('mobile_upload_grave.html', {'message': _(u"Загрузите список могил(json):")})