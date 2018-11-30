# coding=utf-8
import datetime

from django.contrib.auth.models import User
from django.test.client import Client
from django.test.testcases import TestCase
from django.utils.translation import activate, get_language

from burials.models import Cemetery, Burial, Place
from geo.models import Country, Region, City, Street
from persons.models import IDDocumentType, AlivePerson
from users.models import Profile, ProfileLORU, Org


class ResponsibleTest(TestCase):
    def setUp(self):
        activate('ru')
        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        ugh_org = Org.objects.create(
            type=Org.PROFILE_UGH, name='ugh'
        )
        Profile.objects.create(
            user=self.ugh_user, org=ugh_org,
            )
        self.loru_user = User.objects.create_user(username='loru', email='test@example.com', password='test')
        loru_org = Org.objects.create(
            type=Org.PROFILE_LORU, name='loru'
        )
        Profile.objects.create(
            user=self.loru_user, org=loru_org,
        )
        self.ugh_client = Client()
        self.ugh_client.login(username='ugh', password='test')
        self.loru_client = Client()
        self.loru_client.login(username='loru', password='test')
        self.cemetery = Cemetery.objects.create(name='test cem', time_begin='12:00', time_end='17:00', ugh=ugh_org)
        self.ugh_user.profile.org.loru_list.create(loru=loru_org)
        self.br = Burial.objects.create(cemetery=self.cemetery)
        self.country = Country.objects.create(name='Russia')
        self.region = Region.objects.create(name='Lenoblast', country=self.country)
        self.city = City.objects.create(name='SPb', region=self.region)
        self.street = Street.objects.create(name='Stachek', city=self.city)
        self.doc_type = IDDocumentType.objects.create(name='Passport')

    def test_place(self):
        self.br = Burial.objects.get()
        self.assertEqual(self.br.get_place(), None)
        self.assertEqual(self.br.get_responsible(), None)

        self.responsible = AlivePerson.objects.create(last_name=u'Иванов', first_name=u'Иван')
        self.place = Place.objects.create(cemetery=self.cemetery, place='123', responsible=self.responsible)
        self.assertEqual(self.br.get_place(), None)
        self.assertEqual(self.br.get_responsible(), None)

        self.br.place_number = '123'
        self.br.save()
        self.assertEqual(self.br.get_place(), self.place)
        self.assertEqual(self.br.get_responsible(), self.responsible)



