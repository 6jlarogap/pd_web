from builtins import property
import datetime, time
import os, shutil, decimal
from autoslug import AutoSlugField

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction, IntegrityError
from django.apps import apps
get_model = apps.get_model
from django.utils.translation import ugettext as _
from django.db.models import Sum, F
from django.db.models.query_utils import Q

from burials.models import Burial, OrderPlace
from persons.models import OrderDeadPerson
from reports.models import Report
from users.models import Org, is_cabinet_user, is_trade_user
from pd.models import BaseModel, GetLogsMixin, upload_slugified, Files
from geo.models import PointsModel


class Service(models.Model):
    """
    Сервисы, предлагаемые нами для поставщиков товаров/услуг

    Перечисляются в fixtures
    """
    SERVICE_PHOTO = 'photo'
    SERVICE_DELIVERY = 'delivery'

    name = models.CharField(_("Название"), max_length=255, unique=True)
    title = models.CharField(_("Заглавие"), max_length=255)
    description = models.TextField(_("Описание"), default='')

class Measure(models.Model):
    """
    Возможные единицы измерения за сервисы

    Перечисляются в fixtures
    """
    service = models.ForeignKey(Service, verbose_name=_("Сервис"), on_delete=models.PROTECT)
    name = models.CharField(_("Название"), max_length=255)
    title = models.CharField(_("Заглавие"), max_length=255)

    class Meta:
        unique_together = (
            ('service', 'name', ),
        )

class OrgService(models.Model):
    """
    Сервисы, на которые подписалась организация-продавец товаров/услуг
    """
    org = models.ForeignKey(Org, verbose_name=_("Поставщик"), on_delete=models.PROTECT)
    service = models.ForeignKey(Service, verbose_name=_("Тип сервиса"), on_delete=models.PROTECT)
    enabled = models.BooleanField(_("Включен"), default=True)

    class Meta:
        unique_together = (
            ('org', 'service', ),
        )

    def service_name(self):
        return self.service.name

class OrgServicePrice(models.Model):
    """
    Цены сервисов организации-продавца товаров/услуг
    """
    orgservice = models.ForeignKey(OrgService, verbose_name=_("Служба"), on_delete=models.PROTECT)
    measure = models.ForeignKey(Measure, verbose_name=_("Единица измерения"), on_delete=models.PROTECT)
    price = models.DecimalField(_("Цена"), max_digits=20, decimal_places=2, default='0.00')

    class Meta:
        unique_together = (
            ('orgservice', 'measure', ),
        )

    def measure_name(self):
        return self.measure.name

    def price_float(self):
        return float(self.price)

class ProductCategory(models.Model):

    # Категории продуктов, которые доступны при заказе с визитом на место
    #
    AVAILABLE_FOR_VISIT_PKS = (
         5,   # Венки
         6,   # Цветы искусственные
         7,   # Цветы живые
        27,   # Букеты
        28,   # Свечи
        29,   # Лампады
    )

    name = models.CharField(_("Название"), max_length=255)
    sorting = models.CharField(_("Порядок сортировки"), max_length=2, editable=False, default='ZZ')
    icon = models.ImageField("Иконка", upload_to=upload_slugified, blank=True, null=True)

    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ('name', )

    def __str__(self):
        return self.name

class ProductGroup(models.Model):
    loru = models.ForeignKey(Org, verbose_name=_("ЛОРУ"), on_delete=models.CASCADE)
    productcategory = models.ForeignKey(ProductCategory, verbose_name=_("Категория"), on_delete=models.PROTECT)
    name = models.CharField(_("Название"), max_length=255)
    description = models.TextField(_("Описание"), blank=True, default='')
    icon = models.FileField("Иконка", upload_to=upload_slugified, blank=True, null=True)

    class Meta:
        verbose_name = _("Подкатегория")
        verbose_name_plural = _("Подкатегории")
        ordering = ('name', )
        unique_together = (
            ('loru', 'productcategory', 'name', ),
        )

    def __str__(self):
        return self.name

