# coding=utf-8

from django.conf import settings
from django.db import models
from django.db.models.query_utils import Q

from logs.models import write_log
from . import models as burials_models
from django.utils.translation import ugettext as _


class PlaceManager(models.Manager):
    def cancel_exhumation(self, request, burial):
        qs = Q(burial__ugh=request.user.profile.org) | Q(burial__cemetery__ugh=request.user.profile.org)
        qs = burials_models.ExhumationRequest.objects.filter(burial=burial).filter(qs).distinct()
        if qs.count():
            for row in qs.all():
                row.place = burial.place
                row.delete()
            write_log(request, burial, _('Эксгумация отменена'))        
            return True