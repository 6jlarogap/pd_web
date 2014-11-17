# coding=utf-8
from __builtin__ import property
import datetime
import os, shutil
from autoslug import AutoSlugField

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext as _
from django.db.models import Sum
from django.db.models.query_utils import Q

from burials.models import Burial
from reports.models import Report
from users.models import Org
from pd.models import BaseModel, GetLogsMixin, upload_slugified, Files
from geo.models import PointsModel


class Service(models.Model):
    """
    Сервисы, предлагаемые нами для поставщиков товаров/услуг

    Перечисляются в fixtures
    """
    name = models.CharField(_(u"Название"), max_length=255, unique=True)
    title = models.CharField(_(u"Заглавие"), max_length=255)
    description = models.TextField(_(u"Описание"), default='')

class Measure(models.Model):
    """
    Возможные единицы измерения за сервисы

    Перечисляются в fixtures
    """
    service = models.ForeignKey(Service, verbose_name=_(u"Сервис"), on_delete=models.PROTECT)
    name = models.CharField(_(u"Название"), max_length=255)
    title = models.CharField(_(u"Заглавие"), max_length=255)

    class Meta:
        unique_together = (
            ('service', 'name', ),
        )

class OrgService(models.Model):
    """
    Сервисы, на которые подписалась организация
    """
    org = models.ForeignKey(Org, verbose_name=_(u"Поставщик"), on_delete=models.PROTECT)
    service = models.ForeignKey(Service, verbose_name=_(u"Тип сервиса"), on_delete=models.PROTECT)
    enabled = models.BooleanField(_(u"Включен"), default=True)

    class Meta:
        unique_together = (
            ('org', 'service', ),
        )

    def service_name(self):
        return self.service.name

class OrgServicePrice(models.Model):
    """
    Цены сервисов организации
    """
    orgservice = models.ForeignKey(OrgService, verbose_name=_(u"Служба"), on_delete=models.PROTECT)
    measure = models.ForeignKey(Measure, verbose_name=_(u"Единица измерения"), on_delete=models.PROTECT)
    price = models.DecimalField(_(u"Цена"), max_digits=20, decimal_places=2, default='0.00')

    class Meta:
        unique_together = (
            ('orgservice', 'measure', ),
        )

    def measure_name(self):
        return self.measure.name

    def price_float(self):
        return float(self.price)

class ProductCategory(models.Model):
    name = models.CharField(_(u"Название"), max_length=255)
    icon = models.ImageField(u"Иконка", upload_to=upload_slugified, blank=True, null=True)

    class Meta:
        verbose_name = _(u"Категория")
        verbose_name_plural = _(u"Категории")
        ordering = ('name', )

    def __unicode__(self):
        return self.name

class ProductGroup(models.Model):
    loru = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_LORU}, verbose_name=_(u"ЛОРУ"))
    productcategory = models.ForeignKey(ProductCategory, verbose_name=_(u"Категория"), on_delete=models.PROTECT)
    name = models.CharField(_(u"Название"), max_length=255)
    description = models.TextField(_(u"Описание"), blank=True, default='')
    icon = models.FileField(u"Иконка", upload_to=upload_slugified, blank=True, null=True)

    class Meta:
        verbose_name = _(u"Подкатегория")
        verbose_name_plural = _(u"Подкатегории")
        ordering = ('name', )
        unique_together = (
            ('loru', 'productcategory', 'name', ),
        )

    def __unicode__(self):
        return self.name

