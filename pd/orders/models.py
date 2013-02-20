# coding=utf-8
from __builtin__ import property
from burials.models import Burial
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext as _

from reports.models import Report
from users.models import Org


class Product(models.Model):
    PRODUCT_BURIAL = 'burial'
    PRODUCT_CATAFALQUE = 'catafalque'
    PRODUCT_LOADERS = 'loaders'
    PRODUCT_DIGGERS = 'diggers'
    PRODUCT_SIGN = 'SIGN'
    PRODUCT_TYPES = (
        (PRODUCT_BURIAL, _(u"Захоронение")),
        (PRODUCT_CATAFALQUE, _(u"Автокатафалк")),
        (PRODUCT_LOADERS, _(u"Грузчики")),
        (PRODUCT_DIGGERS, _(u"Рытье могилы")),
        (PRODUCT_SIGN, _(u"Написание надмогильной таблички")),
    )

    loru = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_LORU}, null=True, verbose_name=_(u"ЛОРУ"))
    name = models.CharField(_(u"Название"), max_length=255)
    measure = models.CharField(_(u"Ед. изм."), max_length=255, default=_(u"шт"))
    price = models.DecimalField(_(u"Цена"), max_digits=20, decimal_places=2)
    ptype = models.CharField(_(u"Тип"), max_length=255, choices=PRODUCT_TYPES, null=True, blank=True)

    class Meta:
        verbose_name = _(u"Товар")
        verbose_name_plural = _(u"Товары")

    def __unicode__(self):
        return self.name

    def is_burial(self):
        return self.ptype == self.PRODUCT_BURIAL

class Order(models.Model):
    loru = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_LORU}, null=True, verbose_name=_(u"ЛОРУ"))
    person = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Заказчик-ФЛ"), null=True, blank=True)
    org = models.ForeignKey(Org, verbose_name=_(u"Заказчик-ЮЛ"), null=True, blank=True, related_name='org_orders')
    dt = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _(u"Заказ")
        verbose_name_plural = _(u"Заказы")

    def __unicode__(self):
        return u'%s %s' % (self.loru, self.dt)

    @property
    def customer(self):
        return self.person or self.org

    @property
    def total(self):
        return sum([i.total for i in self.orderitem_set.all()], 0)

    def total_float(self):
        return float(self.total)

    def get_catafalquedata(self):
        try:
            return self.catafalquedata
        except CatafalqueData.DoesNotExist:
            return

    def has_catafalque(self):
        return self.orderitem_set.filter(product__ptype=Product.PRODUCT_CATAFALQUE).exists()

    def get_coffindata(self):
        try:
            return self.coffindata
        except CoffinData.DoesNotExist:
            return

    def has_coffin(self):
        ptypes = [Product.PRODUCT_DIGGERS, Product.PRODUCT_LOADERS]
        return self.orderitem_set.filter(product__ptype__in=ptypes).exists()

    def get_documents(self):
        ct = ContentType.objects.get_for_model(self)
        return Report.objects.filter(content_type=ct, object_id=self.pk).order_by('-pk')

    def get_burial(self):
        bo = Burial.objects.filter(order=self)
        try:
            return bo[0]
        except IndexError:
            return None

class OrderItem(models.Model):
    order = models.ForeignKey(Order, editable=False)
    product = models.ForeignKey(Product, verbose_name=_(u"Товар"))
    quantity = models.DecimalField(_(u"Кол-во"), max_digits=20, decimal_places=2, default=1)
    cost = models.DecimalField(_(u"Цена"), max_digits=20, decimal_places=2, editable=False)

    class Meta:
        verbose_name = _(u"Позиция")
        verbose_name_plural = _(u"Позиции")

    def __unicode__(self):
        return u'%s - %s' % (self.order, self.product)
    
    def save(self, *args, **kwargs):
        if not self.cost:
            try:
                self.cost = self.product.price
            except Product.DoesNotExist:
                pass
            else:
                return super(OrderItem, self).save(*args, **kwargs)

    @property
    def total(self):
        return self.cost * self.quantity

class CatafalqueData(models.Model):
    order = models.OneToOneField('orders.Order', editable=False)

    route = models.TextField(_(u"Маршрут"))
    start_time = models.TimeField(_(u"Время подачи"))
    duration_time = models.TimeField(_(u"Время работы"))

class CoffinData(models.Model):
    order = models.OneToOneField('orders.Order', editable=False)

    size = models.TextField(_(u"Размер"))
