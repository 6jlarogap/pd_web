
# coding=utf-8

import decimal

from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework import serializers

from rest_api.fields import HyperlinkedFileField
from orders.models import Order, ProductCategory, Product, Service, Measure, OrgService, OrgServicePrice, \
                          OrderItem, ServiceItem, OrderComment, ResultFile
from persons.models import OrderDeadPerson
from persons.serializers import AlivePerson2Serializer, DeadPerson3Serializer
from burials.models import OrderPlace
from burials.serializers import OrderPlaceSerializer
from users.models import Org, is_cabinet_user, is_trade_user, UserPhoto
from users.serializers import OrgSerializer, OrgShortSerializer, OrgShort3Serializer, OrgShort4Serializer, \
                              OrgShort6Serializer, UserFioSerializer
from pd.utils import utcisoformat, str_to_bool_or_None, CreatedAtMixin, RestoreObjectMixin
from pd.views import ServiceException

class CurrencyCodeMixin(object):

    def currency_code(self, instance):
        """
        Currency code for Product or OrderItem
        """
        result = ''
        if instance:
            o = instance.order if hasattr(instance, 'order') else instance
            if o and o.loru and o.loru.currency:
                result = o.loru.currency.code
        return result

class ProductCategorySerializer(serializers.ModelSerializer):
    icon = HyperlinkedFileField(read_only=True)

    class Meta:
        model = ProductCategory
        fields = ('id', 'name', 'icon', )

class ProductCategory2Serializer(serializers.ModelSerializer):
    title = serializers.CharField(source='name')
    products = serializers.SerializerMethodField('products_func')

    class Meta:
        model = ProductCategory
        fields = ('id', 'title', 'products' )

    def products_func(self, category):
        return [ dict(id=product.pk, title=product.name, price=product.price) \
            for product in Product.objects.filter(
                    productcategory=category,
                    loru=self.context['request'].user.profile.org,
                    is_archived=False,
                )
        ]

class ProductsSerializer(CurrencyCodeMixin, serializers.ModelSerializer):
    photo = HyperlinkedFileField(read_only=True)
    currency = serializers.SerializerMethodField('currency_code')
    supplier = OrgShortSerializer(source='loru')
    price = serializers.SerializerMethodField('price_func')

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'photo', 'measure', 'price', 'currency',
                  'sku', 'supplier', 'slug',
        )

    def price_func(self, product):
        price = product.price
        try:
            if self.context['request'].GET.get('filter[productType]', '').lower() == 'opt':
                price = product.price_wholesale
        except (AttributeError, KeyError,):
            pass
        return price

class ProductShortSerializer(serializers.ModelSerializer):
    imageUrl = HyperlinkedFileField(source='photo', read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'imageUrl',)

class ProductsOptSerializer(CurrencyCodeMixin, serializers.ModelSerializer):
    photo = HyperlinkedFileField(read_only=True)
    currency = serializers.SerializerMethodField('currency_code')
    supplier = OrgShortSerializer(source='loru')
    price = serializers.DecimalField(20, 2, source = 'price_wholesale')
    category = ProductCategorySerializer(source='productcategory')
    subcategory = serializers.SerializerMethodField('subcategory_func')
    withVAT = serializers.SerializerMethodField('withVAT_func')

    class Meta:
        model = Product
        fields = ('id', 'sku', 'photo', 'slug', 'name', 'description', 'measure', 'price', 'currency',
                  'withVAT', 'category', 'subcategory', 'supplier',
        )

    def subcategory_func(self, product):
        return None

    def withVAT_func(self, product):
        return self.context['is_wholesale_with_vat']

class ProductInfoSerializer(CurrencyCodeMixin, serializers.ModelSerializer):
    photo = HyperlinkedFileField(read_only=True)
    currency = serializers.SerializerMethodField('currency_code')
    category = serializers.StringRelatedField(source='productcategory', read_only=True)
    supplier = OrgSerializer(source='loru')
    priceWholesale = serializers.SerializerMethodField('price_wholesale_func')
    model3d = serializers.SerializerMethodField('model3d_func')
    
    class Meta:
        model = Product
        fields = ('id', 'photo', 'price', 'priceWholesale',
                  'currency', 'name', 'description', 'sku', 'category',
                  'supplier', 'model3d', 'slug',
        )

    def price_wholesale_func(self, product):
        return product.price_wholesale if self.context.get('show_wholesale') else None

    def model3d_func(self, product):
        return None

class OptOrdersSerializer(CreatedAtMixin, serializers.ModelSerializer):
    supplier = OrgShort3Serializer(source='loru')
    customer = OrgShort3Serializer(source='applicant_organization')
    number = serializers.ReadOnlyField(source='number_verbose')
    itemsCount = serializers.ReadOnlyField(source='item_count')
    totalPrice = serializers.ReadOnlyField(source='total_float')
    createdAt = serializers.SerializerMethodField('createdAt_func')
    comment = serializers.ReadOnlyField(source='first_comment')

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'supplier', 'customer', 'itemsCount', 'totalPrice', 'status',
            'createdAt', 'comment', 
        )

