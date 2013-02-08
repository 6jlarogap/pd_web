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


class DeadManTest(TestCase):
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
        self.zags = Org.objects.create(name='ZAGS', type=Org.PROFILE_ZAGS)

    def test_add(self):
        r = self.ugh_client.get('/create_deadman/%s/' % self.br.pk)
        self.assertEqual(r.status_code, 302)

        r = self.loru_client.get('/create_deadman/%s/' % self.br.pk)
        self.assertEqual(r.status_code, 200)

        self.br = Burial.objects.get()
        self.assertEqual(self.br.deadman, None)

        r = self.loru_client.post('/create_deadman/%s/' % self.br.pk, {
            'last_name': u'Иванов',
            'first_name': u'Иван',
            'birth_date': u'01.01.1960',
            'death_date': u'01.01.2013',
            'addr-country': self.country.pk,
            'addr-region': self.region.pk,
            'addr-city': self.city.pk,
            'addr-street': self.street.pk,
            'addr-house': '123',
            'dc-s_number': '1111',
            'dc-zags': self.zags.pk,
        })
        self.assertEqual(r.status_code, 302)

        self.br = Burial.objects.get()
        self.assertEqual(self.br.deadman.last_name, u'Иванов')
        self.assertEqual(self.br.deadman.death_date, datetime.date(2013, 1, 1))
        self.assertEqual(self.br.deadman.address.street, self.street)
        self.assertEqual(self.br.deadman.address.house, '123')
        self.assertEqual(self.br.deadman.address.street, self.street)
        self.assertEqual(self.br.deadman.deathcertificate.s_number, '1111')
        self.assertEqual(self.br.deadman.deathcertificate.zags, self.zags)

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

    def test_add(self):
        r = self.ugh_client.get('/create_responsible/%s/' % self.br.pk)
        self.assertEqual(r.status_code, 302)

        r = self.loru_client.get('/create_responsible/%s/' % self.br.pk)
        self.assertEqual(r.status_code, 200)

        self.br = Burial.objects.get()
        self.assertEqual(self.br.responsible, None)

        r = self.loru_client.post('/create_responsible/%s/' % self.br.pk, {
            'last_name': u'Иванов',
            'first_name': u'Иван',
            'birth_date': u'01.01.1960',
            'addr-country': self.country.pk,
            'addr-region': self.region.pk,
            'addr-city': self.city.pk,
            'addr-street': self.street.pk,
            'addr-house': '123',
            'id-id_type': self.doc_type.pk,
            'id-series': '11111',
            'id-number': '1111',
            })
        self.assertEqual(r.status_code, 302)

        self.br = Burial.objects.get()
        self.assertEqual(self.br.responsible.last_name, u'Иванов')
        self.assertEqual(self.br.responsible.address.street, self.street)
        self.assertEqual(self.br.responsible.address.house, '123')
        self.assertEqual(self.br.responsible.address.street, self.street)
        self.assertEqual(self.br.responsible.personid.number, '1111')
        self.assertEqual(self.br.responsible.personid.series, '11111')
        self.assertEqual(self.br.responsible.personid.id_type, self.doc_type)

        self.assertEqual(self.br.responsible, self.br.get_responsible())

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



