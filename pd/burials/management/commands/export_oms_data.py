# -*- coding: utf-8 -*-

import os, zipfile
from xml.dom import minidom

from django.core.management.base import NoArgsCommand

from rest_framework.renderers import XMLRenderer

from django.conf import settings

from burials.models import Cemetery
from users.models import Org

from burials.serializers import ArchCemeterySerializer

# парка в settings.MEDIA_ROOT, где будем складывать архивы /<pk>/org-data.zip:
#
MEDIA_STORAGE = 'org-data'
# имя файла.xml в архиве = имя архива.zip:
#
XML_NAME = ZIP_NAME = 'org-data'

class Command(NoArgsCommand):
    help = 'Collect OMS data and put it to media'

    def handle_ugh(self, ugh):
        try:
            folder = os.path.join(settings.MEDIA_ROOT, MEDIA_STORAGE, "%s" % ugh.pk)
            os.mkdir(folder)
        except OSError:
            pass

        xml = minidom.parseString(XMLRenderer().render(dict(
            cemeteries=[ArchCemeterySerializer(c).data for c in Cemetery.objects.filter(ugh=ugh)]
        )))

        fname = "%s.xml" % XML_NAME
        zip_name = os.path.join(folder, "%s.zip" % ZIP_NAME)
        with zipfile.ZipFile(zip_name,'w') as zip_: zip_.writestr(fname, xml.toprettyxml().encode('utf-8'))

    def handle_noargs(self, **options):
        
        try:
            os.mkdir(os.path.join(settings.MEDIA_ROOT, MEDIA_STORAGE))
        except OSError:
            pass
        for ugh in Org.objects.filter(type=Org.PROFILE_UGH):
            self.handle_ugh(ugh)