class OptOrderInfoSerializer(serializers.ModelSerializer):
    products = serializers.ReadOnlyField(source='products_json')
    number = serializers.ReadOnlyField(source='number_verbose')
    supplier = OrgShort4Serializer(source='loru')
    customer = OrgShort4Serializer(source='applicant_organization')
    comment = serializers.ReadOnlyField(source='first_comment')

    class Meta:
        model = Order
        fields = ('products', 'comment', 'number', 'supplier', 'customer', )

class ProductEditSerializer(RestoreObjectMixin, CurrencyCodeMixin, serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    typeId = serializers.CharField(source='ptype', required=False)
    typeName = serializers.SerializerMethodField('typeName_func')
    categoryId = serializers.SerializerMethodField('categoryId_func')
    categoryName = serializers.StringRelatedField(source='productcategory', read_only=True)
    measurementUnit = serializers.CharField(source='measure', required=False)
    isDefault = serializers.BooleanField(source='default', required=False)
    isArchived = serializers.BooleanField(source='is_archived', required=False)
    retailPrice = serializers.DecimalField(20, 2, source='price', required=False)
    tradePrice = serializers.DecimalField(20, 2, source='price_wholesale', required=False)
    currency = serializers.SerializerMethodField('currency_code')
    isShownInRetailCatalog = serializers.BooleanField(source='is_public_catalog', required=False)
    isShownInTradeCatalog = serializers.BooleanField(source='is_wholesale', required=False)
    imageUrl = HyperlinkedFileField(source='photo', read_only=True)
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'sku',
            'typeId', 'typeName',
            'categoryId', 'categoryName',
            'measurementUnit', 'isDefault', 'stockable', 'isArchived',
            'retailPrice', 'tradePrice', 'currency',
            'isShownInRetailCatalog', 'isShownInTradeCatalog',
            'imageUrl',
        )

    def typeName_func(self, instance):
        return instance.get_ptype_display() or None

    def categoryId_func(self, instance):
        return instance.productcategory.pk

    def get_catalogs_prices(self, instance):
        data = self.context['request'].data
        is_public_catalog = str_to_bool_or_None(data.get('isShownInRetailCatalog'))
        is_wholesale = str_to_bool_or_None(data.get('isShownInTradeCatalog'))
        price = data.get('retailPrice')
        if price is not None:
            try:
                price = decimal.Decimal(price)
            except decimal.InvalidOperation:
                raise ServiceException(_(u'Неверно задана розничная цена'))
        price_wholesale = data.get('tradePrice')
        if price_wholesale is not None:
            try:
                price_wholesale = decimal.Decimal(price_wholesale)
            except decimal.InvalidOperation:
                raise ServiceException(_(u'Неверно задана оптовая цена'))
        if instance:
            is_public_catalog = instance.is_public_catalog if is_public_catalog is None else is_public_catalog
            is_wholesale = instance.is_wholesale if is_wholesale is None else is_wholesale
            price = instance.price if price is None else price
            price_wholesale = instance.price_wholesale if price_wholesale is None else price_wholesale
        else:
            price = price or 0
            price_wholesale = price_wholesale or 0
        if is_public_catalog and price <= 0:
            raise ServiceException(_(u'Не задана или неверна розничная цена при помещении товара/услуги в публичный каталог'))
        elif is_wholesale and price_wholesale <= 0:
            raise ServiceException(_(u'Не задана или неверна оптовая цена при помещении товара/услуги в оптовый каталог'))
        return is_public_catalog, is_wholesale, price, price_wholesale

    def restore_object_(self, instance=None, validated_data=[]):
        data = self.context['request'].data
        image = self.context['request'].data.get('image')
        is_public_catalog, is_wholesale, price, price_wholesale = self.get_catalogs_prices(instance)

        # В вызывающем post (добавление продукта) должны быть проверены
        # на обязательность соответствующие поля продукта
        # При правке продукта правим только то, что в полях kwargs
        # окажется None

        stockable = str_to_bool_or_None(data.get('stockable'))
        if stockable is None:
            if instance:
                stockable = instance.stockable
            else:
                stockable = True

        is_archived = str_to_bool_or_None(data.get('isArchived'))
        if is_archived is None:
            if instance:
                is_archived = instance.is_archived
            else:
                is_archived = False
        fields_got = dict(
            loru=self.context['request'].user.profile.org if not instance else None,
            name=data.get('name'),
            description=data.get('description'),
            measure=data.get('measurementUnit'),
            price=price,
            price_wholesale=price_wholesale,
            ptype=data.get('typeId'),
            default=str_to_bool_or_None(data.get('isDefault')),
            stockable=stockable,
            productcategory=ProductCategory.objects.get(pk=data.get('categoryId')) if data.get('categoryId') else None,
            sku=data.get('sku'),
            is_public_catalog=is_public_catalog,
            is_wholesale=is_wholesale,
            is_archived=is_archived,
            photo=image if image else None,
        )
        fields = dict()
        for k in fields_got:
            if fields_got[k] is not None:
                fields[k] = fields_got[k]
        if not fields_got['ptype'] or fields_got['ptype'] == 'null':
            fields['ptype'] = None
        if instance:
            for k in fields:
                setattr(instance, k, fields[k])
            return instance
        else:
            fields['price'] = fields.get('price', 0)
            fields['price_wholesale'] = fields.get('price_wholesale', 0)
            return Product(**fields)

