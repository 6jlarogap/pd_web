from django.conf import settings
from django.test import TestCase

from geo.forms import LocationForm
from geo.models import Location, DFiasAddrobj, LocationFIAS


class TestLocationForm(TestCase):
    def test_basic(self):
        data = {
            'country_name': 'Россия',
            'region_name': 'Санкт-Петербург',
            'city_name': 'Санкт-Петербург',
        }

        f = LocationForm(data=data)

        self.assertEqual(f.is_valid(), True)
        self.assertEqual(Location.objects.all().count(), 0)

        f.save()

        self.assertEqual(Location.objects.all().count(), 1)

        f = LocationForm(instance=Location.objects.get())
        self.assertDictContainsSubset(data, f.initial)

    def test_autocomplete_fias(self):
        settings.DATABASES['fias'] = settings.TEST_FIAS

        lenin = DFiasAddrobj.objects.get_streets(
            country='Россия',
            region='Санкт-Петербург',
            city='Санкт-Петербург',
            street='улица Ленина',
        )

        self.assertEqual(lenin.count(), 1)
        self.assertEqual(lenin[0].aoguid, '1faa3b1e-8558-42b0-9956-154daafe999f')

        svoboda = DFiasAddrobj.objects.get_streets(
            country='Россия',
            region='Краснодарский край',
            city='Новороссийск',
            street='улица Свободы',
        )

        self.assertEqual(svoboda.count(), 1)
        self.assertEqual(svoboda[0].aoguid, '4a2d152d-0693-441f-9835-d235f41afb83')