class Product(BaseModel):
    PRODUCT_CATAFALQUE = 'catafalque'
    PRODUCT_CATAFALQUE_COMFORT = 'catafalque_comfort'
    PRODUCT_LOADERS = 'loaders'
    PRODUCT_DIGGERS = 'diggers'
    PRODUCT_SIGN = 'SIGN'
    PRODUCT_VIP = 'VIP'
    PRODUCT_TYPES = (
        (PRODUCT_CATAFALQUE, _("Автокатафалк")),
        (PRODUCT_CATAFALQUE_COMFORT, _("Катафалк повыш. комфортности")),
        (PRODUCT_LOADERS, _("Грузчики")),
        (PRODUCT_DIGGERS, _("Рытье могилы")),
        (PRODUCT_SIGN, _("Написание надмогильной таблички")),
        (PRODUCT_VIP, _("ВИП бригада послепохоронного обслуживания")),
    )
    
    PRODUCT_NAME_MAXLEN = 60

    loru = models.ForeignKey(Org, null=True, verbose_name=_("Поставщик"), on_delete=models.CASCADE)
    name = models.CharField(_("Название"), max_length=255)
    slug = AutoSlugField(populate_from='name', max_length=255, editable=False,
                         unique=True, null=True, always_update=True)
    description = models.TextField(_("Описание"), blank=True, default='')
    measure = models.CharField(_("Ед. изм."), max_length=255, default=_("шт"))
    price = models.DecimalField(_("Цена розничная"), max_digits=20, decimal_places=2)
    price_wholesale = models.DecimalField(_("Цена оптовая"), max_digits=20, decimal_places=2)
    ptype = models.CharField(_("Тип"), max_length=255, choices=PRODUCT_TYPES, null=True, blank=True)
    default = models.BooleanField(_("По умолчанию"), default=False, blank=True)
    # True: товар, False: услуга
    stockable = models.BooleanField(_("Товар"), default=True, blank=True)
    photo = models.ImageField("Фото", max_length=255, upload_to=upload_slugified, blank=True, null=True)
    productcategory = models.ForeignKey(ProductCategory, verbose_name=_("Категория"), on_delete=models.PROTECT)
    productgroup = models.ForeignKey(ProductGroup, verbose_name=_("Подкатегория"), null=True, editable=False,
                                     on_delete=models.PROTECT)
    sku = models.CharField(_("Артикул"), max_length=255, blank=True, default='')
    is_public_catalog = models.BooleanField(_("Показать в публичном каталоге"), default=False)
    is_wholesale = models.BooleanField(_("Показать в каталоге оптовикам"), default=False)
    is_for_visit = models.BooleanField(_("Доступно для посещения места захоронения"), default=False)
    is_archived = models.BooleanField(_("Архивирован"), default=False)

    class Meta:
        verbose_name = _("Товар")
        verbose_name_plural = _("Товары")
        ordering = ['name']

    def __str__(self):
        currency_one_char = self.loru and self.loru.currency.one_char_name() or 'р'
        return '%s (%s %s.)' % (self.name, self.price, currency_one_char)

    def is_burial(self):
        return self.ptype == self.PRODUCT_BURIAL

    def delete_photo(self, photo):
        path = photo and photo.name and photo.path or None
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except IOError:
                pass
        thmb = os.path.join(settings.THUMBNAILS_STORAGE_ROOT, photo.name) if path else None
        if thmb and os.path.exists(thmb):
            shutil.rmtree(thmb, ignore_errors=True)

    def delete(self):
        photo = self.photo
        try:
            result = super(Product, self).delete()
        except:
            raise
        else:
            self.delete_photo(photo)
        return result

