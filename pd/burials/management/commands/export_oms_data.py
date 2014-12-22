# -*- coding: utf-8 -*-
#
# export_oms_data.py
#
# Архивация информации по захоронениям у всех ОМС, так чтобы была возможность
# создать их заново из этой информации. Архивы записываются в
# MEDIA_ROOT/org-data/:омс_id/org-data.zip
#
# TODO: Ограничить доступ к этим архивам.
#
# Запуск: ./manage.py export_oms_data
#
# NB: 
#   - выводим данные во временные файлы, из которых делаем zip- архивы
#   - выводим запись за записью из таблиц. Ибо количество захоронений может быть
#     огромным, посему сериализация всех захоронений одного ОМС может
#     породить структуру данных, которая не вместится в память
#
import os, zipfile, tempfile
from xml.dom import minidom
from xml.etree import ElementTree as ET

from django.core.management.base import NoArgsCommand
from django.db.models.query_utils import Q

from rest_framework.renderers import XMLRenderer
from rest_framework.compat import StringIO

from django.conf import settings

from burials.models import Cemetery
from users.models import Org

from billing.serializers import ArchCurrencySerializer

from burials.serializers import ArchCemeterySerializer, ArchCemeteryCoordinatesSerializer, \
                                AreaPurposeSerializer, ArchAreaSerializer, \
                                ArchAreaCoordinatesSerializer, ArchPlaceSizeSerializer, \
                                ArchPlacePhotoSerializer, ArchPlaceSerializer, \
                                ArchAreaPhotoSerializer, ArchReasonSerializer, \
                                ArchBurialSerializer, ArchBurialFilesSerializer, \
                                ArchExhumationRequestSerializer, ArchGraveSerializer

from geo.serializers import ArchCountrySerializer, ArchRegionSerializer, \
                            ArchCitySerializer, ArchStreetSerializer, \
                            ArchLocationSerializer

from persons.serializers import ArchIDDocumentTypeSerializer, ArchDocumentSourceSerializer, \
                                ArchPersonIDSerializer, ArchAlivePersonSerializer, \
                                ArchDeathCertificateSerializer, ArchDeathCertificateScanSerializer, \
                                ArchDeadPersonSerializer

from users.serializers import ArchUserSerializer, ArchProfileSerializer, ArchOrgSerializer, \
                              ArchDoverSerializer

# парка в settings.MEDIA_ROOT, где будем складывать архивы /<pk>/org-data.zip:
#
MEDIA_STORAGE = 'org-data'
# имя файла.xml в архиве = имя архива.zip:
#
XML_NAME = ZIP_NAME = 'org-data'

