from orgs.models import ORG_TYPES_UGH
import re

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase, Client
from django.core import mail


class OrgRegTest(TestCase):
    def test_basic(self):
        c = Client()
        self.assertEqual(User.objects.count(), 0)

        r = c.post('/accounts/register/', {
            'username': 'test',
            'email': 'test@example.com',
            'password1': 'password',
            'password2': 'password',
            'type': ORG_TYPES_UGH,
            'name': 'test',
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.filter(is_active=False).count(), 1)

        re_match = re.findall('http://%s(\S*)' % Site.objects.get_current().domain, mail.outbox[0].body)
        self.assertEqual(len(re_match), 1)

        url = re_match[0]
        r2 = c.get(url)
        self.assertEqual(r2.status_code, 302)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.filter(is_active=True).count(), 1)
