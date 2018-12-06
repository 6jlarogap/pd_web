from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase, Client
from django.utils.translation import activate
from django.conf import settings

from users.models import Profile, Org


class LoginTest(TestCase):
    def setUp(self):
        activate('ru')
        settings.DATABASES['fias'] = settings.TEST_FIAS
        self.user = User.objects.create_user(username='test', email='test@example.com', password='test')
        org = Org.objects.create(name='name', type=Org.PROFILE_LORU)
        Profile.objects.create(user=self.user, org=org)
        self.client = Client()

    def test_login(self):
        self.client.get('/login/')
        r = self.client.post('/login/', dict(username='test', password='test'))
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/order/dashboard/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'], self.user)

    def test_logout(self):
        self.client.login(username='test', password='test')
        r = self.client.get('/order/dashboard/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'], self.user)

        r = self.client.get('/logout/')
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/?show=1')
        self.assertIsInstance(r.context['user'], AnonymousUser)

class RegisterTest(TestCase):
    def setUp(self):
        activate('ru')
        settings.DATABASES['fias'] = settings.TEST_FIAS
        self.client = Client()

    def test_loru(self):
        self.client.get('/register/')
        r = self.client.post('/register/', dict(
            username='test', email='test@example.com', password1='test', password2='test',
            first_name='test loru', last_name='last loru',
        ))
        self.assertEqual(r.status_code, 302)
        org = Org.objects.create(name='name', type=Org.PROFILE_LORU)
        u = User.objects.get()
        profile = u.profile
        profile.org = org
        profile.save()
        r = self.client.get('/order/dashboard/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'].is_authenticated(), True)
        self.assertEqual(r.context['user'].profile.is_loru(), True)
        self.assertEqual(r.context['user'].first_name, 'test loru')
        self.assertEqual(r.context['user'].last_name, 'last loru')

    def test_ugh(self):
        self.client.get('/register/')
        r = self.client.post('/register/', dict(
            username='test', email='test@example.com', password1='test', password2='test',
            first_name='test ugh', last_name='last ugh',
        ))
        self.assertEqual(r.status_code, 302)
        org = Org.objects.create(name='name', type=Org.PROFILE_UGH)
        u = User.objects.get()
        profile = u.profile
        profile.org = org
        profile.save()
        r = self.client.get('/?show=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'].is_authenticated(), True)
        self.assertEqual(r.context['user'].profile.is_ugh(), True)
        self.assertEqual(r.context['user'].first_name, 'test ugh')
        self.assertEqual(r.context['user'].last_name, 'last ugh')

class ProfileTest(TestCase):
    def setUp(self):
        activate('ru')
        settings.DATABASES['fias'] = settings.TEST_FIAS
        self.user = User.objects.create_user(username='test', email='test@example.com', password='test')
        self.client = Client()

    def test_profile(self):
        self.client.login(username='test', password='test')
        r = self.client.get('/profile/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'], self.user)
        self.assertNotIn('id="id_loru_list-1-loru"', r.content)

        r = self.client.post('/profile/', {
            'org_type': Org.PROFILE_LORU, 'org_name': 'LORU', 'org_inn': '111', 'places_type': 'manual',
            'bankaccount_set-TOTAL_FORMS': '1', 'bankaccount_set-INITIAL_FORMS': '0', 'bankaccount_set-MAX_NUM_FORMS': '',
        })
        self.assertEqual(r.status_code, 302)

        profile = Profile.objects.get()
        self.assertEqual(profile.org.type, Org.PROFILE_LORU)

        r = self.client.get('/profile/')
        self.assertNotIn('id="id_loru_list-1-loru"', r.content)

        profile.org = None
        profile.save()

        r = self.client.post('/profile/', {
            'org_type': Org.PROFILE_UGH, 'org_name': 'UGH', 'org_inn': '222', 'places_type': 'manual', 'numbers_algo': '',
            'bankaccount_set-TOTAL_FORMS': '1', 'bankaccount_set-INITIAL_FORMS': '0', 'bankaccount_set-MAX_NUM_FORMS': '',
        })
        self.assertEqual(r.status_code, 302)

        profile = Profile.objects.get()
        self.assertEqual(profile.org.type, Org.PROFILE_UGH)

        r = self.client.get('/profile/')
        self.assertIn('id="id_loru_list-1-loru"', r.content)

class EditDataTest(TestCase):
    def setUp(self):
        activate('ru')
        settings.DATABASES['fias'] = settings.TEST_FIAS
        self.user = User.objects.create_user(username='test', email='test@example.com', password='test')
        self.client = Client()

        r = self.client.login(username='test', password='test')
        self.assertEquals(r, True)

        r = self.client.post('/profile/', {
            'org_type': Org.PROFILE_LORU, 'org_name': 'LORU', 'org_inn': '111', 'places_type': 'manual',
            'bankaccount_set-TOTAL_FORMS': '1', 'bankaccount_set-INITIAL_FORMS': '0', 'bankaccount_set-MAX_NUM_FORMS': '',
        })
        self.assertEqual(r.status_code, 302)

    def test_data(self):
        r = self.client.get('/user/%s/edit/' % self.user.pk)
        self.assertEqual(r.status_code, 200)

        u = User.objects.get()
        self.assertEqual(u.username, 'test')
        self.assertEqual(u.email, 'test@example.com')

        r = self.client.post('/user/%s/edit/' % self.user.pk, {'username': 'test1', 'email': 'test1@example.com'})
        self.assertEqual(r.status_code, 302)

        u = User.objects.get()
        self.assertEqual(u.username, 'test1')
        self.assertEqual(u.email, 'test1@example.com')

    def test_password(self):
        r = self.client.get('/user/%s/password/' % self.user.pk)
        self.assertEqual(r.status_code, 200)

        r = self.client.post('/user/%s/password/' % self.user.pk, {'password1': 'test1', 'password2': 'test1'})
        self.assertEqual(r.status_code, 302)

        self.client.logout()
        r = self.client.login(username='test', password='test')
        self.assertEquals(r, False)
        r = self.client.login(username='test', password='test1')
        self.assertEquals(r, True)

    def test_create(self):
        r = self.client.post('/user/create/', dict(
            username='test1', email='test1@example.com', password1='test1', password2='test1',
        ))
        self.assertEqual(r.status_code, 302)

        self.client.logout()
        r = self.client.login(username='test1', password='test1')
        self.assertEquals(r, True)
