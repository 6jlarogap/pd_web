from decimal import Decimal
from django.contrib.auth.models import User
from django.test.client import Client
from django.test.testcases import TestCase
from django.utils.translation import activate
from logs.models import Log

from orders.models import Product, Order, CatafalqueData, OrderItem, CoffinData
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
        self.loru_org = Org.objects.create(
            type=Org.PROFILE_LORU, name='loru'
        )
        Profile.objects.create(
            user=self.loru_user, org=self.loru_org,
        )
        self.loru_client = Client()
        self.loru_client.login(username='loru', password='test')
        self.product = Product.objects.create(
            loru=self.loru_org, name='test product', measure='items', price='10.50', ptype=Product.PRODUCT_BURIAL
        )

    def test_list(self):
        r = self.loru_client.get('/order/')
        self.assertEqual(r.status_code, 200)

    def test_create(self):
        r = self.loru_client.get('/order/create/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Order.objects.all().count(), 0)

        r = self.loru_client.post('/order/create/', {
            'applicant_organization': self.loru_org.pk, 'opf': 'org', 'payment': 'cash'
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Order.objects.all().count(), 1)
        self.assertEqual(Order.objects.get().loru, self.loru_user.profile.org)
        self.assertEqual(Order.objects.get().applicant, None)
        self.assertEqual(Order.objects.get().applicant_organization, self.loru_org)

    def test_edit(self):
        o = Order.objects.create(loru=self.loru_user.profile.org, applicant_organization=self.loru_org)

        r = self.loru_client.get('/order/%s/applicant/' % o.pk)
        self.assertEqual(r.status_code, 200)

        r = self.loru_client.post('/order/%s/applicant/' % o.pk, {
            'applicant-last_name': 'Test', 'applicant-first_name': 'Test', 'applicant-middle_name': 'Test', 'org': '',
            'opf': 'person', 'payment': 'cash',
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Order.objects.get().loru, self.loru_user.profile.org)
        self.assertEqual(Order.objects.get().applicant.last_name, 'Test')
        self.assertEqual(Order.objects.get().applicant_organization, None)

        r = self.loru_client.post('/order/%s/products/' % o.pk, {
            'orderitem_set-0-id': '', 'orderitem_set-0-product': '%s' % self.product.pk, 'orderitem_set-0-quantity': '10',
            'orderitem_set-1-id': '', 'orderitem_set-1-product': '', 'orderitem_set-1-quantity': '1',
            'orderitem_set-2-id': '', 'orderitem_set-2-quantity': '1', 'orderitem_set-2-product': '',
            'orderitem_set-INITIAL_FORMS': '0', 'orderitem_set-MAX_NUM_FORMS': '', 'orderitem_set-TOTAL_FORMS': '3',
            })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Order.objects.get().orderitem_set.all().count(), 1)

    def test_print(self):
        o = Order.objects.create(loru=self.loru_user.profile.org, applicant_organization=self.loru_org)
        self.assertEqual(o.get_documents().count(), 0)

        r = self.loru_client.get('/order/%s/print/' % o.pk)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(o.get_documents().count(), 1)

        r = self.loru_client.get('/order/%s/contract/' % o.pk)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(o.get_documents().count(), 2)

    def test_same_products(self):
        self.product_same = self.product
        self.product_type = Product.objects.create(
            loru=self.loru_org, name='test other', measure='items', price='10.50', ptype=Product.PRODUCT_BURIAL
        )
        self.product_other = Product.objects.create(
            loru=self.loru_org, name='test diggers', measure='items', price='10.50', ptype=Product.PRODUCT_DIGGERS
        )

        o = Order.objects.create(loru=self.loru_user.profile.org, applicant_organization=self.loru_org)
        self.assertEqual(Order.objects.get().orderitem_set.all().count(), 0)

        r = self.loru_client.post('/order/%s/products/' % o.pk, {
            'orderitem_set-0-id': '', 'orderitem_set-0-product': '%s' % self.product.pk, 'orderitem_set-0-quantity': '10',
            'orderitem_set-1-id': '', 'orderitem_set-1-product': '%s' % self.product_same.pk, 'orderitem_set-1-quantity': '1',
            'orderitem_set-2-id': '', 'orderitem_set-2-product': '%s' % self.product_type.pk, 'orderitem_set-2-quantity': '1',
            'orderitem_set-3-id': '', 'orderitem_set-3-product': '%s' % self.product_other.pk, 'orderitem_set-3-quantity': '1',
            'orderitem_set-INITIAL_FORMS': '0', 'orderitem_set-MAX_NUM_FORMS': '', 'orderitem_set-TOTAL_FORMS': '4',
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Order.objects.get().orderitem_set.all().count(), 2)
        self.assertEqual(Order.objects.get().orderitem_set.get(product=self.product).quantity, 1)
        self.assertEqual(Order.objects.get().orderitem_set.get(product=self.product_other).quantity, 1)

    def test_cat(self):
        self.product_cat = Product.objects.create(
            loru=self.loru_org, name='test', measure='items', price='10.50', ptype=Product.PRODUCT_CATAFALQUE
        )

        o = Order.objects.create(loru=self.loru_user.profile.org, applicant_organization=self.loru_org)
        self.assertEqual(o.has_catafalque(), False)
        self.assertEqual(o.get_catafalquedata(), None)

        oi = OrderItem.objects.create(product=self.product_cat, order=o)
        self.assertEqual(o.has_catafalque(), True)
        self.assertEqual(o.get_catafalquedata(), None)

        cd = CatafalqueData.objects.create(order=o, route='test', start_time='12:00')
        self.assertEqual(o.has_catafalque(), True)
        self.assertEqual(o.get_catafalquedata(), cd)

    def test_coffin_diggers(self):
        self.product_cat = Product.objects.create(
            loru=self.loru_org, name='test', measure='items', price='10.50', ptype=Product.PRODUCT_DIGGERS
        )

        o = Order.objects.create(loru=self.loru_user.profile.org, applicant_organization=self.loru_org)
        self.assertEqual(o.has_coffin(), False)
        self.assertEqual(o.get_coffindata(), None)

        oi = OrderItem.objects.create(product=self.product_cat, order=o)
        self.assertEqual(o.has_coffin(), True)
        self.assertEqual(o.get_coffindata(), None)

        cd = CoffinData.objects.create(order=o, size='1:0:0')
        self.assertEqual(o.has_coffin(), True)
        self.assertEqual(o.get_coffindata(), cd)

    def test_coffin_loaders(self):
        self.product_cat = Product.objects.create(
            loru=self.loru_org, name='test', measure='items', price='10.50', ptype=Product.PRODUCT_LOADERS
        )

        o = Order.objects.create(loru=self.loru_user.profile.org, applicant_organization=self.loru_org)
        self.assertEqual(o.has_coffin(), False)
        self.assertEqual(o.get_coffindata(), None)

        oi = OrderItem.objects.create(product=self.product_cat, order=o)
        self.assertEqual(o.has_coffin(), True)
        self.assertEqual(o.get_coffindata(), None)

        cd = CoffinData.objects.create(order=o, size='1:0:0')
        self.assertEqual(o.has_coffin(), True)
        self.assertEqual(o.get_coffindata(), cd)

    def test_cat_coffin_others(self):
        self.product_cat = Product.objects.create(
            loru=self.loru_org, name='test', measure='items', price='10.50', ptype=Product.PRODUCT_BURIAL
        )

        o = Order.objects.create(loru=self.loru_user.profile.org, applicant_organization=self.loru_org)
        oi = OrderItem.objects.create(product=self.product_cat, order=o)
        self.assertEqual(o.has_coffin(), False)
        self.assertEqual(o.get_coffindata(), None)
        self.assertEqual(o.has_catafalque(), False)
        self.assertEqual(o.get_catafalquedata(), None)

    def test_comment(self):
        o = Order.objects.create(loru=self.loru_user.profile.org, applicant_organization=self.loru_org)

        r = self.loru_client.post('/order/%s/comment/' % o.pk, {'comment': 'test'})
        self.assertEqual(r.status_code, 302)

        self.assertEqual(Log.objects.all().count(), 1)
        self.assertTrue('test' in Log.objects.get().msg)