class Product(BaseModel):
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
    
    PRODUCT_NAME_MAXLEN = 60

    loru = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_LORU}, null=True, verbose_name=_(u"ЛОРУ"))
    name = models.CharField(_(u"Название"), max_length=255)
    slug = AutoSlugField(populate_from='name', max_length=255, editable=False,
                         unique=True, null=True, always_update=True)
    description = models.TextField(_(u"Описание"), blank=True, default='')
    measure = models.CharField(_(u"Ед. изм."), max_length=255, default=_(u"шт"))
    price = models.DecimalField(_(u"Цена розничная"), max_digits=20, decimal_places=2)
    price_wholesale = models.DecimalField(_(u"Цена оптовая"), max_digits=20, decimal_places=2)
    ptype = models.CharField(_(u"Тип"), max_length=255, choices=PRODUCT_TYPES, null=True, blank=True)
    default = models.BooleanField(_(u"По умолчанию"), default=False, blank=True)
    photo = models.ImageField(u"Фото", max_length=255, upload_to=upload_slugified, blank=True, null=True)
    productcategory = models.ForeignKey(ProductCategory, verbose_name=_(u"Категория"), on_delete=models.PROTECT)
    productgroup = models.ForeignKey(ProductGroup, verbose_name=_(u"Подкатегория"), null=True, editable=False,
                                     on_delete=models.PROTECT)
    sku = models.CharField(_(u"Артикул"), max_length=255, blank=True, default='')
    is_public_catalog = models.BooleanField(_(u"Показать в публичном каталоге"), default=False)
    is_wholesale = models.BooleanField(_(u"Показать в каталоге оптовикам"), default=False)

    class Meta:
        verbose_name = _(u"Товар")
        verbose_name_plural = _(u"Товары")
        ordering = ['name']

    def __unicode__(self):
        return u'%s (%s р.)' % (self.name, self.price)

    def is_burial(self):
        return self.ptype == self.PRODUCT_BURIAL

    def delete(self):
        path = self.photo and self.photo.path or None
        thmb = os.path.join(settings.THUMBNAILS_STORAGE_ROOT, self.photo.name) if path else None
        try:
            super(Product, self).delete()
        except:
            raise
        else:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except IOError:
                    pass
            if thmb and os.path.exists(thmb):
                shutil.rmtree(thmb, ignore_errors=True)

class Order(GetLogsMixin, BaseModel):
    # Типы заказов.
    # "Изначальный" джанго заказ
    TYPE_BURIAL = 'burial'
    # Оптовый заказ
    TYPE_TRADE = 'trade'
    # Заказ на сервисы, т.е. инмцируемый пользователем- физ-лицом
    TYPE_CUSTOMER = 'customer'
    ORDER_TYPES = (
        (TYPE_BURIAL, _(u'Заказ на захоронение')),
        (TYPE_TRADE, _(u'Оптовый заказ')),
        (TYPE_CUSTOMER, _(u'Заказ пользователя')),
    )

    PAYMENT_CASH = 'cash'
    PAYMENT_WIRE = 'wire'
    PAYMENT_CHOICES = (
        (PAYMENT_CASH, _(u'Наличный')),
        (PAYMENT_WIRE, _(u'Безналичный')),
    )

    # Заказы от пользователя-физ.лица
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DONE = 'done'

    # Оптовые заказы
    STATUS_POSTED = 'posted'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_SHIPPED = 'shipped'
    STATUS_ACCEPTED = 'accepted'

    STATUS_TYPES = (
        (STATUS_PENDING, _(u"Размещен")),
        (STATUS_IN_PROGRESS, _(u"В процессе выполнения")),
        (STATUS_DONE, _(u"Выполнен")),

        (STATUS_POSTED, _(u"Размещен")),
        (STATUS_CONFIRMED, _(u"Подтвержден")),
        (STATUS_SHIPPED, _(u"Отправлен")),
        (STATUS_ACCEPTED, _(u"Принят")),
    )

    type = models.CharField(_(u"Тип Заказ"), max_length=255, choices=ORDER_TYPES, default=TYPE_BURIAL, editable=False)

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

    customplace = models.ForeignKey('persons.CustomPlace', verbose_name=_(u"Место захоронения"), null=True, editable=False)
    status = models.CharField(_(u"Статус"), max_length=255, choices=STATUS_TYPES, default=STATUS_PENDING, editable=False,)
    applicant_approved = models.NullBooleanField(_(u"Одобрено заказчиком"), null=True, editable=False,)

    # При создании оптового заказа исполнителем, когда заказчик обращении к нему по телефону
    # (applicant == applicant_organization = None):
    title = models.CharField(_(u"Наименование покупателя"), max_length=255, default='', editable=False)
    phones = models.TextField(_(u"Телефоны"), null=True, editable=False)
    address = models.ForeignKey('geo.Location', verbose_name=_(u"Адрес"), null=True, editable=False)

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

    def is_type_burial(self):
        return self.type == Order.TYPE_BURIAL

    def is_type_trade(self):
        return self.type == Order.TYPE_TRADE

    def is_type_customer(self):
        return self.type == Order.TYPE_CUSTOMER

