# coding=utf-8

from django.db import models
from django.utils.translation import ugettext_lazy as _

PT_COMMON = ''
PT_BURIAL = 'burial'

PRODUCT_TYPES = (
    (PT_COMMON, _(u'Обычная')),
    (PT_BURIAL, _(u'Захоронение')),
)

class Product(models.Model):
    """
    One product for using for orders. If `owner` is None - can be used by any user, else - available only for owner.
    """
    creator = models.ForeignKey('auth.User', blank=True, null=True, editable=False)
    name = models.CharField(_(u'Название'), max_length=255)
    type = models.CharField(_(u'Тип услуги'), max_length=255, choices=PRODUCT_TYPES)
    price = models.DecimalField(_(u'Стоимость'), max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _(u'Товар или услуга')
        verbose_name_plural = _(u'Товары и услуги')

    def __unicode__(self):
        return u'%s [%s, %s]' % (self.name, self.get_type_display(), self.creator)

class Order(models.Model):
    """
    Container for few products for one exact client (person or organization)
    """
    client_person = models.ForeignKey('persons.Person')
    client_org = models.ForeignKey('orgs.Organization')

    created = models.DateTimeField(auto_now_add=True)
    changed = models.DateTimeField(auto_now=True)

class OrderItem(models.Model):
    """
    One product used in Order. Contains almost nothing now but can be extended further.
    """
    order = models.ForeignKey(Order)
    ordering = models.PositiveIntegerField()
    product = models.ForeignKey(Product)