from burials.models import Cemetery, BurialRequest
from django.contrib.auth.models import User
from django.test.client import Client
from django.test.testcases import TestCase
from django.utils.translation import activate, get_language
from persons.models import DeadPerson
from users.models import Profile, ProfileLORU, Org


class LoginTest(TestCase):
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

    def test_lists(self):
        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

    def test_create(self):
        r = self.ugh_client.get('/requests/create/')
        self.assertEqual(r.status_code, 302)

        r = self.loru_client.get('/requests/create/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(BurialRequest.objects.all().count(), 0)

        r = self.loru_client.post('/requests/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(BurialRequest.objects.all().count(), 1)

        br = BurialRequest.objects.all()[0]
        self.assertEqual(br.status, BurialRequest.STATUS_DRAFT)

    def test_created_lists(self):
        r = self.loru_client.post('/requests/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        self.assertEqual(r.status_code, 302)
        br = BurialRequest.objects.all()[0]
        br.status = BurialRequest.STATUS_READY
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
        r = self.loru_client.post('/requests/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        self.assertEqual(r.status_code, 302)
        br = BurialRequest.objects.all()[0]
        br.deadman = DeadPerson.objects.create(last_name='Ivanov')
        br.save()

        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 0)
        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.post('/requests/view/%s/' % br.pk, {'ready': '1'})

        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 1)
        self.assertIn('loru', r.content)

        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.ugh_client.post('/requests/view/%s/' % br.pk, {'approve': '1'})

        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 1)
        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.ugh_client.post('/requests/view/%s/' % br.pk, {'complete': '1'})
        self.assertEqual(r.status_code, 302)

        r = self.ugh_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 0)
        r = self.loru_client.get('/?show=1')
        self.assertEqual(r.context['burials'].count(), 0)

    def test_back(self):
        r = self.loru_client.post('/requests/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        br = BurialRequest.objects.all()[0]
        br.deadman = DeadPerson.objects.create(last_name='Ivanov')
        br.save()

        r = self.loru_client.post('/requests/view/%s/' % br.pk, {'ready': '1'})
        r = self.ugh_client.post('/requests/view/%s/' % br.pk, {'approve': '1'})

        br = BurialRequest.objects.all()[0]
        self.assertEqual(br.status, BurialRequest.STATUS_APPROVED)

        r = self.loru_client.post('/requests/view/%s/' % br.pk, {'back': '1'})

        br = BurialRequest.objects.all()[0]
        self.assertEqual(br.status, BurialRequest.STATUS_BACKED)

        r = self.loru_client.post('/requests/view/%s/' % br.pk, {'ready': '1'})
        r = self.ugh_client.post('/requests/view/%s/' % br.pk, {'approve': '1'})
        r = self.ugh_client.post('/requests/view/%s/' % br.pk, {'complete': '1'})

        br = BurialRequest.objects.all()[0]
        self.assertEqual(br.status, BurialRequest.STATUS_CLOSED)

    def test_archive(self):
        r = self.loru_client.post('/requests/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        self.assertEqual(r.status_code, 302)
        br = BurialRequest.objects.all()[0]
        self.assertEqual(br.status, BurialRequest.STATUS_DRAFT)

        r = self.ugh_client.get('/requests/archive/')
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.get('/requests/archive/')
        self.assertEqual(r.context['burials'].count(), 1)

        self.ugh_user.profile.org.loru_list.all().delete()

        r = self.ugh_client.get('/requests/archive/')
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.get('/requests/archive/')
        self.assertEqual(r.context['burials'].count(), 1)

    def test_edit(self):
        r = self.loru_client.post('/requests/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        self.assertEqual(r.status_code, 302)

        br = BurialRequest.objects.all()[0]
        self.assertEqual(br.creator, self.loru_user)
        self.assertEqual(br.is_edit(), True)

        r = self.loru_client.get('/requests/edit/%s/' % br.pk)
        self.assertEqual(r.status_code, 200)

        r = self.ugh_client.get('/requests/edit/%s/' % br.pk)
        self.assertEqual(r.status_code, 302)


