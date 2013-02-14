# coding=utf-8
from __builtin__ import property
from django.db import models
from django.utils.translation import ugettext as _

from users.models import Org


class Product(models.Model):
    PRODUCT_BURIAL = 'burial'
    PRODUCT_TYPES = (
        (PRODUCT_BURIAL, _(u"Захоронение")),
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
    person = models.CharField(_(u"Заказчик-ФЛ"), max_length=255, null=True, blank=True)
    org = models.CharField(_(u"Заказчик-ЮЛ"), max_length=255, null=True, blank=True)
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