class MeasureSerializer(serializers.ModelSerializer):

    class Meta:
        model = Measure
        fields = ('name', 'title', )

class ServiceSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='name')
    measures = MeasureSerializer(many=True, source='measure_set')

    class Meta:
        model = Service
        fields = ('type', 'title', 'description', 'measures', )

class OrgServicePriceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='measure_name')
    price = serializers.ReadOnlyField(source='price_float')

    class Meta:
        model = OrgServicePrice
        fields = ('name', 'price', )

class OrgServiceSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='service_name')
    isActive = serializers.BooleanField(source='enabled')
    measures = OrgServicePriceSerializer(many=True, source='orgserviceprice_set')
    
    class Meta:
        model = OrgService
        fields = ('type', 'isActive', 'measures', )

class ServiceOrderSerializer(CreatedAtMixin, CurrencyCodeMixin, serializers.ModelSerializer):
    type = serializers.ReadOnlyField(source='service_name')
    location = serializers.ReadOnlyField(source='customer_location')
    performer = OrgShort3Serializer(source='loru')
    owner = serializers.SerializerMethodField('owner_func')
    number = serializers.ReadOnlyField(source='number_verbose')
    totalPrice = serializers.ReadOnlyField(source='total_float')
    currency = serializers.SerializerMethodField('currency_code')
    createdAt = serializers.SerializerMethodField('createdAt_func')
    modifiedAt = serializers.SerializerMethodField('modifiedAt_func')
    isArchived = serializers.BooleanField(source='archived')
    titlePhoto = HyperlinkedFileField(source='title_photo', required=False)

    class Meta:
        model = Order
        fields = ('id', 'type', 'performer', 'owner', 'number', 'status', 'isArchived',
                  'totalPrice', 'currency', 'createdAt', 'modifiedAt',
                  'titlePhoto', 'location',
        )
    def owner_func(self, instance):
        result = None
        if instance.customplace and instance.customplace.user:
            return UserFioSerializer(instance.customplace.user).data
        return result

class LoruOrderSerializer(CreatedAtMixin, CurrencyCodeMixin, serializers.ModelSerializer):
    number = serializers.ReadOnlyField(source='number_verbose')
    createdDate = serializers.DateField(source='dt', format="%d.%m.%Y")
    dueDate = serializers.DateField(source='dt_due', format="%d.%m.%Y")
    customer = AlivePerson2Serializer(source='applicant')
    deadman = serializers.SerializerMethodField('deadman_func')
    place = serializers.SerializerMethodField('place_func')
    createdAt = serializers.SerializerMethodField('createdAt_func')
    modifiedAt = serializers.SerializerMethodField('modifiedAt_func')
    totalPrice = serializers.ReadOnlyField(source='total_float')
    currency = serializers.SerializerMethodField('currency_code')
    products = serializers.SerializerMethodField('products_func')
    burialPlanTime = serializers.TimeField(source='burial_plan_time', format='%H:%M')
    initialTime = serializers.TimeField(source='initial_time', format='%H:%M')
    serviceTime = serializers.TimeField(source='service_time', format='%H:%M')
    repastTime = serializers.TimeField(source='repast_time', format='%H:%M')
    initialPlace = serializers.CharField(source='initial_place')
    servicePlace = serializers.CharField(source='service_place')
    repastPlace = serializers.CharField(source='repast_place')

    class Meta:
        model = Order
        fields = ('id', 'number', 'createdDate', 'dueDate',
                  'customer', 'deadman', 'place', 'products',
                  'createdAt', 'modifiedAt', 'totalPrice', 'currency',
                  'burialPlanTime', 'initialTime', 'serviceTime', 'repastTime',
                  'initialPlace', 'servicePlace', 'repastPlace',
        )

    def deadman_func(self, instance):
        deadman = None
        try:
            deadman = instance.orderdeadperson
        except OrderDeadPerson.DoesNotExist:
             deadman = instance.burial and instance.burial.deadman
        return deadman and DeadPerson3Serializer(deadman).data
        
    def place_func(self, instance):
        try:
            orderplace = instance.orderplace
        except (OrderPlace.DoesNotExist, AttributeError,):
            return None
        return OrderPlaceSerializer(orderplace).data

    def products_func(self, instance):
        return [
            {
                'id': orderitem.product.pk,
                'title': orderitem.product.name,
                'price': orderitem.product.price,
                'amount': orderitem.quantity_round(),
                'discount': orderitem.discount_round(),
            } \
            for orderitem in OrderItem.objects.filter(order=instance).order_by('pk')
        ]

