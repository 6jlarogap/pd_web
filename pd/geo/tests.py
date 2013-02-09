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
            aolevel=1,
            aoguid='',
            citycode='',
            areacode='',
            ctarcode='',
            placecode='',
            streetcode='',
            extrcode='',
            sextcode='',
            formalname='',
            offname='',
            shortname='',
            parentguid='',
            enddate=datetime.date.today()
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

        f = LocationForm(instance=Location.objects.get())
        self.assertDictContainsSubset(data, f.initial)
