# coding=utf-8

from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.http import Http404

# REST import
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# EOF REST import


from serializers import PlaceLogSerializer

from burials.models import Place, Grave, Burial
from logs.models import Log

def getLogQuerySet(log_type=None, place=None):
    if log_type == "place" and place and place.id:
        ct_place = ContentType.objects.get(app_label="burials", model="place")
        ct_grave = ContentType.objects.get(app_label="burials", model="grave")
        ct_burial = ContentType.objects.get(app_label="burials", model="burial")
        ct_fl = ContentType.objects.get(app_label="persons", model="aliveperson")
        
        responsible_ids = []
        if Place.responsible:
            responsible_ids.append(place.responsible_id)
    
        grave_ids = [i.pk for i in Grave.objects.filter(place__pk=place.id)]
    
        burial_ids = [i.pk for i in Burial.objects.filter(
            cemetery=place.cemetery,
            area=place.area,
            row=place.row,
            place_number=place.place,
        )]

        qs = Log.objects.filter(
            Q(obj_id = place.id) & Q(ct=ct_place) | \
            Q(obj_id__in = grave_ids) & Q(ct=ct_grave) | \
            Q(obj_id__in = burial_ids) & Q(ct=ct_burial) | \
            Q(obj_id__in = responsible_ids) & Q(ct=ct_fl)
        )
    else:
        raise Http404()
    return qs.all()


class LogViewSet(viewsets.ModelViewSet):
    model = Log
    serializer_class = PlaceLogSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None

    def get_queryset(self):
        log_type = self.request.GET.get("type")
        try:
            id = int(self.request.GET.get('id'))
            place = Place.objects.get(pk=id)
        except:
            raise Http404()
        return  getLogQuerySet(log_type=log_type, place=place)