class OrderSerializer(CreatedAtMixin, serializers.ModelSerializer):
    type = serializers.ReadOnlyField(source='service_name')
    createdAt = serializers.SerializerMethodField('createdAt_func')
    modifiedAt = serializers.SerializerMethodField('modifiedAt_func')
    number = serializers.ReadOnlyField(source='number_verbose')
    performer = OrgShort6Serializer(source='loru')

    class Meta:
        model = Order
        fields = (
            'id', 'type', 'createdAt', 'modifiedAt', 'number', 'status',
            'performer',
        )

class OrderCommentsSerializer(CreatedAtMixin, serializers.ModelSerializer):
    createdAt = serializers.SerializerMethodField('createdAt_func')
    user = serializers.SerializerMethodField('user_func')

    class Meta:
        model = OrderComment
        fields = ('id', 'comment', 'createdAt', 'user', )

    def user_func(self, instance):
        request = self.context['request']
        try:
            userphoto = UserPhoto.objects.get(user=instance.user)
            avatarUrl = request.build_absolute_uri(userphoto.bfile.url)
        except UserPhoto.DoesNotExist:
            avatarUrl = None
        data = dict(
            id=instance.user.pk,
            avatarUrl=avatarUrl,
        )
        if is_cabinet_user(instance.user):
            data.update(dict(
                username=instance.user.customerprofile.full_name(put_middle_name=False),
                organisation=None,
            ))
        if is_trade_user(instance.user):
            data.update(dict(
                username=instance.user.profile.full_name(put_middle_name=False),
                organisation=instance.user.profile.org.name,
            ))
        return data

class OrderResultsSerializer(serializers.ModelSerializer):
    fileUrl = HyperlinkedFileField(source='bfile', required=False)
    createdAt = serializers.SerializerMethodField('createdAt_func')
    isTitle = serializers.BooleanField(source='is_title')

    class Meta:
        model = ResultFile
        fields = ('id', 'fileUrl', 'type', 'createdAt', 'isTitle',)

    def createdAt_func(self, instance):
        return utcisoformat(instance.date_of_creation)

class OrderItemSerializer(CurrencyCodeMixin, serializers.ModelSerializer):
    productId = serializers.PrimaryKeyRelatedField(source='product', read_only=True)
    price = serializers.ReadOnlyField(source='cost_float')
    quantity = serializers.ReadOnlyField(source='quantity_float')
    currency = serializers.SerializerMethodField('currency_code')
    product = serializers.SerializerMethodField('product_func')

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'price', 'quantity', 'currency', 'productId', )

    def product_func(self, orderitem):
        product = orderitem.product
        request = self.context['request']
        return ProductShortSerializer(
            product,
            context=dict(request=request)).data

class ServiceItemSerializer(CurrencyCodeMixin, serializers.ModelSerializer):
    type = serializers.CharField(source='orgservice.service.name')
    title = serializers.CharField(source='orgservice.service.title')
    price = serializers.ReadOnlyField(source='cost_float')
    currency = serializers.SerializerMethodField('currency_code')

    class Meta:
        model = ServiceItem
        fields = ('id', 'type', 'title', 'price', 'currency',)

class ServiceOrderDetailSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='service_name')
    supplierId = serializers.PrimaryKeyRelatedField(source='loru', read_only=True)
    placeId = serializers.PrimaryKeyRelatedField(source='customplace', read_only=True)
    number = serializers.ReadOnlyField(source='number_verbose')
    isArchived = serializers.BooleanField(source='archived')
    clientRating = serializers.NullBooleanField(source='applicant_approved')
    services = ServiceItemSerializer(many=True, source='serviceitem_set')
    products = serializers.SerializerMethodField('products_func')

    class Meta:
        model = Order
        fields = (
            'id', 'supplierId', 'number', 'type', 'placeId', 'status', 'isArchived',
            'clientRating', 'services', 'products',
        )

    def products_func(self, order):
        return [ OrderItemSerializer(
            item,
            context=dict(request=self.context['request']),
        ).data for item in order.orderitem_set.all()
        ]
