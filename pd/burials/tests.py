import datetime
from burials.forms import BurialCloseForm
from burials.models import Cemetery, Burial, Place, Area
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test.client import Client
from django.test.testcases import TestCase
from django.utils.translation import activate, get_language
from persons.models import DeadPerson, IDDocumentType
from users.models import Profile, ProfileLORU, Org, Dover


class RequestsTest(TestCase):
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
        self.area = Area.objects.create(cemetery=self.cemetery, name='rest')
        self.ugh_user.profile.org.loru_list.create(loru=loru_org)
        self.zags = Org.objects.create(name='ZAGS', type=Org.PROFILE_ZAGS)
        self.doc_type = IDDocumentType.objects.create(name='Passport')

    def test_lists(self):
        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

    def test_create(self):
        r = self.ugh_client.get('/burials/create/')
        self.assertEqual(r.status_code, 200)

        r = self.loru_client.get('/burials/create/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Burial.objects.all().count(), 0)

        r = self.loru_client.post('/burials/create/', {
            'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00',
            'opf': 'person', 'applicant-last_name': u'Petrov',
            'deadman-dc-zags': self.zags.pk, 'responsible-personid-number': '11', 'responsible-personid-series': '11',
            'responsible-personid-id_type': self.doc_type.pk,
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Burial.objects.all().count(), 1)

        br = Burial.objects.all()[0]
        self.assertEqual(br.status, Burial.STATUS_DRAFT)

    def test_created_lists(self):
        r = self.loru_client.post('/burials/create/', {
            'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00',
            'opf': 'person', 'applicant-last_name': u'Petrov',
            'deadman-dc-zags': self.zags.pk, 'responsible-personid-number': '11', 'responsible-personid-series': '11',
            'responsible-personid-id_type': self.doc_type.pk,
        })
        self.assertEqual(r.status_code, 302)
        br = Burial.objects.all()[0]
        br.status = Burial.STATUS_READY
        br.save()

        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

        ProfileLORU.objects.all().delete()

        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

    def test_actions(self):
        r = self.loru_client.post('/burials/create/', {
            'burial_type': 'common', 'opf': 'person', 'applicant-last_name': u'Petrov',
            'cemetery': self.cemetery.pk, 'area': self.area.pk,
            'plan_date': '12.12.2013', 'plan_time': '12:00',
        })
        self.assertEqual(r.status_code, 302)
        br = Burial.objects.all()[0]

        r = self.loru_client.get('/burials/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 0)
        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.post('/burials/%s/' % br.pk, {'ready': '1'}, follow=True)

        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 1)
        self.assertIn('loru', r.content)

        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.ugh_client.post('/burials/%s/' % br.pk, {'approve': '1'}, follow=True)

        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 1)
        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.loru_client.get('/burials/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.ugh_client.post('/burials/%s/' % br.pk, {
            'complete': '1',
            'close-cemetery': self.cemetery.pk, 'close-area': self.area.pk,
            'close-place_number': '123', 'close-fact_date': datetime.date.today().strftime('%d.%m.%Y'),
        }, follow=True)

        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 0)
        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.loru_client.get('/burials/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

    def test_back(self):
        r = self.loru_client.post('/burials/create/', {
            'burial_type': 'common', 'opf': 'person', 'applicant-last_name': u'Petrov',
            'cemetery': self.cemetery.pk, 'area': self.area.pk,
            'plan_date': '12.12.2013', 'plan_time': '12:00',
        })
        br = Burial.objects.all()[0]

        r = self.loru_client.post('/burials/%s/' % br.pk, {'ready': '1'}, follow=True)
        r = self.ugh_client.post('/burials/%s/' % br.pk, {'approve': '1'}, follow=True)

        br = Burial.objects.all()[0]
        self.assertEqual(br.status, Burial.STATUS_APPROVED)

        r = self.loru_client.post('/burials/%s/' % br.pk, {'back': '1'})

        br = Burial.objects.all()[0]
        self.assertEqual(br.status, Burial.STATUS_BACKED)

        r = self.loru_client.post('/burials/%s/' % br.pk, {'ready': '1'}, follow=True)
        r = self.ugh_client.post('/burials/%s/' % br.pk, {'approve': '1'}, follow=True)
        r = self.ugh_client.post('/burials/%s/' % br.pk, {
            'complete': '1',
            'close-cemetery': self.cemetery.pk, 'close-area': self.area.pk,
            'close-place_number': '123', 'close-fact_date': datetime.date.today().strftime('%d.%m.%Y'),
        }, follow=True)

        br = Burial.objects.all()[0]
        self.assertEqual(br.status, Burial.STATUS_CLOSED)

    def test_archive(self):
        r = self.loru_client.post('/burials/create/', {
            'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00',
            'opf': 'person', 'applicant-last_name': u'Petrov',
            'deadman-dc-zags': self.zags.pk, 'responsible-personid-number': '11', 'responsible-personid-series': '11',
            'responsible-personid-id_type': self.doc_type.pk,
        })
        self.assertEqual(r.status_code, 302)
        br = Burial.objects.all()[0]
        self.assertEqual(br.status, Burial.STATUS_DRAFT)

        r = self.ugh_client.get('/burials/archive/')
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.get('/burials/archive/')
        self.assertEqual(r.context['burials'].count(), 1)

        self.ugh_user.profile.org.loru_list.all().delete()

        r = self.ugh_client.get('/burials/archive/')
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.get('/burials/archive/')
        self.assertEqual(r.context['burials'].count(), 1)

    def test_edit(self):
        r = self.loru_client.post('/burials/create/', {
            'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00',
            'opf': 'person', 'applicant-last_name': u'Petrov',
            'deadman-dc-zags': self.zags.pk, 'responsible-personid-number': '11', 'responsible-personid-series': '11',
            'responsible-personid-id_type': self.doc_type.pk,
        })
        self.assertEqual(r.status_code, 302)

        br = Burial.objects.all()[0]
        self.assertEqual(br.loru, self.loru_user.profile.org)
        self.assertEqual(br.cemetery, self.cemetery)
        self.assertEqual(br.cemetery.ugh, self.ugh_user.profile.org)
        self.assertEqual(br.is_edit(), True)

        r = self.loru_client.get('/burials/edit/%s/' % br.pk)
        self.assertEqual(r.status_code, 200)

        r = self.ugh_client.get('/burials/edit/%s/' % br.pk)
        self.assertEqual(r.status_code, 404)

    def test_edit_loru(self):
        r = self.loru_client.post('/burials/create/', {
            'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00',
            'opf': 'person', 'applicant-last_name': u'Petrov',
            'deadman-dc-zags': self.zags.pk, 'responsible-personid-number': '11', 'responsible-personid-series': '11',
            'responsible-personid-id_type': self.doc_type.pk,
            })
        self.assertEqual(r.status_code, 302)
        br = Burial.objects.all()[0]

        self.assertEqual(br.loru, self.loru_user.profile.org)

        r = self.loru_client.get('/burials/edit/%s/' % br.pk)
        self.assertEqual(r.status_code, 200)

class BurialsTest(TestCase):
    def setUp(self):
        activate('ru')
        self.client = Client()
        self.ugh_client = Client()

        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        ugh_org = Org.objects.create(type=Org.PROFILE_UGH, name='ugh')
        Profile.objects.create(user=self.ugh_user, org=ugh_org)
        self.ugh_client.login(username='ugh', password='test')

        self.cemetery = Cemetery.objects.create(name='test cem', time_begin='12:00', time_end='17:00', ugh=ugh_org)
        self.zags = Org.objects.create(name='ZAGS', type=Org.PROFILE_ZAGS)
        self.doc_type = IDDocumentType.objects.create(name='Passport')

    def test_search(self):
        r = self.ugh_client.get('/burials/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

        Burial.objects.create(
            burial_type=Burial.BURIAL_TYPES[0][0],
            cemetery=self.cemetery,
            ugh=self.cemetery.ugh,
            area=None,
            row=None,
            place=None,
            responsible=None,
            fact_date=datetime.date.today(),
            status=Burial.STATUS_CLOSED,
            deadman=DeadPerson.objects.create(
                last_name=u'Ivanov',
            )
        )

        r = self.ugh_client.get('/burials/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.ugh_client.get('/burials/?fio=Petrov')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.ugh_client.get('/burials/?fio=Ivanov')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.ugh_client.get('/burials/?fio=Ivanov Ivan')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

    def test_hierarchy(self):
        loru = Org.objects.create(name='loru', type=Org.PROFILE_LORU)
        ProfileLORU.objects.create(loru=loru, ugh=self.ugh_user.profile.org)
        agent = Profile.objects.create(org=loru, is_agent=True)
        dover = Dover.objects.create(agent=agent, number=1, begin='2010-10-10', end='2020-10-10')

        r = self.ugh_client.post('/burials/create/', {
            'plan_date': '12.12.2013', 'opf': 'org',
            'dover': dover.pk,
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['form'].is_valid(), False)

        r = self.ugh_client.post('/burials/create/', {
            'plan_date': '12.12.2013', 'opf': 'org',
            'agent': agent.pk, 'dover': dover.pk,
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['form'].is_valid(), False)

        r = self.ugh_client.post('/burials/create/', {
            'plan_date': '12.12.2013', 'opf': 'org',
            'loru': loru.pk, 'agent': agent.pk, 'dover': dover.pk,
        })
        self.assertEqual(r.status_code, 302)

    def test_paginate(self):
        r = self.ugh_client.get('/burials/')

        params = dict(
            burial_type=Burial.BURIAL_TYPES[0][0],
            cemetery=self.cemetery,
            ugh=self.cemetery.ugh,
            area=None,
            row=None,
            place=None,
            responsible=None,
            fact_date=datetime.date.today(),
            status=Burial.STATUS_CLOSED,
            deadman=DeadPerson.objects.create(
                last_name=u'Ivanov',
            )
        )

        for i in range(30):
            Burial.objects.create(**params)

        r = self.ugh_client.get('/burials/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 20)

        r = self.ugh_client.get('/burials/?page=2')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 10)

        r = self.ugh_client.get('/burials/?page=3')
        self.assertEqual(r.status_code, 404)

    def test_place(self):
        r = self.client.get('/places/000/')
        self.assertEqual(r.status_code, 404)

        place = Place.objects.create(
            cemetery=self.cemetery,
            area=None,
            row=None,
            place=None,
            responsible=None,
        )

        r = self.client.get('/places/%s/' % place.pk)
        self.assertEqual(r.status_code, 200)

    def test_create(self):
        r = self.client.get('/burials/create/')
        self.assertEqual(r.status_code, 302)

        r = self.ugh_client.get('/burials/create/')
        self.assertEqual(r.status_code, 200)

        self.assertEquals(Burial.objects.all().count(), 0)

        r = self.ugh_client.post('/burials/create/', {
            'burial_type': Burial.BURIAL_TYPES[0][0],
            'fact_date': datetime.date.today().strftime('%d.%m.%Y'),
            'cemetery': self.cemetery.pk,
            'opf': 'person',
            'place_number': 123,
            'deadman-last_name': u'Ivanov',
            'deadman-dc-zags': self.zags.pk,
            'responsible-last_name': u'Petrov',
            'applicant-last_name': u'Petrov',
            'applicant-pid-id_type': self.doc_type.pk,
            'applicant-pid-series': '11111',
            'applicant-pid-number': '222',
        })
        self.assertEqual(r.status_code, 302)

        self.assertEquals(Burial.objects.all().count(), 1)

        br = Burial.objects.get()

        self.assertEqual(br.status, Burial.STATUS_DRAFT)
        self.assertEqual(br.source_type, Burial.SOURCE_UGH)
        self.assertEqual(br.ugh, self.ugh_user.profile.org)

        r = self.client.get('/burials/%s/' % br.pk)
        self.assertEqual(r.status_code, 404)

        r = self.ugh_client.get('/burials/%s/' % br.pk)
        self.assertEqual(r.status_code, 200)

class TestArchived(TestCase):
    def setUp(self):
        activate('ru')
        self.client = Client()
        self.ugh_client = Client()

        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        ugh_org = Org.objects.create(type=Org.PROFILE_UGH, name='ugh')
        Profile.objects.create(user=self.ugh_user, org=ugh_org)
        self.ugh_client.login(username='ugh', password='test')

        self.cemetery = Cemetery.objects.create(name='test cem', time_begin='12:00', time_end='17:00', ugh=ugh_org)
        self.zags = Org.objects.create(name='ZAGS', type=Org.PROFILE_ZAGS)
        self.doc_type = IDDocumentType.objects.create(name='Passport')

    def test_create(self):
        r = self.ugh_client.get('/burials/create/?archive=1')
        self.assertEqual(r.status_code, 200)

        self.assertEquals(Burial.objects.all().count(), 0)

        r = self.ugh_client.post('/burials/create/?archive=1', {
            'burial_type': Burial.BURIAL_TYPES[0][0],
            'fact_date': datetime.date.today().strftime('%d.%m.%Y'),
            'cemetery': self.cemetery.pk,
            'opf': 'person',
            'applicant-last_name': u'Petrov',
            'place_number': 123,
            'deadman-last_name': u'Ivanov',
            'deadman-dc-zags': self.zags.pk,
        })
        self.assertEqual(r.status_code, 302)

        self.assertEquals(Burial.objects.all().count(), 1)

        br = Burial.objects.get()

        self.assertEqual(br.status, Burial.STATUS_DRAFT)
        self.assertEqual(br.source_type, Burial.SOURCE_ARCHIVE)
        self.assertEqual(br.ugh, self.ugh_user.profile.org)

        r = self.client.get('/burials/%s/' % br.pk)
        self.assertEqual(r.status_code, 404)

        r = self.ugh_client.get('/burials/%s/' % br.pk)
        self.assertEqual(r.status_code, 200)

class TestForms(TestCase):
    def setUp(self):
        activate('ru')
        self.client = Client()
        self.ugh_client = Client()

        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        ugh_org = Org.objects.create(type=Org.PROFILE_UGH, name='ugh')
        Profile.objects.create(user=self.ugh_user, org=ugh_org)
        self.ugh_client.login(username='ugh', password='test')

    def test_children(self):
        request = HttpRequest()
        request.user = self.ugh_user
        f = BurialCloseForm(request)
        self.assertEqual(f.cemetery_areas_json(), "{}")
        self.assertEqual(f.agent_dover_json(), "{}")
        self.assertEqual(f.loru_agents_json(), "{}")
