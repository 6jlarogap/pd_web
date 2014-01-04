# coding=utf-8
from __builtin__ import property
import datetime
from burials.models import Burial
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext as _

from reports.models import Report
from users.models import Org
from pd.models import BaseModel, GetLogsMixin


class ProductCategory(models.Model):
    name = models.CharField(_(u"Название"), max_length=255)
    icon = models.FileField(u"Иконка", upload_to='icons', blank=True, null=True)

class Product(models.Model):
    PRODUCT_CATAFALQUE = 'catafalque'
    PRODUCT_LOADERS = 'loaders'
    PRODUCT_DIGGERS = 'diggers'
    PRODUCT_SIGN = 'SIGN'
    PRODUCT_TYPES = (
        (PRODUCT_CATAFALQUE, _(u"Автокатафалк")),
        (PRODUCT_LOADERS, _(u"Грузчики")),
        (PRODUCT_DIGGERS, _(u"Рытье могилы")),
        (PRODUCT_SIGN, _(u"Написание надмогильной таблички")),
    )

    loru = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_LORU}, null=True, verbose_name=_(u"ЛОРУ"))
    name = models.CharField(_(u"Название"), max_length=255)
    description = models.TextField(_(u"Описание"), blank=True, default='')
    measure = models.CharField(_(u"Ед. изм."), max_length=255, default=_(u"шт"))
    price = models.DecimalField(_(u"Цена"), max_digits=20, decimal_places=2)
    ptype = models.CharField(_(u"Тип"), max_length=255, choices=PRODUCT_TYPES, null=True, blank=True)
    default = models.BooleanField(_(u"По умолчанию"), default=False, blank=True)
    photo = models.FileField(u"Фото", upload_to='product-photo', blank=True, null=True)
    currency = models.ForeignKey('billing.Currency', verbose_name=_(u"Валюта"))
    sku = models.CharField(_(u"Артикул"), max_length=255, blank=True, default='')

    class Meta:
        verbose_name = _(u"Товар")
        verbose_name_plural = _(u"Товары")

    def __unicode__(self):
        return u'%s (%s р.)' % (self.name, self.price)

    def is_burial(self):
        return self.ptype == self.PRODUCT_BURIAL

