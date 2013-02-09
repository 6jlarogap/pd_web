# coding=utf-8
import datetime
from django.test import TestCase

from geo.forms import LocationForm
from geo.models import Location, DFiasAddrobj, LocationFIAS


class TestLocationForm(TestCase):
    def test_basic(self):
        data = {
            'country_name': u'Россия',
            'region_name': u'Санкт-Петербург',
            'city_name': u'Санкт-Петербург',
        }

        f = LocationForm(data=data)

        self.assertEqual(f.is_valid(), True)
        self.assertEqual(Location.objects.all().count(), 0)

        f.save()

        self.assertEqual(Location.objects.all().count(), 1)

        f = LocationForm(instance=Location.objects.get())
        self.assertDictContainsSubset(data, f.initial)

    def test_fias(self):
        fias_data = dict(
            aoid='',
            formalname='',
            regioncode='',
            autocode='',
            areacode='',
            citycode='',
            ctarcode='',
            placecode='',
            streetcode='',
            extrcode='',
            sextcode='',
            offname='',
            postalcode='',
            ifnsfl='',
            terrifnsfl='',
            ifnsul='',
            terrifnsul='',
            okato='',
            oktmo='',
            updatedate=datetime.date.today(),
            shortname='',
            aolevel='',
            parentguid='',
            aoguid='',
            previd='',
            nextid='',
            code='',
            plaincode='',
            actstatus=1,
            centstatus=1,
            operstatus=1,
            currstatus=1,
            startdate=datetime.date.today(),
            enddate=datetime.date.today(),
            normdoc='',
        )
        fias_data.update(aolevel=1, aoguid='c2deb16a-0330-4f05-821f-1d09c93331e6', offname=u'СПб', shortname=u'г')
        DFiasAddrobj.objects.using('fias').create(**fias_data)
        fias_data.update(aolevel=2, parentguid='c2deb16a-0330-4f05-821f-1d09c93331e6',
                         aoguid='5fa7d375-2cb8-4d30-9028-835938d6dca8', offname=u'Греческая', shortname=u'пл')
        DFiasAddrobj.objects.using('fias').create(**fias_data)

        data = {
            'country_name': u'Россия',
            'fias_1': u'c2deb16a-0330-4f05-821f-1d09c93331e6',
            'fias_2': u'5fa7d375-2cb8-4d30-9028-835938d6dca8',
        }
        f = LocationForm(data=data)

        self.assertEqual(f.is_valid(), True)
        self.assertEqual(Location.objects.all().count(), 0)
        self.assertEqual(LocationFIAS.objects.all().count(), 0)

        f.save()

        self.assertEqual(Location.objects.all().count(), 1)
        self.assertEqual(LocationFIAS.objects.all().count(), 2)

        data.update(
            fias_1=DFiasAddrobj.objects.using('fias').get(pk=data['fias_1']),
            fias_2=DFiasAddrobj.objects.using('fias').get(pk=data['fias_2']),
        )

        f = LocationForm(instance=Location.objects.get())
        self.assertDictContainsSubset(data, f.initial)
