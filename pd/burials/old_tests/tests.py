import datetime
import json
from burials.forms import BurialApproveCloseForm
from burials.models import Cemetery, Burial, Place, Area, ExhumationRequest
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test.client import Client
from django.test.testcases import TestCase
from django.utils.translation import activate, get_language
from logs.models import Log
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
        r = self.ugh_client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.loru_client.get('/order/dashboard/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['object_list'].count(), 0)

    def test_create(self):
        r = self.ugh_client.get('/burials/create/')
        self.assertEqual(r.status_code, 200)

        r = self.loru_client.get('/burials/create/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Burial.objects.all().count(), 0)

        r = self.loru_client.post('/burials/create/', {
            'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00',
            'opf': 'person', 'applicant-last_name': 'Petrov', 'places_type': 'manual', 'grave_number': 1,
            'deadman-dc-zags': self.zags.pk, 'responsible-personid-number': '11', 'responsible-personid-series': '11',
            'responsible-personid-id_type': self.doc_type.pk, 'responsible-take_from': 'new',
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Burial.objects.all().count(), 1)

        br = Burial.objects.all()[0]
        self.assertEqual(br.status, Burial.STATUS_DRAFT)

    def test_created_lists(self):
        r = self.loru_client.post('/burials/create/', {
            'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00',
            'opf': 'person', 'applicant-last_name': 'Petrov', 'places_type': 'manual', 'grave_number': 1,
            'deadman-dc-zags': self.zags.pk, 'responsible-personid-number': '11', 'responsible-personid-series': '11',
            'responsible-personid-id_type': self.doc_type.pk, 'responsible-take_from': 'new',
        })
        self.assertEqual(r.status_code, 302)
        br = Burial.objects.all()[0]
        br.status = Burial.STATUS_READY
        br.save()

        r = self.ugh_client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.get('/order/dashboard/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['object_list'].count(), 0)

        ProfileLORU.objects.all().delete()

        r = self.ugh_client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

    def test_actions(self):
        r = self.loru_client.post('/burials/create/', {
            'coffin_type': 'coffin', 'opf': 'person', 'applicant-last_name': 'Petrov',
            'cemetery': self.cemetery.pk, 'area': self.area.pk, 'places_type': 'manual',
            'plan_date': '12.12.2013', 'plan_time': '12:00', 'grave_number': 1, 'responsible-take_from': 'new',
        })
        self.assertEqual(r.status_code, 302)
        br = Burial.objects.get()

        r = self.loru_client.get('/burials/?test=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.ugh_client.get('/')
        self.assertEqual(r.context['burials'].count(), 1)
        r = self.loru_client.get('/order/dashboard/')
        self.assertEqual(r.context['object_list'].count(), 0)

        r = self.loru_client.post('/burials/%s/' % br.pk, {'ready': '1'}, follow=True)

        r = self.ugh_client.get('/')
        self.assertEqual(r.context['burials'].count(), 1)
        self.assertIn('loru', r.content)

        r = self.loru_client.get('/order/dashboard/')
        self.assertEqual(r.context['object_list'].count(), 0)

        r = self.ugh_client.post('/burials/%s/' % br.pk, {'approve': '1'}, follow=True)

        r = self.ugh_client.get('/')
        self.assertEqual(r.context['burials'].count(), 1)
        r = self.loru_client.get('/order/dashboard/')
        self.assertEqual(r.context['object_list'].count(), 0)

        r = self.loru_client.get('/burials/?test=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.ugh_client.post('/burials/%s/' % br.pk, {
            'complete': '1',
            'cemetery': self.cemetery.pk, 'area': self.area.pk,
            'place_number': '123', 'fact_date_day': 10, 'fact_date_month': 10, 'fact_date_year': 2010,
        }, follow=True)

        r = self.ugh_client.get('/')
        self.assertEqual(r.context['burials'].count(), 0)
        r = self.loru_client.get('/order/dashboard/')
        self.assertEqual(r.context['object_list'].count(), 0)

        r = self.loru_client.get('/burials/?test=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

    def test_back(self):
        r = self.loru_client.post('/burials/create/', {
            'coffin_type': 'coffin', 'opf': 'person', 'applicant-last_name': 'Petrov',
            'cemetery': self.cemetery.pk, 'area': self.area.pk, 'places_type': 'manual',
            'plan_date': '12.12.2013', 'plan_time': '12:00', 'grave_number': 1, 'responsible-take_from': 'new',
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
            'cemetery': self.cemetery.pk, 'area': self.area.pk,
            'place_number': '123', 'fact_date_day': 10, 'fact_date_month': 10, 'fact_date_year': 2010,
        }, follow=True)

        br = Burial.objects.all()[0]
        self.assertEqual(br.status, Burial.STATUS_CLOSED)
        self.assertIsNotNone(br.place)
        self.assertIsNotNone(br.get_place())

    def test_archive(self):
        r = self.loru_client.post('/burials/create/', {
            'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00',
            'opf': 'person', 'applicant-last_name': 'Petrov', 'places_type': 'manual', 'grave_number': 1,
            'deadman-dc-zags': self.zags.pk, 'responsible-personid-number': '11', 'responsible-personid-series': '11',
            'responsible-personid-id_type': self.doc_type.pk, 'responsible-take_from': 'new',
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
            'opf': 'person', 'applicant-last_name': 'Petrov', 'places_type': 'manual', 'grave_number': 1,
            'deadman-dc-zags': self.zags.pk, 'responsible-personid-number': '11', 'responsible-personid-series': '11',
            'responsible-personid-id_type': self.doc_type.pk, 'responsible-take_from': 'new',
        })
        self.assertEqual(r.status_code, 302)

        br = Burial.objects.all()[0]
        self.assertEqual(br.applicant_organization, self.loru_user.profile.org)
        self.assertEqual(br.cemetery, self.cemetery)
        self.assertEqual(br.cemetery.ugh, self.ugh_user.profile.org)
        self.assertEqual(br.is_edit(), True)

        r = self.loru_client.get('/burials/%s/edit/' % br.pk)
        self.assertEqual(r.status_code, 200)

        r = self.ugh_client.get('/burials/%s/edit/' % br.pk)
        self.assertEqual(r.status_code, 404)

    def test_edit_loru(self):
        r = self.loru_client.post('/burials/create/', {
            'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00',
            'opf': 'person', 'applicant-last_name': 'Petrov', 'places_type': 'manual', 'grave_number': 1,
            'deadman-dc-zags': self.zags.pk, 'responsible-personid-number': '11', 'responsible-personid-series': '11',
            'responsible-personid-id_type': self.doc_type.pk, 'responsible-take_from': 'new',
        })
        self.assertEqual(r.status_code, 302)
        br = Burial.objects.all()[0]

        self.assertEqual(br.applicant_organization, self.loru_user.profile.org)

        r = self.loru_client.get('/burials/%s/edit/' % br.pk)
        self.assertEqual(r.status_code, 200)

    def test_comment(self):
        r = self.loru_client.post('/burials/create/', {
            'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'grave_number': 1,  'responsible-take_from': 'new',
        })
        self.assertEqual(r.status_code, 302)
        br = Burial.objects.all()[0]
        self.assertEqual(Log.objects.all().count(), 1)

        r = self.loru_client.post('/burials/%s/comment/' % br.pk, {'comment': 'test'})
        self.assertEqual(r.status_code, 302)

        self.assertEqual(Log.objects.all().count(), 2)
        self.assertTrue('test' in Log.objects.get(pk=2).msg)

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
        r = self.ugh_client.get('/burials/?test=1')
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
                last_name='Ivanov',
            )
        )

        r = self.ugh_client.get('/burials/?test=1')
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
            'plan_date': '12.12.2013', 'opf': 'org', 'places_type': 'manual',
            'dover': dover.pk, 'grave_number': 1, 'responsible-take_from': 'new',
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['form'].is_valid(), False)

        r = self.ugh_client.post('/burials/create/', {
            'plan_date': '12.12.2013', 'opf': 'org', 'places_type': 'manual',
            'agent': agent.pk, 'dover': dover.pk, 'grave_number': 1, 'responsible-take_from': 'new',
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['form'].is_valid(), False)

        r = self.ugh_client.post('/burials/create/', {
            'plan_date': '12.12.2013', 'opf': 'org', 'places_type': 'manual', 'grave_number': 1,
            'applicant_organization': loru.pk, 'agent': agent.pk, 'dover': dover.pk, 'responsible-take_from': 'new',
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
                last_name='Ivanov',
            )
        )

        for i in range(30):
            Burial.objects.create(**params)

        r = self.ugh_client.get('/burials/?test=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 25)

        r = self.ugh_client.get('/burials/?page=2')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 5)

        r = self.ugh_client.get('/burials/?page=3')
        self.assertEqual(r.status_code, 404)

        r = self.ugh_client.get('/burials/?per_page=10')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 10)

        r = self.ugh_client.get('/burials/?per_page=10&page=2')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 10)

        r = self.ugh_client.get('/burials/?per_page=10&page=3')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 10)

        r = self.ugh_client.get('/burials/?per_page=10&page=4')
        self.assertEqual(r.status_code, 404)

    def test_place(self):
        r = self.ugh_client.get('/places/000/')
        self.assertEqual(r.status_code, 404)

        place = Place.objects.create(
            cemetery=self.cemetery,
            area=None,
            row=None,
            place=None,
            responsible=None,
        )

        r = self.ugh_client.get('/places/%s/' % place.pk)
        self.assertEqual(r.status_code, 200)

    def test_create(self):
        r = self.client.get('/burials/create/')
        self.assertEqual(r.status_code, 302)

        r = self.ugh_client.get('/burials/create/')
        self.assertEqual(r.status_code, 200)

        self.assertEqual(Burial.objects.all().count(), 0)

        r = self.ugh_client.post('/burials/create/', {
            'coffin_type': 'coffin',
            'fact_date_day': 10, 'fact_date_month': 10, 'fact_date_year': 2010,
            'cemetery': self.cemetery.pk,
            'grave_number': 1,
            'opf': 'person',
            'places_type': 'manual',
            'place_number': 123,
            'deadman-last_name': 'Ivanov',
            'deadman-dc-zags': self.zags.pk,
            'responsible-take_from': 'new',
            'responsible-last_name': 'Petrov',
            'applicant-last_name': 'Petrov',
            'applicant-pid-id_type': self.doc_type.pk,
            'applicant-pid-series': '11111',
            'applicant-pid-number': '222',
        })
        self.assertEqual(r.status_code, 302)

        self.assertEqual(Burial.objects.all().count(), 1)

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

        self.assertEqual(Burial.objects.all().count(), 0)

        r = self.ugh_client.post('/burials/create/?archive=1', {
            'coffin_type': 'coffin',
            'fact_date_day': 10, 'fact_date_month': 10, 'fact_date_year': 2010,
            'cemetery': self.cemetery.pk,
            'grave_number': 1,
            'opf': 'person',
            'places_type': 'manual',
            'responsible-take_from': 'new',
            'applicant-last_name': 'Petrov',
            'place_number': 123,
            'deadman-last_name': 'Ivanov',
            'deadman-dc-zags': self.zags.pk,
        })
        self.assertEqual(r.status_code, 302)

        self.assertEqual(Burial.objects.all().count(), 1)

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
        f = BurialApproveCloseForm(request)
        self.assertEqual(f.cemetery_areas_json(), "{}")
        self.assertEqual(f.agent_dover_json(), "{}")
        self.assertEqual(f.loru_agents_json(), "{}")

