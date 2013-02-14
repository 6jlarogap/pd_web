from decimal import Decimal
from django.contrib.auth.models import User
from django.test.client import Client
from django.test.testcases import TestCase
from django.utils.translation import activate

from orders.models import Product
from users.models import Org, Profile


class ProductsTest(TestCase):
    def setUp(self):
        activate('ru')
        self.loru_user = User.objects.create_user(username='loru', email='test@example.com', password='test')
        loru_org = Org.objects.create(
            type=Org.PROFILE_LORU, name='loru'
        )
        Profile.objects.create(
            user=self.loru_user, org=loru_org,
        )
        self.loru_client = Client()
        self.loru_client.login(username='loru', password='test')

    def test_list(self):
        r = self.loru_client.get('/manage/product/')
        self.assertEqual(r.status_code, 200)

    def test_create(self):
        r = self.loru_client.get('/manage/product/create/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Product.objects.all().count(), 0)

        r = self.loru_client.post('/manage/product/create/', {
            'name': 'test', 'measure': 'items', 'price': '10.20',
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Product.objects.all().count(), 1)
        self.assertEqual(Product.objects.get().loru, self.loru_user.profile.org)

    def test_edit(self):
        p = Product.objects.create(
            loru=self.loru_user.profile.org, name='test', measure='items', price='10.20'
        )

        r = self.loru_client.get('/manage/product/%s/edit/' % p.pk)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Product.objects.get().price, Decimal('10.20'))

        r = self.loru_client.post('/manage/product/%s/edit/' % p.pk, {
            'name': 'test', 'measure': 'items', 'price': '10.50',
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Product.objects.get().price, Decimal('10.50'))
        self.assertEqual(Product.objects.get().loru, self.loru_user.profile.org)