class Order(GetLogsMixin, BaseModel):
    # Типы заказов.
    # "Изначальный" джанго заказ
    TYPE_BURIAL = 'burial'
    # Заказ похорон, из front-end
    TYPE_FUNERAL = 'funeral'
    # Оптовый заказ
    TYPE_TRADE = 'trade'
    # Заказ на сервисы, т.е. инмцируемый пользователем- физ-лицом
    TYPE_CUSTOMER = 'customer'
    ORDER_TYPES = (
        (TYPE_BURIAL, _('Заказ на захоронение')),
        (TYPE_TRADE, _('Оптовый заказ')),
        (TYPE_CUSTOMER, _('Заказ пользователя')),
    )

    PAYMENT_CASH = 'cash'
    PAYMENT_WIRE = 'wire'
    PAYMENT_CHOICES = (
        (PAYMENT_CASH, _('Наличный')),
        (PAYMENT_WIRE, _('Безналичный')),
    )

    STATUS_POSTED = 'posted'
    STATUS_ACCEPTED = 'accepted'
    STATUS_ADVANCED = 'advanced'
    STATUS_PAID = 'paid'
    STATUS_DONE = 'done'

    STATUS_TYPES = (
        (STATUS_POSTED, _("Размещен")),
        (STATUS_ACCEPTED, _("Принят")),
        (STATUS_ADVANCED, _("Выплачен аванс")),
        (STATUS_PAID, _("Оплачен")),
        (STATUS_DONE, _("Выполнен")),
    )

    type = models.CharField(_("Тип Заказ"), max_length=255, choices=ORDER_TYPES, default=TYPE_BURIAL, editable=False)

    loru = models.ForeignKey(Org, null=True, verbose_name=_("ЛОРУ"), on_delete=models.CASCADE)
    loru_number = models.PositiveIntegerField(_("Номер в переделах исполнителя заказа"), null=True, editable=False)
    number = models.PositiveIntegerField(_("Номер в переделах исполнителя заказа и года"), null=True, editable=False)
    payment = models.CharField(_("Тип платежа"), max_length=255, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    applicant = models.ForeignKey('persons.AlivePerson', verbose_name=_("Заказчик-ФЛ"), null=True, blank=True,
                                  on_delete=models.PROTECT)
    applicant_organization = models.ForeignKey(Org, verbose_name=_("Заказчик-ЮЛ"), null=True, blank=True, related_name='org_orders', on_delete=models.CASCADE)
    agent_director = models.BooleanField(_("Директор-Агент"), default=False, blank=True)
    agent = models.ForeignKey('users.Profile', verbose_name=_("Агент"), null=True, blank=True,
                              limit_choices_to={'is_agent': True}, on_delete=models.PROTECT)
    dover = models.ForeignKey('users.Dover', verbose_name=_("Доверенность"), null=True, blank=True,
                              on_delete=models.PROTECT)
    annulated = models.BooleanField(_('Аннулирован'), editable=False, default=False)
    archived = models.BooleanField(_('Архивирован'), editable=False, default=False)
    cost = models.DecimalField(_("Цена"), max_digits=20, decimal_places=2, editable=False)
    dt = models.DateField(_("Дата заказа"))
    dt_paid = models.DateTimeField(_("Дата/время оплаты"), null=True)
    burial = models.ForeignKey(Burial, related_name='burial_orders', editable=False, null=True, on_delete=models.CASCADE)

    customplace = models.ForeignKey('persons.CustomPlace', verbose_name=_("Место захоронения"),
                                    null=True, editable=False, on_delete=models.PROTECT)
    status = models.CharField(_("Статус"), max_length=255, choices=STATUS_TYPES, default=STATUS_POSTED, editable=False,)
    applicant_approved = models.NullBooleanField(_("Одобрено заказчиком"), null=True, editable=False,)

    # При создании оптового заказа исполнителем, когда заказчик обращении к нему по телефону
    # (applicant == applicant_organization = None):
    title = models.CharField(_("Наименование покупателя"), max_length=255, default='', editable=False)
    phones = models.TextField(_("Телефоны"), null=True, editable=False)
    address = models.ForeignKey('geo.Location', verbose_name=_("Адрес"), null=True, editable=False, on_delete=models.CASCADE)

    # Для заказа похорон
    dt_due = models.DateField(_("Дата похорон"), editable=False, null=True)

    burial_plan_time = models.TimeField(_("План. время захоронения"), null=True, editable=False)
    initial_place = models.CharField(_("Место подачи катафалка"), max_length=255, editable=False, default='')
    initial_time = models.TimeField(_("Время подачи катафалка"), null=True, editable=False)
    service_place = models.CharField(_("Место отпевания"), max_length=255, editable=False, default='')
    service_time = models.TimeField(_("Время отпевания"), null=True, editable=False)
    repast_place = models.CharField(_("Место отпевания"), max_length=255, editable=False, default='')
    repast_time = models.TimeField(_("Время отпевания"), null=True, editable=False)

    class Meta:
        verbose_name = _("Заказ")
        verbose_name_plural = _("Заказы")
        # unique_together = (
        #     ('loru_number', 'loru'),
        # )

    def __str__(self):
        return '%s от %s' % (self.loru_number or _("б/н"), self.dt.strftime('%d.%m.%Y'))

    def save(self, *args, **kwargs):
        if not self.cost:
            self.cost = 0
        if self.loru:
            if not self.loru_number:
                existing = Order.objects.filter(loru=self.loru).exclude(loru_number__isnull=True).order_by('-loru_number')
                if self.pk:
                    existing = existing.exclude(pk=self.pk)
                try:
                    self.loru_number = int(existing[0].loru_number) + 1
                except (IndexError, TypeError) as e:
                    self.loru_number = 1
            if not self.number:
                year = self.dt and self.dt.year or datetime.date.today().year
                existing = Order.objects.filter(loru=self.loru, dt__year=year).exclude(number__isnull=True).order_by('-number')
                if self.pk:
                    existing = existing.exclude(pk=self.pk)
                try:
                    self.number = int(existing[0].number) + 1
                except (IndexError, TypeError) as e:
                    self.number = 1
        return super(Order, self).save(*args, **kwargs)

    @transaction.atomic
    def delete(self):
        for app, model in (
            ('orders', 'OrderComment'),
            ('orders', 'ResultFile'),
            ('orders', 'Route'),
            ('orders', 'OrderWebPay'),
            ('orders', 'ServiceItem'),
            ('orders', 'OrderItem'),
            ('persons', 'OrderDeadPerson'),
            ('burials', 'OrderPlace'),
           ):
            model = get_model(app, model)
            for item in model.objects.filter(order=self):
                item.delete()
        address = self.address
        if address:
            self.address = None
            self.save()
            try:
                address.delete()
            except IntegrityError:
                pass
        super(Order, self).delete()

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
            return _("%(org)s, в лице директора %(director)s") % dict(
                org=org, director=org.director
            )
        else:
            return _("\"%(org)s\", в лице агента %(agent)s, "
                     "действующего на основании доверенности %(dover)s") % dict(
                         org=org, agent=self.agent, dover=self.dover.number
            )

    @property
    def total(self):
        return self.cost

    def total_float(self):
        return float(self.total)

    def total_int(self):
        return int(self.total)

    def total_copecks(self):
        return int((self.total - int(self.total)) * 100)

    def has_burial(self):
        return self.orderitem_set.filter(product__ptype=Product.PRODUCT_BURIAL).exists()

    def get_catafalquedata(self):
        try:
            return self.catafalquedata
        except CatafalqueData.DoesNotExist:
            return

    def has_vip(self):
        return self.orderitem_set.filter(product__ptype=Product.PRODUCT_VIP).exists()

    def has_catafalque(self):
        return self.orderitem_set.filter(product__ptype=Product.PRODUCT_CATAFALQUE).exists()

    def has_catafalque_comfort(self):
        return self.orderitem_set.filter(product__ptype=Product.PRODUCT_CATAFALQUE_COMFORT).exists()

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

    def is_type_funeral(self):
        return self.type == Order.TYPE_FUNERAL

    def is_type_trade(self):
        return self.type == Order.TYPE_TRADE

    def is_type_customer(self):
        return self.type == Order.TYPE_CUSTOMER

    def number_verbose(self):
        """
        Автогенерируемый номер заказа
        """
        return "%d-%d-%d" % (
            self.dt.year,
            self.loru.pk,
            self.number or 0,
        )

    number_webpay = number_verbose

    def first_comment(self):
        """
        В оптовых заказах, при создании, обязательно делается комментарий
        """
        try:
            return OrderComment.objects.filter(order=self).order_by('dt_created')[0].comment
        except IndexError:
            return ''

    def products_json(self):
       return [dict(
                    id=item.product.pk,
                    count=float(item.quantity),
                    comment=item.comment,
               ) for item in OrderItem.objects.filter(order=self)
       ]

    def service_name(self):
        """
        Имя сервиса у заказа TYPE_CUSTOMER
        """
        result = type_delivery = type_org = None
        if self.is_type_customer():
            for serviceitem in ServiceItem.objects.filter(order=self):
                if serviceitem.orgservice.service.name == Service.SERVICE_DELIVERY:
                    type_delivery = Service.SERVICE_DELIVERY
                elif not type_org:
                    type_org = serviceitem.orgservice.service.name
            return type_org or type_delivey
        return result

    def customer_location(self):
        """
        Координаты места у заказа TYPE_CUSTOMER

        Конечная точка маршрута
        """
        result = None
        if self.is_type_customer():
            try:
                point = Route.objects.filter(order=self).order_by('-index')[0]
                return dict(latitude=point.lat, longitude=point.lng)
            except IndexError:
                pass
        return result

    def is_accessible(self, user):
        """
        Доступность ResultFile, OrderComment от этого Order и самого Order
        """
        result = False
        if is_trade_user(user):
            org = user.profile.org
            result = self.loru and self.loru == org or \
                     self.applicant_organization and self.applicant_organization == org
        elif is_cabinet_user(user):
            result = self.applicant and self.applicant.user and \
                     self.applicant.user == user
            # КОСТЫЛЬ!
            # Это для формируемых лориком заказов, в которых включены сервисы
            # В таких заказах applicant может отличаться от ответственного
            # с мобильным телефоном для входа, из которого (ответственного)
            # и формируется кабинетчик.
            if not result:
                result = self.customplace and \
                         self.customplace.user == user
        return bool(result)

    def price_photo(self):
        """
        Стоимость услуги фотографирования или None, если исполнитель не подписан на эту услугу
        """
        result = None
        if self.loru:
            try:
                result = OrgServicePrice.objects.filter(
                    orgservice__org=self.loru,
                    orgservice__service__name=Service.SERVICE_PHOTO,
                    orgservice__enabled=True,
                ).distinct()[0].price
            except IndexError:
                pass
        return result

    def has_photo(self):
        return self.serviceitem_set.filter(orgservice__service__name=Service.SERVICE_PHOTO).exists()

    def title_photo(self):
        try:
            return ResultFile.objects.filter(order=self, is_title=True)[0].bfile
        except IndexError:
            return None

    def stockable_products(self):
        return self.orderitem_set.filter(product__stockable=True)

    def items_to_act(self):
        """
        Товары и услуги, которые заносятся в Акт, для Ялты
        """
        return self.orderitem_set.filter(
            product__ptype__in = (
                Product.PRODUCT_CATAFALQUE,
                Product.PRODUCT_CATAFALQUE_COMFORT,
                Product.PRODUCT_LOADERS,
        ))

    def total_to_act(self):
        #result = self.items_to_act().aggregate(total=Sum(F('cost') * F('quantity'))['total']) or \
                #decimal.Decimal('0.00')
            # не получилось с F()*F()
        #return decimal.Decimal("{:.2f}".format(result))
        result = decimal.Decimal('0.00')
        items = self.items_to_act()
        for item in items:
            result += item.total
        return decimal.Decimal("{:.2f}".format(result))

    def total_to_act_int(self):
        return int(self.total_to_act())

    def total_to_act_copecks(self):
        total = self.total_to_act()
        return int((total - int(total)) * 100)

    def deadman(self):
        """
        усопший при заказе, для отчета
        """
        result = ''
        if self.burial:
            result = self.burial.deadman_or_bio()
        else:
            try:
                result = self.orderdeadperson
            except (OrderDeadPerson.DoesNotExist, AttributeError,):
                pass
        return result

    def cemetery(self):
        """
        кладбище при заказе, для отчета
        """
        result = ''
        if self.burial:
            result = self.burial.cemetery and self.burial.cemetery.name or ''
        else:
            try:
                place = self.orderplace
                if place.cemetery_text:
                    result = place.cemetery_text
                elif place.cemetery:
                    result = place.cemetery.name
            except (OrderPlace.DoesNotExist, AttributeError,):
                pass
        return result

    def is_advanced(self):
        return self.status == Order.STATUS_ADVANCED

    def is_paid(self):
        return self.status == Order.STATUS_PAID

class OrderItemMixin(object):

    def cost_float(self):
        return float(self.cost)

class ServiceItem(OrderItemMixin, models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    orgservice = models.ForeignKey(OrgService, verbose_name=_("Услуга"), on_delete=models.PROTECT)
    cost = models.DecimalField(_("Цена"), max_digits=20, decimal_places=2)

class OrderComment(BaseModel):

    TYPE_PRIVATE = 'private'
    TYPE_SHARED = 'shared'
    TYPE_PUBLIC = 'public'
    COMMENT_TYPES = (
        (TYPE_PRIVATE, _("Личный")),
        (TYPE_SHARED, _("Доступный автору и собеседнику")),
        (TYPE_PUBLIC, _("Общедоступный")),
    )

    order = models.ForeignKey(Order, verbose_name=_("Заказ"), on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', verbose_name=_("Пользователь"), on_delete=models.CASCADE)
    type = models.CharField(_("Тип"), max_length=255, choices=COMMENT_TYPES, default=TYPE_SHARED)
    comment = models.TextField(_("Комментарий"), )

class OrderWebPay(BaseModel):
    """
    Транзакции по успешной оплате заказа в WebPay
    """

    METHOD_TEST = 'test'
    METHOD_CARD = 'cc'
    PAYMENT_METHODS = (
        (METHOD_TEST, _("Тест, без реального платежа")),
        (METHOD_CARD, _("Платежная карточка")),
    )

    PAY_TYPE_COMPLETED = '1'
    PAY_TYPE_DECLINED = '2'
    PAY_TYPE_PENDING = '3'
    PAY_TYPE_AUTHORIZED = '4'
    PAY_TYPE_REFUNDED = '5'
    PAY_TYPE_SYSTEM = '6'
    PAY_TYPE_VOIDED = '7'
    PAY_TYPE_FAILED = '8'
    TRANSACTION_TYPES = (
        (PAY_TYPE_COMPLETED, _("Completed (Завершенная)")),
        (PAY_TYPE_DECLINED, _("Declined (Отклоненная)")),
        (PAY_TYPE_PENDING, _("Pending (В обработке)")),
        (PAY_TYPE_AUTHORIZED, _("Authorized (Авторизованная)")),
        (PAY_TYPE_REFUNDED, _("Refunded (Возвращенная)")),
        (PAY_TYPE_SYSTEM, _("System (Системная))")),
        (PAY_TYPE_VOIDED, _("Voided (Сброшенная после авторизации)")),
        (PAY_TYPE_FAILED, _("Failed (Ошибка в проведении транзакции)")),
    )

    # Успешной оплате соответствуют следующие типы PAY_TYPE
    SUCCESS_PAY_TYPES = (
        PAY_TYPE_COMPLETED,
        PAY_TYPE_AUTHORIZED,
    )

    order = models.ForeignKey(Order, verbose_name=_("Заказ"), on_delete=models.CASCADE)

    # Этот номер, wsb_order_num, "наш" номер заказа, формируемый функцией
    # Order.number_verbose(), отправляется в WebPay, чтобы тот попросил заказчика
    # расплатиться по заказу с этим нашим номером. Когда заказчик расплатится,
    # придет уведомление типа:
    #
    #   http(s)://.../api/orders/<order_pk>/webpay/notify?<wsb_order_num>
    #
    # В колонке wsb_order_num держим этот номер в целях протоколирования.
    # Возможно, по нему будет производится поиск
    # 
    wsb_order_num = models.CharField(_("Номер заказа"), max_length=255, db_index=True)

    # Имена этих полей -- в соответствии с полями ответа от WebPay
    # (кроме order_id (WebPay) == order_ident в этой модели)
    # Заполняются, когда придет ответ
    #
    transaction_id = models.CharField(_("Номер транзакции"), max_length=255, null=True)
    batch_timestamp = models.CharField(_("Время совершения транзакции"), max_length=255, null=True)
    currency_id = models.CharField(_("Код валюты согласно ISO4271"), max_length=255, null=True)
    amount = models.CharField(_("Сумма"), max_length=255, null=True)
    payment_method = models.CharField(_("Метод платежа"), max_length=255, choices=PAYMENT_METHODS, null=True)
    payment_type = models.CharField(_("Тип транзакции"), max_length=255, choices=TRANSACTION_TYPES, null=True)
    order_ident = models.CharField(_("Номер заказа в системе WebPay (order_id)"), max_length=255, null=True)
    rrn = models.CharField(_("Номер транзакции в системе Visa/MasterCard"), max_length=255, null=True)
    wsb_signature = models.CharField(_("Электронная подпись"), max_length=255, null=True)

class ResultFile(Files):
    """
    Результаты выполнения заказа на фото места
    """
    TYPE_IMAGE = 'image'
    TYPE_VIDEO = 'video'
    RESULT_TYPES = (
        (TYPE_IMAGE, _("Изображение")),
        (TYPE_VIDEO, _("Видео")),
    )

    # Мегабайт:
    MAX_IMAGE_SIZE = 10

    order = models.ForeignKey(Order, verbose_name=_("Заказ"), on_delete=models.CASCADE)
    type = models.CharField(_("Тип"), max_length=255, choices=RESULT_TYPES, default=TYPE_IMAGE)
    is_title = models.BooleanField(_("Титульное фото"), default=False, editable=False)

    def save(self, *args, **kwargs):
        customplace = None
        if not self.type or self.type == self.TYPE_IMAGE:
            customplace = self.order.customplace
            if self.is_title:
                ResultFile.objects.filter(order=self.order, is_title=True).update(is_title=False)
            else:
                qs = ResultFile.objects.filter(
                        order=self.order,
                        type=self.TYPE_IMAGE,
                        is_title=True)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
                if not qs.exists():
                    self.is_title = True
        result = super(ResultFile, self).save(*args, **kwargs)
        if customplace and self.is_title and self.bfile:
            customplace.update_title_photo(self.bfile)
        return result

    def delete(self):
        is_title = self.is_title
        order = self.order
        result = super(ResultFile, self).delete()
        if is_title:
            try:
                last_photo_result = ResultFile.objects.filter(order=order, type=self.TYPE_IMAGE). \
                                    order_by('-date_of_creation')[0]
                ResultFile.objects.filter(pk=last_photo_result.pk).update(is_title=True)
            except IndexError:
                pass
        return result

class OrderItem(OrderItemMixin, models.Model):
    order = models.ForeignKey(Order, editable=False, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name=_("Товар"), on_delete=models.CASCADE)
    quantity = models.DecimalField(_("Кол-во"), max_digits=20, decimal_places=2, default=1)
    cost = models.DecimalField(_("Цена"), max_digits=20, decimal_places=2, editable=True)
    discount = models.DecimalField(_("Скидка"), max_digits=4, decimal_places=2, editable=False, default='0.00')

    # name, description, productcategory, productcategory_name,
    # productgroup, productgroup_name, measure:
    #    содержат копии сооответствующих полей продукта в момент внесения его в заказ
    # is_wholesale_with_vat:
    #    содержит копию сооответствующего параметра лору в момент создания заказа

    name = models.CharField(_("Название"), max_length=255, editable=False)
    measure = models.CharField(_("Ед. изм."), max_length=255, default=_("шт"))
    description = models.TextField(_("Описание"), blank=True, default='')
    productcategory = models.ForeignKey(ProductCategory, verbose_name=_("Категория"),
                                        editable=False, on_delete=models.PROTECT)
    productcategory_name = models.CharField(_("Название категории"), max_length=255, editable=False)
    productgroup = models.ForeignKey(ProductGroup, verbose_name=_("Подкатегория"), null=True,
                                     editable=False, on_delete=models.PROTECT)
    productgroup_name = models.CharField(_("Название подкатегории"), max_length=255, default='', editable=False)
    productgroup_description = models.TextField(_("Описание подкатегории"), blank=True, default='', editable=False)
    comment = models.TextField(_("Комментарий"), blank=True, default='', editable=False)
    is_wholesale_with_vat = models.BooleanField(_("Цена с НДС"), default=False, editable=False)

    class Meta:
        verbose_name = _("Позиция")
        verbose_name_plural = _("Позиции")

    def __str__(self):
        return '%s - %s' % (self.order, self.product)
    
    def save(self, *args, **kwargs):
        if not self.cost:
            try:
                self.cost = self.product.price * \
                            (decimal.Decimal('100.00') - decimal.Decimal(self.discount)) / 100
            except Product.DoesNotExist:
                self.cost = 0.00
        if not self.name and self.product:
            # Доп. поля никогда не заполнялись ранее
            #
            self.name = self.product.name
            self.measure = self.product.measure
            self.description = self.product.description
            self.productcategory = self.product.productcategory
            self.productcategory_name = self.product.productcategory.name
            self.productgroup = self.product.productgroup
            self.productgroup_name = self.product.productgroup and self.product.productgroup.name or ''
            self.productgroup_description = self.product.productgroup and self.product.productgroup.description or ''
        return super(OrderItem, self).save(*args, **kwargs)

    @property
    def total(self):
        return self.cost * self.quantity

    def quantity_float(self):
        return float(self.quantity)

    def quantity_round(self):
        if self.quantity - int(self.quantity) > 0:
            return self.quantity
        else:
            return int(self.quantity)

    def discount_round(self):
        if self.discount - int(self.discount) > 0:
            return self.discount
        else:
            return int(self.discount)

class CatafalqueData(models.Model):
    order = models.OneToOneField('orders.Order', editable=False, on_delete=models.CASCADE)

    route = models.TextField(_("Маршрут"))
    start_time = models.TimeField(_("Время подачи"))
    start_place = models.TextField(_("Место подачи"), null=True)
    end_time = models.TimeField(_("Время отпуска клиентом"), null=True)
    cemetery_time = models.TimeField(_("Время заезда на кладбище"), null=True)

class AddInfoData(models.Model):
    order = models.OneToOneField('orders.Order', editable=False, on_delete=models.CASCADE)
    add_info = models.TextField(_("Доп.инфо"), blank=True)

class CoffinData(models.Model):
    order = models.OneToOneField('orders.Order', editable=False, on_delete=models.CASCADE)
    size = models.TextField(_("Размер"))

class Route(PointsModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('order', 'index', ),
        )

def recount_cost(instance, **kwargs):
    instance.order.cost = sum([i.total for i in instance.order.orderitem_set.all()], 0)
    instance.order.cost += sum([i.cost for i in instance.order.serviceitem_set.all()], 0)
    instance.order.save()
models.signals.post_save.connect(recount_cost, sender=OrderItem)
models.signals.post_delete.connect(recount_cost, sender=OrderItem)
models.signals.post_save.connect(recount_cost, sender=ServiceItem)
models.signals.post_delete.connect(recount_cost, sender=ServiceItem)