class Order(GetLogsMixin, BaseModel):
    PAYMENT_CASH = 'cash'
    PAYMENT_WIRE = 'wire'
    PAYMENT_CHOICES = (
        (PAYMENT_CASH, _(u'Наличный')),
        (PAYMENT_WIRE, _(u'Безналичный')),
    )

    loru = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_LORU}, null=True, verbose_name=_(u"ЛОРУ"))
    loru_number = models.PositiveIntegerField(null=True, editable=False)
    payment = models.CharField(_(u"Тип платежа"), max_length=255, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    applicant = models.ForeignKey('persons.AlivePerson', verbose_name=_(u"Заказчик-ФЛ"), null=True, blank=True,
                                  on_delete=models.PROTECT)
    applicant_organization = models.ForeignKey(Org, verbose_name=_(u"Заказчик-ЮЛ"), null=True, blank=True, related_name='org_orders')
    agent_director = models.BooleanField(_(u"Директор-Агент"), default=False, blank=True)
    agent = models.ForeignKey('users.Profile', verbose_name=_(u"Агент"), null=True, blank=True,
                              limit_choices_to={'is_agent': True}, on_delete=models.PROTECT)
    dover = models.ForeignKey('users.Dover', verbose_name=_(u"Доверенность"), null=True, blank=True,
                              on_delete=models.PROTECT)
    annulated = models.BooleanField(_(u'Аннулировано'), editable=False, default=False)
    cost = models.DecimalField(_(u"Цена"), max_digits=20, decimal_places=2, editable=False)
    dt = models.DateField(_(u"Дата заказа"))
    burial = models.ForeignKey(Burial, related_name='burial_orders', editable=False, null=True)

    class Meta:
        verbose_name = _(u"Заказ")
        verbose_name_plural = _(u"Заказы")
        # unique_together = (
        #     ('loru_number', 'loru'),
        # )

    def __unicode__(self):
        return u'%s от %s' % (self.loru_number or _(u"б/н"), self.dt.strftime('%d.%m.%Y'))

    def save(self, *args, **kwargs):
        if not self.cost:
            self.cost = 0
        if not self.loru_number and self.loru:
            existing = Order.objects.filter(loru=self.loru).exclude(loru_number__isnull=True).order_by('-loru_number')
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            try:
                self.loru_number = int(existing[0].loru_number) + 1
            except (IndexError, TypeError), e:
                self.loru_number = 1
        return super(Order, self).save(*args, **kwargs)

    def annulate(self):
        self.annulated = True
        b = self.burial
        if b:
            save_burial = False
            if b.status in [Burial.STATUS_READY, Burial.STATUS_APPROVED]:
                b.status = Burial.STATUS_BACKED
                b.account_number = None
                save_burial = True
            if b.can_loru_annulate():
                b.annulated = True
                save_burial = True
            if  save_burial:
                b.save()
        self.save()

    def recover(self):
        self.annulated = False
        self.save()

    @property
    def customer(self):
        return self.applicant or (self.applicant_organization and self.get_formal_org()) or ''

    def get_formal_org(self):
        org = self.applicant_organization
        if self.agent_director:
            return _(u"%s, в лице директора %s") % (org, org.director)
        else:
            params = (org, self.agent, self.dover.number)
            return _(u"\"%s\", в лице агента %s, действующего на основании доверенности %s") % params

    @property
    def total(self):
        return self.cost

    def total_float(self):
        return float(self.total)

    def has_burial(self):
        return self.orderitem_set.filter(product__ptype=Product.PRODUCT_BURIAL).exists()

    def get_catafalquedata(self):
        try:
            return self.catafalquedata
        except CatafalqueData.DoesNotExist:
            return

    def has_catafalque(self):
        return self.orderitem_set.filter(product__ptype=Product.PRODUCT_CATAFALQUE).exists()

    def get_addinfodata(self):
        try:
            return self.addinfodata
        except AddInfoData.DoesNotExist:
            return

    def get_coffindata(self):
        try:
            return self.coffindata
        except CoffinData.DoesNotExist:
            return

    def has_coffin(self):
        ptypes = [Product.PRODUCT_DIGGERS, Product.PRODUCT_LOADERS]
        return self.orderitem_set.filter(product__ptype__in=ptypes).exists()

    def has_sign(self):
        return self.orderitem_set.filter(product__ptype=Product.PRODUCT_SIGN).exists()

    def has_diggers(self):
        return self.orderitem_set.filter(product__ptype=Product.PRODUCT_DIGGERS).exists()

    def has_loaders(self):
        return self.orderitem_set.filter(product__ptype=Product.PRODUCT_LOADERS).exists()

    def has_services(self):
        # return self.has_diggers() or self.has_loaders() or self.has_sign() or self.has_catafalque()
        # Но это все имеющиеся сейчас типы услуг. Быстрее будет:
        return self.orderitem_set.filter(product__ptype__isnull=False).exists()

    def get_documents(self):
        ct = ContentType.objects.get_for_model(self)
        return Report.objects.filter(content_type=ct, object_id=self.pk).order_by('-pk')

    def item_count(self):
        return self.orderitem_set.all().count()

    def get_catafalque_hours(self):
        if not self.has_catafalque():
            return
        hrs = self.orderitem_set.filter(product__ptype=Product.PRODUCT_CATAFALQUE)[0].quantity
        minutes = int(round(hrs * 60))
        return dict(hour=minutes // 60, minute=minutes % 60)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, editable=False)
    product = models.ForeignKey(Product, verbose_name=_(u"Товар"))
    quantity = models.DecimalField(_(u"Кол-во"), max_digits=20, decimal_places=2, default=1)
    cost = models.DecimalField(_(u"Цена"), max_digits=20, decimal_places=2, editable=True)

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
        return super(OrderItem, self).save(*args, **kwargs)

    @property
    def total(self):
        return self.cost * self.quantity

class CatafalqueData(models.Model):
    order = models.OneToOneField('orders.Order', editable=False)

    route = models.TextField(_(u"Маршрут"))
    start_time = models.TimeField(_(u"Время подачи"))
    start_place = models.TextField(_(u"Место подачи"), null=True)
    end_time = models.TimeField(_(u"Время отпуска клиентом"), null=True)
    cemetery_time = models.TimeField(_(u"Время заезда на кладбище"), null=True)

class AddInfoData(models.Model):
    order = models.OneToOneField('orders.Order', editable=False)
    add_info = models.TextField(_(u"Доп.инфо"), blank=True)

class CoffinData(models.Model):
    order = models.OneToOneField('orders.Order', editable=False)
    size = models.TextField(_(u"Размер"))

def recount_cost(instance, **kwargs):
    instance.order.cost = sum([i.total for i in instance.order.orderitem_set.all()], 0)
    instance.order.save()
models.signals.post_save.connect(recount_cost, sender=OrderItem)
models.signals.post_delete.connect(recount_cost, sender=OrderItem)
