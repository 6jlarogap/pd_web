import re

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase, Client
from django.core import mail


class OrgRegTest(TestCase):
    def test_basic(self):
        c = Client()
        self.assertEqual(User.objects.count(), 0)

        r = c.post('/registration/', {
            'name': 'test',
            'slug': 'test',
            'email': 'test@example.com',
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.filter(is_active=False).count(), 1)

        re_match = re.findall('http://%s(\S*)' % Site.objects.get_current().domain, mail.outbox[0].body)
        self.assertEqual(len(re_match), 1)

        url = re_match[0]
        r2 = c.post(url, {
            'username': 'test',
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'password': 'password',
            'password_confirm': 'password',
        })
        print r2.content
        self.assertEqual(r2.status_code, 302)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.filter(is_active=True).count(), 1)
