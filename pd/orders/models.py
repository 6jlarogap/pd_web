# coding=utf-8
from django.db import models
from django.utils.translation import ugettext as _

from users.models import Org


class Product(models.Model):
    loru = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_LORU}, null=True, verbose_name=_(u"ЛОРУ"))
    name = models.CharField(_(u"Название"), max_length=255)
    measure = models.CharField(_(u"Ед. изм."), max_length=255, default=_(u"шт"))
    price = models.DecimalField(_(u"Цена"), max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _(u"Товар")
        verbose_name_plural = _(u"Товары")

    def __unicode__(self):
        return self.name

class Order(models.Model):
    loru = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_LORU}, null=True, verbose_name=_(u"ЛОРУ"))
    dt = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _(u"Заказ")
        verbose_name_plural = _(u"Заказы")

    def __unicode__(self):
        return u'%s %s' % (self.loru, self.dt)

class OrderItem(models.Model):
    order = models.ForeignKey(Order)
    product = models.ForeignKey(Product, verbose_name=_(u"Товар"))
    quantity = models.DecimalField(_(u"Кол-во"), max_digits=20, decimal_places=2, default=1)
    cost = models.DecimalField(_(u"Цена"), max_digits=20, decimal_places=2)
    total = models.DecimalField(_(u"Стоимость"), max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _(u"Позиция")
        verbose_name_plural = _(u"Позиции")

    def __unicode__(self):
        return u'%s - %s' % (self.order, self.product)