class TestAJAX(TestCase):
    def setUp(self):
        activate('ru')
        self.client = Client()
        self.ugh_client = Client()

        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        self.ugh_org = Org.objects.create(type=Org.PROFILE_UGH, name='ugh')
        Profile.objects.create(user=self.ugh_user, org=self.ugh_org)
        self.ugh_client.login(username='ugh', password='test')

        self.cemetery = Cemetery.objects.create(name='test cem', time_begin='12:00', time_end='17:00', ugh=self.ugh_org,
                                                time_slots='10:20\n10:40\n11:00')

    def test_cemetery_times(self):
        params = (self.cemetery.pk, datetime.date.today().strftime('%d.%m.%Y'))
        r = self.client.get('/cemetery_times/?cem=%s&date=%s' % params)
        self.assertEqual(r.status_code, 302)

        r = self.ugh_client.get('/cemetery_times/?cem=%s&date=%s' % params)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(json.loads(r.content)), 1)

    def test_add_agent(self):
        loru = Org.objects.create(type=Org.PROFILE_LORU, name='loru')
        data = {
            'agent-username': 'test',
            'agent-email': 'test@example.com',
            'agent-first_name': 'test',
            'agent-last_name': 'testov',
            'agent_dover-number': '123',
            'agent_dover-begin': '10.10.2010',
            'agent_dover-end': '20.02.2020',
        }
        self.assertEqual(Profile.objects.filter(is_agent=True).count(), 0)
        self.assertEqual(Dover.objects.all().count(), 0)

        r = self.ugh_client.post('/burials/add_agent/?loru=%s' % loru.pk, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(json.loads(r.content)['pk'], 2)
        self.assertEqual(json.loads(r.content)['dover_pk'], 1)
        self.assertEqual(Profile.objects.filter(is_agent=True).count(), 1)
        self.assertEqual(Dover.objects.all().count(), 1)
        self.assertEqual(Dover.objects.get().agent, Profile.objects.get(is_agent=True))

    def test_add_dover(self):
        agent = Profile.objects.create(org=self.ugh_org, is_agent=True)
        data = {
            'dover-number': '123',
            'dover-begin': '10.10.2010',
            'dover-end': '20.02.2020',
        }
        self.assertEqual(Dover.objects.all().count(), 0)

        r = self.ugh_client.post('/burials/add_dover/?agent=%s' % agent.pk, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(json.loads(r.content)['pk'], 1)
        self.assertEqual(Dover.objects.all().count(), 1)

    def test_add_doctype(self):
        data = {
            'doctype-name': 'Passport',
        }
        self.assertEqual(IDDocumentType.objects.all().count(), 0)

        r = self.ugh_client.post('/burials/add_doctype/', data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(json.loads(r.content)['pk'], 1)
        self.assertEqual(IDDocumentType.objects.all().count(), 1)

    def test_add_loru(self):
        data = {
            'loru-name': '123',
            'loru-full_name': '10.10.2010',
            'loru-inn': '123456789',
            'loru-director': 'Petrov',
        }
        self.assertEqual(Org.objects.all().count(), 1)

        r = self.ugh_client.post('/burials/add_org/', data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(json.loads(r.content)['pk'], 2)
        self.assertEqual(Org.objects.all().count(), 2)

    def test_place_info(self):
        params = (self.cemetery.pk, '', '123', )
        r = self.ugh_client.get('/burials/get_place/?cemetery=%s&area=%s&row=&place_number=%s' % params)
        self.assertEqual(r.content, '')

        area = Area.objects.create(cemetery=self.cemetery, name='area')
        params = (self.cemetery.pk, area.pk, '123', )

        r = self.ugh_client.get('/burials/get_place/?cemetery=%s&area=%s&row=&place_number=%s' % params)
        self.assertEqual(r.content, '')

        p, _created = Place.objects.get_or_create(cemetery=self.cemetery, area=area, row='', place='123')

        r = self.ugh_client.get('/burials/get_place/?cemetery=%s&area=%s&row=&place_number=%s' % params)
        self.assertNotEqual(str(r.content.decode('utf-8')), '')
        self.assertContains(r, p.place)

class ExhumationTest(TestCase):
    def setUp(self):
        activate('ru')
        self.client = Client()
        self.ugh_client = Client()

        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        self.ugh_org = Org.objects.create(type=Org.PROFILE_UGH, name='ugh')
        Profile.objects.create(user=self.ugh_user, org=self.ugh_org)
        self.ugh_client.login(username='ugh', password='test')

        self.cemetery = Cemetery.objects.create(name='test cem', time_begin='12:00', time_end='17:00', ugh=self.ugh_org)
        self.area = Area.objects.create(cemetery=self.cemetery, name='rest')
        self.place = Place.objects.create(
            cemetery=self.cemetery,
            area=None,
            row=None,
            place='123',
            responsible=None,
        )
        self.burial = Burial.objects.create(
            cemetery=self.cemetery,
            status=Burial.STATUS_CLOSED,
            source_type=Burial.SOURCE_ARCHIVE,
            place=self.place,
            ugh=self.ugh_org,
        )

    def test_model(self):
        now = datetime.datetime.now()
        ex = ExhumationRequest(place=self.place, burial=self.burial, plan_date=now.date(), plan_time=now.time())
        self.assertEqual(Burial.objects.get().place, self.place)
        self.assertEqual(Burial.objects.get().exhumated, None)

        ex.save()
        self.assertEqual(Burial.objects.get().place, None)
        self.assertEqual(Burial.objects.get().exhumated, ex)
        self.assertEqual(Burial.objects.get().exhumated.place, self.place)
        self.assertEqual(Burial.objects.get().status, Burial.STATUS_EXHUMATED)

    def test_view(self):
        self.assertEqual(ExhumationRequest.objects.count(), 0)

        r = self.ugh_client.post('/burials/%s/exhumate/' % self.burial.pk, {
            'fact_date': '01.01.2001', 'plan_time': '10:10',
            })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(ExhumationRequest.objects.count(), 0)
        self.assertEqual(Burial.objects.get().place, self.place)
        self.assertEqual(Burial.objects.get().exhumated, None)

        r = self.ugh_client.post('/burials/%s/exhumate/' % self.burial.pk, {
            'fact_date': '01.01.2001', 'plan_time': '10:10', 'applicant_organization': self.ugh_org.pk, 'opf': 'org',
            })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(ExhumationRequest.objects.count(), 1)

        self.assertEqual(Burial.objects.get().place, None)
        self.assertEqual(Burial.objects.get().status, Burial.STATUS_EXHUMATED)
        self.assertEqual(Burial.objects.get().exhumated, ExhumationRequest.objects.get())
        self.assertEqual(Burial.objects.get().exhumated.place, self.place)
        self.assertEqual(ExhumationRequest.objects.get().applicant, None)
        self.assertEqual(ExhumationRequest.objects.get().applicant_organization, self.ugh_org)

    def test_cancel(self):
        self.assertEqual(ExhumationRequest.objects.count(), 0)

        r = self.ugh_client.post('/burials/%s/exhumate/' % self.burial.pk, {
            'fact_date': '01.01.2001', 'plan_time': '10:10', 'applicant_organization': self.ugh_org.pk, 'opf': 'org',
            })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(ExhumationRequest.objects.count(), 1)
        self.assertEqual(Log.objects.all().count(), 1)

        ex = ExhumationRequest.objects.get()

        r = self.ugh_client.post('/burials/%s/exhumate/cancel/' % ex.pk)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(ExhumationRequest.objects.count(), 0)
        self.assertEqual(ex.burial.status, Burial.STATUS_CLOSED)
        self.assertEqual(Log.objects.all().count(), 2)

class TestPlaces(TestCase):
    def setUp(self):
        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        self.ugh_org = Org.objects.create(type=Org.PROFILE_UGH, name='ugh')
        Profile.objects.create(user=self.ugh_user, org=self.ugh_org)

        self.cemetery = Cemetery.objects.create(name='test cem', time_begin='12:00', time_end='17:00', ugh=self.ugh_org)
        self.area = Area.objects.create(cemetery=self.cemetery, name='rest')

    def test_manual(self):
        self.cemetery.places_algo = Cemetery.PLACE_MANUAL
        place = Place(
            cemetery=self.cemetery,
            area=self.area,
            row='234',
            place=None,
            responsible=None,
        )
        self.assertEqual(place.place, None)

        place.save()
        self.assertEqual(place.place, None)

    def test_area(self):
        self.cemetery.places_algo = Cemetery.PLACE_AREA
        old_place = Place.objects.create(
            cemetery=self.cemetery,
            area=self.area,
            row='234',
            place='123',
            responsible=None,
        )
        wrong_place = Place.objects.create(
            cemetery=self.cemetery,
            area=None,
            row='234',
            place='245',
            responsible=None,
        )
        place = Place(
            cemetery=self.cemetery,
            area=self.area,
            row=None,
            place=None,
            responsible=None,
        )
        self.assertEqual(place.place, None)

        place.save()
        self.assertEqual(str(place.place), '124')

    def test_row(self):
        self.cemetery.places_algo = Cemetery.PLACE_ROW
        old_place = Place.objects.create(
            cemetery=self.cemetery,
            area=self.area,
            row='234',
            place='123',
            responsible=None,
        )
        wrong_place = Place.objects.create(
            cemetery=self.cemetery,
            area=self.area,
            row=None,
            place='245',
            responsible=None,
        )
        more_wrong_place = Place.objects.create(
            cemetery=self.cemetery,
            area=None,
            row='234',
            place='345',
            responsible=None,
        )
        place = Place(
            cemetery=self.cemetery,
            area=self.area,
            row='234',
            place=None,
            responsible=None,
        )
        self.assertEqual(place.place, None)

        place.save()
        self.assertEqual(str(place.place), '124')

    def test_k2(self):
        self.cemetery.places_algo = Cemetery.PLACE_CEM_YEAR
        place = Place(
            cemetery=self.cemetery,
            area=self.area,
            row='234',
            place=None,
            responsible=None,
        )
        self.assertEqual(place.place, None)

        place.save()
        self.assertEqual(str(place.place), str(datetime.date.today().year) + '0001')

        old_place = Place.objects.create(
            cemetery=self.cemetery,
            area=None,
            row=None,
            place=str(datetime.date.today().year) + '0123',
            responsible=None,
        )
        more_wrong_place = Place.objects.create(
            cemetery=self.cemetery,
            area=self.area,
            row='234',
            place=str(datetime.date.today().year+1) + '0245',
            responsible=None,
        )
        place = Place(
            cemetery=self.cemetery,
            area=self.area,
            row='234',
            place=None,
            responsible=None,
        )
        self.assertEqual(place.place, None)

        place.save()
        self.assertEqual(str(place.place), str(datetime.date.today().year) + '0124')