class ServiceItem(models.Model):
    order = models.ForeignKey(Order)
    orgservice = models.ForeignKey(OrgService, verbose_name=_(u"Услуга"), on_delete=models.PROTECT)
    cost = models.DecimalField(_(u"Цена"), max_digits=20, decimal_places=2)

class OrderComment(BaseModel):

    TYPE_PRIVATE = 'private'
    TYPE_SHARED = 'shared'
    TYPE_PUBLIC = 'public'
    COMMENT_TYPES = (
        (TYPE_PRIVATE, _(u"Личный")),
        (TYPE_SHARED, _(u"Доступный автору и собеседнику")),
        (TYPE_PUBLIC, _(u"Общедоступный")),
    )

    order = models.ForeignKey(Order, verbose_name=_(u"Заказ"), )
    user = models.ForeignKey('auth.User', verbose_name=_(u"Пользователь"), )
    type = models.CharField(_(u"Тип"), max_length=255, choices=COMMENT_TYPES, default=TYPE_SHARED)
    comment = models.TextField(_(u"Комментарий"), )

class ResultFile(Files):
    """
    Результаты выполнения заказа на фото места
    """
    order = models.ForeignKey(Order, verbose_name=_(u"Заказ"), )

class OrderItem(models.Model):
    order = models.ForeignKey(Order, editable=False)
    product = models.ForeignKey(Product, verbose_name=_(u"Товар"))
    quantity = models.DecimalField(_(u"Кол-во"), max_digits=20, decimal_places=2, default=1)
    cost = models.DecimalField(_(u"Цена"), max_digits=20, decimal_places=2, editable=True)

    # name, description, productcategory, productcategory_name,
    # productgroup, productgroup_name, measure:
    #    содержат копии сооответствующих полей продукта в момент внесения его в заказ
    # is_wholesale_with_vat:
    #    содержит копию сооответствующего параметра лору в момент создания заказа

    name = models.CharField(_(u"Название"), max_length=255, editable=False)
    measure = models.CharField(_(u"Ед. изм."), max_length=255, default=_(u"шт"))
    description = models.TextField(_(u"Описание"), blank=True, default='')
    productcategory = models.ForeignKey(ProductCategory, verbose_name=_(u"Категория"),
                                        editable=False, on_delete=models.PROTECT)
    productcategory_name = models.CharField(_(u"Название категории"), max_length=255, editable=False)
    productgroup = models.ForeignKey(ProductGroup, verbose_name=_(u"Подкатегория"), null=True,
                                     editable=False, on_delete=models.PROTECT)
    productgroup_name = models.CharField(_(u"Название подкатегории"), max_length=255, default='', editable=False)
    productgroup_description = models.TextField(_(u"Описание подкатегории"), blank=True, default='', editable=False)
    comment = models.TextField(_(u"Комментарий"), blank=True, default='', editable=False)
    is_wholesale_with_vat = models.BooleanField(_(u"Цена с НДС"), default=False, editable=False)

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
                self.cost = 0.00
        if not self.name and self.product:
            # Доп. поля никогда не заполнялись ранее
            #
            self.name = self.product.name,
            self.measure = self.product.measure,
            self.description = self.product.description,
            self.productcategory = self.product.productcategory
            self.productcategory_name = self.product.productcategory.name
            self.productgroup = self.product.productgroup
            self.productgroup_name = self.product.productgroup and self.product.productgroup.name or ''
            self.productgroup_description = self.product.productgroup and self.product.productgroup.description or ''
        return super(OrderItem, self).save(*args, **kwargs)

    @property
    def total(self):
        return self.cost * self.quantity

