from burials.models import Cemetery
from django.contrib.auth.models import User
from django.test import TestCase, Client
from logs.models import write_log, Log
from users.models import Profile


class LogsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        self.client = Client()
        self.client.login(username='ugh', password='test')
        self.cemetery = Cemetery.objects.create(name='test cem', time_begin='12:00', time_end='17:00')

    def test_basic(self):
        r = self.client.get('/')
        self.assertEqual(Log.objects.all().count(), 0)

        req = r.context['request']

        write_log(req, None, 'test 1')
        self.assertEqual(Log.objects.all().count(), 1)

        write_log(req, self.user, 'test 2')
        self.assertEqual(Log.objects.all().count(), 2)

    def test_create_request(self):
        self.assertEqual(Log.objects.all().count(), 0)

        Profile.objects.create(
            user=self.user, type=Profile.PROFILE_LORU, name='loru'
        )
        r = self.client.post('/create/', {'cemetery': self.cemetery.pk, 'plan_date': '12.12.2013', 'plan_time': '12:00'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Log.objects.all().count(), 1)


