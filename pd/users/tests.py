from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase, Client
from users.models import Profile


class LoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', email='test@example.com', password='test')
        self.client = Client()

    def test_login(self):
        self.client.get('/login/')
        r = self.client.post('/login/', dict(username='test', password='test'))
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'], self.user)

    def test_logout(self):
        self.client.login(username='test', password='test')
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'], self.user)

        r = self.client.get('/logout/')
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/')
        self.assertIsInstance(r.context['user'], AnonymousUser)

class RegisterTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_loru(self):
        self.client.get('/register/')
        r = self.client.post('/register/', dict(
            username='test', email='test@example.com', password1='test', password2='test',
            type=Profile.PROFILE_LORU, name='test loru'
        ))
        self.assertEqual(r.status_code, 302)
        self.client.login(username='test', password='test')
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'].profile.is_loru(), True)

    def test_ugh(self):
        self.client.get('/register/')
        r = self.client.post('/register/', dict(
            username='test', email='test@example.com', password1='test', password2='test',
            type=Profile.PROFILE_UGH, name='test ugh'
        ))
        self.assertEqual(r.status_code, 302)
        self.client.login(username='test', password='test')
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'].profile.is_ugh(), True)

    def test_user(self):
        self.client.get('/register/')
        r = self.client.post('/register/', dict(
            username='test', email='test@example.com', password1='test', password2='test',
            type=Profile.PROFILE_USER, name='test user'
        ))
        self.assertEqual(r.status_code, 302)
        self.client.login(username='test', password='test')
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'].profile.is_user(), True)

class ProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', email='test@example.com', password='test')
        self.client = Client()

    def test_profile(self):
        self.client.login(username='test', password='test')
        r = self.client.get('/profile/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'], self.user)
        self.assertNotIn('id="id_loru_list-1-loru"', r.content)

        r = self.client.post('/profile/', {'type': Profile.PROFILE_LORU, 'name': 'LORU'})
        self.assertEqual(r.status_code, 302)

        profile = Profile.objects.get()
        self.assertEqual(profile.type, Profile.PROFILE_LORU)

        r = self.client.get('/profile/')
        self.assertNotIn('id="id_loru_list-1-loru"', r.content)

        r = self.client.post('/profile/', {'type': Profile.PROFILE_UGH, 'name': 'UGH'})
        self.assertEqual(r.status_code, 302)

        profile = Profile.objects.get()
        self.assertEqual(profile.type, Profile.PROFILE_UGH)

        r = self.client.get('/profile/')
        self.assertIn('id="id_loru_list-1-loru"', r.content)
