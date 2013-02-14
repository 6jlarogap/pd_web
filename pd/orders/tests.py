from decimal import Decimal
from django.contrib.auth.models import User
from django.test.client import Client
from django.test.testcases import TestCase
from django.utils.translation import activate

from orders.models import Product, Order
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

class OrdersTest(TestCase):
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
        self.product = Product.objects.create(loru=loru_org, name='test product', measure='items', price='10.50')

    def test_list(self):
        r = self.loru_client.get('/order/')
        self.assertEqual(r.status_code, 200)

    def test_create(self):
        r = self.loru_client.get('/order/create/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Order.objects.all().count(), 0)

        r = self.loru_client.post('/order/create/', {
            'person': 'Test testov', 'org': 'Test LTD',
            })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Order.objects.all().count(), 1)
        self.assertEqual(Order.objects.get().loru, self.loru_user.profile.org)
        self.assertEqual(Order.objects.get().person, 'Test testov')
        self.assertEqual(Order.objects.get().org, 'Test LTD')

    def test_edit(self):
        o = Order.objects.create(loru=self.loru_user.profile.org, org='test LTD')

        r = self.loru_client.get('/order/%s/edit/' % o.pk)
        self.assertEqual(r.status_code, 200)

        r = self.loru_client.post('/order/%s/edit/' % o.pk, {
            'person': 'Test testov', 'org': '',
            'orderitem_set-0-id': u'', 'orderitem_set-0-product': u'%s' % self.product.pk, 'orderitem_set-0-quantity': u'10',
            'orderitem_set-1-id': u'', 'orderitem_set-1-product': u'', 'orderitem_set-1-quantity': u'1',
            'orderitem_set-2-id': u'', 'orderitem_set-2-quantity': u'1', 'orderitem_set-2-product': u'',
            'orderitem_set-INITIAL_FORMS': u'0', 'orderitem_set-MAX_NUM_FORMS': u'', 'orderitem_set-TOTAL_FORMS': u'3',
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Order.objects.get().loru, self.loru_user.profile.org)
        self.assertEqual(Order.objects.get().person, 'Test testov')
        self.assertEqual(Order.objects.get().org, '')
        self.assertEqual(Order.objects.get().orderitem_set.all().count(), 1)

