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


from serializers import LogSerializer

from burials.models import Place, Grave
from logs.models import Log

class LogViewSet(viewsets.ModelViewSet):
    model = Log
    serializer_class = LogSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None

    def get_queryset(self):
        log_type = self.request.GET.get("type")
        if log_type == "place":
            ct_place = ContentType.objects.get(app_label="burials", model="place")
            ct_grave = ContentType.objects.get(app_label="burials", model="grave")
            ct_fl = ContentType.objects.get(app_label="persons", model="aliveperson")
            
            try:
                id = int(self.request.GET.get('id'))
                place = Place.objects.get(pk=id)
            except:
                raise Http404()
            responsible_ids = []
            if Place.responsible:
                responsible_ids.append(place.responsible_id)
 
            grave_ids = [i.pk for i in Grave.objects.filter(place__pk=id)]

            qs = self.model.objects.select_related()
            qs = qs.filter( Q(Q(obj_id = id) & Q(ct=ct_place)) | \
                            Q(Q(obj_id__in = grave_ids) & Q(ct=ct_grave)) | \
                            Q(Q(obj_id__in = responsible_ids) & Q(ct=ct_fl)) )
        else:
            raise Http404()
        
        return qs.all()