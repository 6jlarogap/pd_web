# coding=utf-8
import datetime
from burials.models import Cemetery, BurialRequest
from django.contrib.auth.models import User
from django.test.client import Client
from django.test.testcases import TestCase
from django.utils.translation import activate, get_language
from geo.models import Country, Region, City, Street
from persons.models import ZAGS
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
        self.br = BurialRequest.objects.create(cemetery=self.cemetery)
        self.country = Country.objects.create(name='Russia')
        self.region = Region.objects.create(name='Lenoblast', country=self.country)
        self.city = City.objects.create(name='SPb', region=self.region)
        self.street = Street.objects.create(name='Stachek', city=self.city)
        self.zags = ZAGS.objects.create(name='ZAGS')

    def test_add(self):
        r = self.ugh_client.get('/create_deadman/%s/' % self.br.pk)
        self.assertEqual(r.status_code, 302)

        r = self.loru_client.get('/create_deadman/%s/' % self.br.pk)
        self.assertEqual(r.status_code, 200)

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

        self.br = BurialRequest.objects.get()
        self.assertEqual(self.br.deadman.last_name, u'Иванов')
        self.assertEqual(self.br.deadman.death_date, datetime.date(2013, 1, 1))
        self.assertEqual(self.br.deadman.address.street, self.street)
        self.assertEqual(self.br.deadman.address.house, '123')
        self.assertEqual(self.br.deadman.address.street, self.street)
        self.assertEqual(self.br.deadman.deathcertificate.s_number, '1111')
        self.assertEqual(self.br.deadman.deathcertificate.zags, self.zags)




