from burials.models import Cemetery, BurialRequest
from django.contrib.auth.models import User
from django.test.client import Client
from django.test.testcases import TestCase
from django.utils.translation import activate, get_language
from users.models import Profile, ProfileLORU


class LoginTest(TestCase):
    def setUp(self):
        activate('ru')
        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        Profile.objects.create(
            user=self.ugh_user, type=Profile.PROFILE_UGH, name='ugh'
        )
        self.loru_user = User.objects.create_user(username='loru', email='test@example.com', password='test')
        Profile.objects.create(
            user=self.loru_user, type=Profile.PROFILE_LORU, name='loru'
        )
        self.ugh_client = Client()
        self.ugh_client.login(username='ugh', password='test')
        self.loru_client = Client()
        self.loru_client.login(username='loru', password='test')
        self.cemetery = Cemetery.objects.create(name='test cem', time_begin='12:00', time_end='17:00')
        self.ugh_user.profile.loru_list.create(loru=self.loru_user.profile)

    def test_lists(self):
        r = self.ugh_client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.loru_client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

    def test_create(self):
        r = self.ugh_client.get('/create/')
        self.assertEqual(r.status_code, 302)

        r = self.loru_client.get('/create/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(BurialRequest.objects.all().count(), 0)

        r = self.loru_client.post('/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(BurialRequest.objects.all().count(), 1)

        br = BurialRequest.objects.all()[0]
        self.assertEqual(br.approved_ugh, None)
        self.assertEqual(br.processed_loru, None)
        self.assertEqual(br.completed_ugh, None)

    def test_created_lists(self):
        r = self.loru_client.post('/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        self.assertEqual(r.status_code, 302)
        br = BurialRequest.objects.all()[0]

        r = self.ugh_client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

        ProfileLORU.objects.all().delete()

        r = self.ugh_client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 0)

    def test_actions(self):
        r = self.loru_client.post('/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        self.assertEqual(r.status_code, 302)
        br = BurialRequest.objects.all()[0]

        r = self.ugh_client.get('/')
        self.assertEqual(r.context['burials'].count(), 1)
        r = self.loru_client.get('/')
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.ugh_client.get('/view/%s/?approve=1' % br.pk)

        r = self.ugh_client.get('/')
        self.assertEqual(r.context['burials'].count(), 0)
        r = self.loru_client.get('/')
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.get('/view/%s/?execute=1' % br.pk)
        self.assertEqual(r.status_code, 302)

        r = self.ugh_client.get('/')
        self.assertEqual(r.context['burials'].count(), 1)
        r = self.loru_client.get('/')
        self.assertEqual(r.context['burials'].count(), 0)

        r = self.ugh_client.get('/view/%s/?complete=1' % br.pk)
        self.assertEqual(r.status_code, 302)

        r = self.ugh_client.get('/')
        self.assertEqual(r.context['burials'].count(), 0)
        r = self.loru_client.get('/')
        self.assertEqual(r.context['burials'].count(), 0)

    def test_archive(self):
        r = self.loru_client.post('/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        self.assertEqual(r.status_code, 302)
        br = BurialRequest.objects.all()[0]

        r = self.ugh_client.get('/archive/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

        r = self.loru_client.get('/archive/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['burials'].count(), 1)

        self.assertEqual(br.status, BurialRequest.STATUS_DICT[0])