class Command(NoArgsCommand):
    help = 'Collect OMS data and put it to media'
    
    # Дескриптор временного файла:
    #
    f = None
    
    def xml_indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.xml_indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def handle_fields(self, r, d):
        if isinstance(d, dict):
            for k, v in d.iteritems():
                s = ET.SubElement(r, k)
                self.handle_fields(s, v)
        elif isinstance(d, tuple) or isinstance(d, list):
            for v in d:
                s = ET.SubElement(r, 'list-item')
                self.handle_fields(s, v)
        elif d is None:
            r.text = d
        else:
            r.text = unicode(d)
        return r

    def handle_rec(self, data, title):
        r = ET.Element(title)
        xml = self.handle_fields(r, data)
        self.xml_indent(xml)
        return ET.tostring(xml, encoding="utf-8", method="xml")

    def handle_model(self, title, serializer, queryset):
        objects = serializer.Meta.model.objects
        if queryset:
            where = objects.filter(queryset).distinct()
        else:
            where = objects.all()
        for c in where:
            data = serializer(c).data
            st = self.handle_rec(data, title)
            self.f.write(st)

    def handle_ugh(self, ugh):
        folder = os.path.join(settings.MEDIA_ROOT, MEDIA_STORAGE, "%s" % ugh.pk)
        try:
            os.mkdir(folder)
        except OSError:
            pass

        try:
            self.f = tempfile.NamedTemporaryFile(delete=False)
            
            # Заголовок: <?xml version='1.0' encoding='utf-8'?>
            #
            temp_stream = StringIO()
            temp_et = ET.Element('cem')
            ET.ElementTree(temp_et).write(temp_stream, encoding="utf-8", xml_declaration=True)
            self.f.write(u"%s\n<root>\n" % temp_stream.getvalue().split("\n", 1)[0])

            country_qs =    Q(region__city__street__location__cemetery__ugh=ugh) | \
                            Q(region__city__street__location__org=ugh) | \
                            Q(region__city__street__location__baseperson__aliveperson__applied_burials__ugh=ugh) | \
                            Q(region__city__street__location__org__burial__ugh=ugh) | \
                            Q(region__city__street__location__org__applicant_organization_burials__ugh=ugh) | \
                            Q(region__city__street__location__org__exhumationrequest__burial__ugh=ugh)

            region_qs =     Q(city__street__location__cemetery__ugh=ugh) | \
                            Q(city__street__location__org=ugh) | \
                            Q(city__street__location__baseperson__aliveperson__applied_burials__ugh=ugh) | \
                            Q(city__street__location__org__burial__ugh=ugh) | \
                            Q(city__street__location__org__applicant_organization_burials__ugh=ugh) | \
                            Q(city__street__location__org__exhumationrequest__burial__ugh=ugh)

            city_qs =       Q(street__location__cemetery__ugh=ugh) | \
                            Q(street__location__org=ugh) | \
                            Q(street__location__baseperson__aliveperson__applied_burials__ugh=ugh) | \
                            Q(street__location__org__burial__ugh=ugh) | \
                            Q(street__location__org__applicant_organization_burials__ugh=ugh) | \
                            Q(street__location__org__exhumationrequest__burial__ugh=ugh)

            street_qs =     Q(location__cemetery__ugh=ugh) | \
                            Q(location__org=ugh) | \
                            Q(location__baseperson__aliveperson__applied_burials__ugh=ugh) | \
                            Q(location__org__burial__ugh=ugh) | \
                            Q(location__org__applicant_organization_burials__ugh=ugh) | \
                            Q(location__org__exhumationrequest__burial__ugh=ugh)

            location_qs =   Q(cemetery__ugh=ugh) | \
                            Q(org=ugh) | \
                            Q(baseperson__aliveperson__applied_burials__ugh=ugh) | \
                            Q(org__burial__ugh=ugh) | \
                            Q(org__applicant_organization_burials__ugh=ugh) | \
                            Q(org__exhumationrequest__burial__ugh=ugh)
            
            cemetery_qs =   Q(ugh=ugh)
            cemeterycoordinates_qs = Q(cemetery__ugh=ugh)
            area_qs =       Q(cemetery__ugh=ugh)
            areaphoto_qs =  Q(area__cemetery__ugh=ugh)
            areacoordinates_qs = Q(area__cemetery__ugh=ugh)
            placesize_qs =  Q(org=ugh)
            placephoto_qs = Q(place__cemetery__ugh=ugh)

            user_qs =       Q(profile__org=ugh) | \
                            Q(profile__loru_agent_burials__ugh=ugh) | \
                            Q(profile__agent_burials__ugh=ugh)
            profile_qs =    Q(org=ugh) | \
                            Q(loru_agent_burials__ugh=ugh) | \
                            Q(agent_burials__ugh=ugh)
            dover_qs =      Q(agent__loru_agent_burials__ugh=ugh) | \
                            Q(agent__agent_burials__ugh=ugh)

            currency_qs =   Q(org=ugh)
            reason_qs =     Q(org=ugh)

            org_qs =        Q(pk=ugh.pk) | \
                            Q(burial__ugh=ugh) | \
                            Q(applicant_organization_burials__ugh=ugh) | \
                            Q(exhumationrequest__burial__ugh=ugh)
            
            iddocumentsource_qs = Q(personid__person__aliveperson__applied_burials__ugh=ugh) | \
                                  Q(personid__person__aliveperson__place__cemetery__ugh=ugh) | \
                                  Q(personid__person__aliveperson__exhumationrequest__burial__ugh=ugh)
            aliveperson_qs = Q(applied_burials__ugh=ugh) | \
                             Q(place__cemetery__ugh=ugh) | \
                             Q(exhumationrequest__burial__ugh=ugh)
            personid_qs =   Q(person__aliveperson__applied_burials__ugh=ugh) | \
                            Q(person__aliveperson__place__cemetery__ugh=ugh) | \
                            Q(person__aliveperson__exhumationrequest__burial__ugh=ugh)
            place_qs =      Q(cemetery__ugh=ugh)
            grave_qs =      Q(place__cemetery__ugh=ugh)
            burial_qs =     Q(ugh=ugh)
            burialfiles_qs = Q(burial__ugh=ugh)
            exhumationrequest_qs = Q(burial__ugh=ugh)

            deadperson_qs = Q(burial__ugh=ugh)
            deathcertificate_qs = Q(person__burial__ugh=ugh)
            deathcertificatescan_qs = Q(deathcertificate__person__burial__ugh=ugh)

            for (title, serializer, queryset) in \
                    ( 
                        ('country', ArchCountrySerializer, country_qs),
                        ('region', ArchRegionSerializer, region_qs),
                        ('city', ArchCitySerializer, city_qs),
                        ('street', ArchStreetSerializer, street_qs),
                        ('location', ArchLocationSerializer, location_qs),

                        ('currency', ArchCurrencySerializer, currency_qs),
                        ('org', ArchOrgSerializer, org_qs),

                        ('user', ArchUserSerializer, user_qs),
                        ('profile', ArchProfileSerializer, profile_qs),
                        ('dover', ArchDoverSerializer, dover_qs),

                        ('cemetery', ArchCemeterySerializer, cemetery_qs),
                        ('cemeterycoordinates', ArchCemeteryCoordinatesSerializer, cemeterycoordinates_qs),
                        ('areapurpose', AreaPurposeSerializer, None),
                        ('area', ArchAreaSerializer, area_qs),
                        ('areaphoto', ArchAreaPhotoSerializer, areaphoto_qs),
                        ('areacoordinates', ArchAreaCoordinatesSerializer, areacoordinates_qs),
                        ('placesize', ArchPlaceSizeSerializer, placesize_qs),

                        ('iddocumenttype', ArchIDDocumentTypeSerializer, None),
                        ('iddocumentsource', ArchDocumentSourceSerializer, iddocumentsource_qs),
                        ('aliveperson', ArchAlivePersonSerializer, aliveperson_qs),
                        ('personid', ArchPersonIDSerializer, personid_qs),

                        ('place', ArchPlaceSerializer, place_qs),
                        ('placephoto', ArchPlacePhotoSerializer, placephoto_qs),
                        ('grave', ArchGraveSerializer, grave_qs),

                        ('deadperson', ArchDeadPersonSerializer, deadperson_qs),
                        ('deathcertificate', ArchDeathCertificateSerializer, deathcertificate_qs),
                        ('deathcertificatescan', ArchDeathCertificateScanSerializer, deathcertificatescan_qs),
                        ('burial', ArchBurialSerializer, burial_qs),
                        ('burialfiles', ArchBurialFilesSerializer, burialfiles_qs),
                        ('exhumationrequest', ArchExhumationRequestSerializer, exhumationrequest_qs),

                        ('reason', ArchReasonSerializer, reason_qs),
                    ):
                self.handle_model(title, serializer, queryset)

            self.f.write(u"</root>\n")
            self.f.close()
            fname = "%s.xml" % XML_NAME
            zip_name = os.path.join(folder, "%s.zip" % ZIP_NAME)
            with zipfile.ZipFile(zip_name, 'w') as zip_:
                zip_.write(self.f.name, arcname=fname)        
        finally:
            try:
                os.unlink(self.f.name)
            except (OSError, AttributeError,):
                pass

    # Главная функция
    #
    def handle_noargs(self, **options):
        
        try:
            os.mkdir(os.path.join(settings.MEDIA_ROOT, MEDIA_STORAGE))
        except OSError:
            pass
        for ugh in Org.objects.filter(type=Org.PROFILE_UGH):
            self.handle_ugh(ugh)
