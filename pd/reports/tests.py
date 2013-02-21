from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from burials.models import Burial
from reports.models import Report
from users.models import Profile, Org


class BurialReportTest(TestCase):
    def setUp(self):
        self.loru_user = User.objects.create_user(username='loru', email='test@example.com', password='test')
        self.loru_org = Org.objects.create(
            type=Org.PROFILE_LORU, name='loru'
        )
        Profile.objects.create(
            user=self.loru_user, org=self.loru_org,
        )
        self.loru_client = Client()
        self.loru_client.login(username='loru', password='test')

    def test_create(self):
        b = Burial.objects.create(applicant_organization=self.loru_org)
        self.assertEqual(Report.objects.all().count(), 0)

        r = self.loru_client.get('/burials/%s/notification/' % b.pk)
        self.assertEqual(r.status_code, 302)

        self.assertEqual(Report.objects.all().count(), 1)
        r = self.loru_client.get('/reports/%s/' % Report.objects.get().pk)
        self.assertEqual(r.status_code, 200)

        r = self.loru_client.get('/burials/%s/spravka/' % b.pk)
        self.assertEqual(r.status_code, 302)

        self.assertEqual(Report.objects.all().count(), 2)