class Iorder(BaseModel):
    """
    Интернет-заказ оптовой продукции
    """
    STATUS_POSTED = 'posted'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_SHIPPED = 'shipped'
    STATUS_ACCEPTED = 'accepted'
    STATUS_TYPES = (
        (STATUS_POSTED, _(u"Размещен")),
        (STATUS_CONFIRMED, _(u"Подтвержден")),
        (STATUS_SHIPPED, _(u"Отправлен")),
        (STATUS_ACCEPTED, _(u"Принят")),
    )
    supplier = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_LORU},
                                      verbose_name=_(u"Поставщик"), related_name='iorder_suppliers')
    customer = models.ForeignKey(Org,
                                      verbose_name=_(u"Покупатель"), related_name='iorder_customers',
                                      null=True)
    status = models.CharField(_(u"Статус"), max_length=255, choices=STATUS_TYPES, default=STATUS_POSTED)
    # Порядковый номер в пределах поставщика, покупателя, года
    number = models.IntegerField(_(u"Номер"))
    comment = models.TextField(_(u"Комментарий"), blank=True, default='')
    # При обращении к заказу по телефону (customer=None):
    title = models.CharField(_(u"Наименование покупателя"), max_length=255, default='')
    phones = models.TextField(_(u"Телефоны"), null=True)
    address = models.ForeignKey('geo.Location', verbose_name=_(u"Адрес"), null=True)

    def number_verbose(self):
        """
        Автогенерируемый номер заказа
        """
        return u"%d-%d-%d-%d" % (
            self.dt_created.year,
            self.customer and self.customer.pk or 0,
            self.supplier.pk,
            self.number,
        )

    def items_count(self):
        return IorderItem.objects.filter(iorder=self).count()

    def total(self):
        return IorderItem.objects.filter(iorder=self). \
                aggregate(total=Sum('price_wholesale'))['total']

    def total_float(self):
        return float(self.total())

    def products_json(self):
       return [dict(
                    id=item.product.pk,
                    count=float(item.quantity),
                    comment=item.comment,
               ) for item in IorderItem.objects.filter(iorder=self)
       ]

class IorderItem(BaseModel):
    """
    Пункты интернет-заказа оптовой продукции

    price_wholesale, productcategory, productcategory_name, productgroup, productgroup_name,
    name, description, measure:
        содержат копии сооответствующих полей продукта в момент внесения его в интернет-заказ
    is_wholesale_with_vat:
        содержит копию сооответствующего параметра лору в момент создания заказа

    """
    iorder = models.ForeignKey(Iorder, editable=False)
    product = models.ForeignKey(Product, verbose_name=_(u"Товар"))
    quantity = models.DecimalField(_(u"Кол-во"), max_digits=20, decimal_places=2, default=1)
    measure = models.CharField(_(u"Ед. изм."), max_length=255, default=_(u"шт"))
    price_wholesale = models.DecimalField(_(u"Цена оптовая"), max_digits=20, decimal_places=2)
    name = models.CharField(_(u"Название"), max_length=255)
    productcategory = models.ForeignKey(ProductCategory, verbose_name=_(u"Категория"),
                                        on_delete=models.PROTECT)
    productcategory_name = models.CharField(_(u"Название категории"), max_length=255)
    productgroup = models.ForeignKey(ProductGroup, verbose_name=_(u"Подкатегория"), null=True,
                                     on_delete=models.PROTECT)
    productgroup_name = models.CharField(_(u"Название подкатегории"), max_length=255, default='')
    productgroup_description = models.TextField(_(u"Описание подкатегории"), blank=True, default='')
    comment = models.TextField(_(u"Комментарий"), blank=True, default='')
    is_wholesale_with_vat = models.BooleanField(_(u"Цена с НДС"))

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

class Route(PointsModel):
    order = models.ForeignKey(Order)

    class Meta:
        unique_together = (
            ('order', 'index', ),
        )

def recount_cost(instance, **kwargs):
    instance.order.cost = sum([i.total for i in instance.order.orderitem_set.all()], 0)
    instance.order.save()
models.signals.post_save.connect(recount_cost, sender=OrderItem)
models.signals.post_delete.connect(recount_cost, sender=OrderItem)