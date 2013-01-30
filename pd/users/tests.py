from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase, Client
from django.utils.translation import activate
from users.models import Profile, Org


class LoginTest(TestCase):
    def setUp(self):
        activate('ru')
        self.user = User.objects.create_user(username='test', email='test@example.com', password='test')
        org = Org.objects.create(name='name', type=Org.PROFILE_LORU)
        Profile.objects.create(user=self.user, org=org)
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
        activate('ru')
        self.client = Client()

    def test_loru(self):
        self.client.get('/register/')
        r = self.client.post('/register/', dict(
            username='test', email='test@example.com', password1='test', password2='test',
            type=Org.PROFILE_LORU, name='test loru'
        ))
        self.assertEqual(r.status_code, 302)
        self.client.login(username='test', password='test')
        org = Org.objects.create(name='name', type=Org.PROFILE_LORU)
        profile = User.objects.get().profile
        profile.org = org
        profile.save()
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'].profile.is_loru(), True)

    def test_ugh(self):
        self.client.get('/register/')
        r = self.client.post('/register/', dict(
            username='test', email='test@example.com', password1='test', password2='test',
        ))
        self.assertEqual(r.status_code, 302)
        self.client.login(username='test', password='test')
        org = Org.objects.create(name='name', type=Org.PROFILE_UGH)
        profile = User.objects.get().profile
        profile.org = org
        profile.save()
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'].profile.is_ugh(), True)

class ProfileTest(TestCase):
    def setUp(self):
        activate('ru')
        self.user = User.objects.create_user(username='test', email='test@example.com', password='test')
        self.client = Client()

    def test_profile(self):
        self.client.login(username='test', password='test')
        r = self.client.get('/profile/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['user'], self.user)
        self.assertNotIn('id="id_loru_list-1-loru"', r.content)

        r = self.client.post('/profile/', {'org_type': Org.PROFILE_LORU, 'org_name': 'LORU'})
        self.assertEqual(r.status_code, 302)

        profile = Profile.objects.get()
        self.assertEqual(profile.org.type, Org.PROFILE_LORU)

        r = self.client.get('/profile/')
        self.assertNotIn('id="id_loru_list-1-loru"', r.content)

        profile.org = None
        profile.save()

        r = self.client.post('/profile/', {'org_type': Org.PROFILE_UGH, 'org_name': 'UGH'})
        self.assertEqual(r.status_code, 302)

        profile = Profile.objects.get()
        self.assertEqual(profile.org.type, Org.PROFILE_UGH)

        r = self.client.get('/profile/')
        self.assertIn('id="id_loru_list-1-loru"', r.content)
