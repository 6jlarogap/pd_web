
# coding=utf-8

import decimal

from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework.fields import Field

from rest_api.fields import HyperlinkedFileField
from orders.models import ProductCategory, Product, Iorder, Service, Measure, OrgService, OrgServicePrice
from users.models import Org
from users.serializers import OrgSerializer, OrgShortSerializer, OrgShort3Serializer, OrgShort4Serializer
from pd.utils import utcisoformat, str_to_bool_or_None
from pd.views import ServiceException

class ProductCurrencyMixin(object):
    def get_org_currency(self, instance):
        return instance.loru.currency

class ProductCategorySerializer(serializers.HyperlinkedModelSerializer):
    icon = HyperlinkedFileField()
    
    class Meta:
        model = ProductCategory
        fields = ('id', 'name', 'icon', )

class ProductsSerializer(ProductCurrencyMixin, serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency = serializers.SerializerMethodField('get_org_currency')
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

class ProductsOptSerializer(ProductCurrencyMixin, serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency = serializers.SerializerMethodField('get_org_currency')
    supplier = OrgShortSerializer(source='loru')
    price = Field(source = 'price_wholesale')
    category = ProductCategorySerializer(source='productcategory')
    subcategory = serializers.SerializerMethodField('subcategory_func')
    withVAT = serializers.SerializerMethodField('withVAT_func')

    class Meta:
        model = Product
        fields = ('id', 'sku', 'photo', 'slug', 'name', 'description', 'measure', 'price', 'currency',
                  'withVAT', 'category', 'subcategory', 
        )

    def subcategory_func(self, product):
        return None

    def withVAT_func(self, product):
        return self.context['is_wholesale_with_vat']

class ProductInfoSerializer(ProductCurrencyMixin, serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency = serializers.SerializerMethodField('get_org_currency')
    category = serializers.RelatedField(source='productcategory')
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

class IordersSerializer(serializers.HyperlinkedModelSerializer):
    supplier = OrgShort3Serializer(source='supplier')
    customer = OrgShort3Serializer(source='customer')
    number = serializers.Field(source='number_verbose')
    itemsCount = serializers.Field(source='items_count')
    totalPrice = serializers.Field(source='total_float')
    createdAt = serializers.SerializerMethodField('createdAt_func')

    class Meta:
        model = Iorder
        fields = (
            'id', 'number', 'supplier', 'customer', 'itemsCount', 'totalPrice', 'status',
            'createdAt', 'comment', 
        )

    def createdAt_func(self, instance):
        return utcisoformat(instance.dt_created)

class IorderInfoSerializer(serializers.HyperlinkedModelSerializer):
    products = serializers.Field(source='products_json')
    number = serializers.Field(source='number_verbose')
    supplier = OrgShort4Serializer(source='supplier')
    customer = OrgShort4Serializer(source='customer')

    class Meta:
        model = Iorder
        fields = ('products', 'comment', 'number', 'supplier', 'customer', )

class ProductEditSerializer(ProductCurrencyMixin, serializers.HyperlinkedModelSerializer):
    name = Field(source='name')
    typeId = Field(source='ptype')
    typeName = serializers.SerializerMethodField('typeName_func')
    categoryId = serializers.SerializerMethodField('categoryId_func')
    categoryName = serializers.RelatedField(source='productcategory')
    measurementUnit = Field(source='measure')
    isDefault = Field(source='default')
    retailPrice = Field(source='price')
    currency = serializers.SerializerMethodField('get_org_currency')
    tradePrice = Field(source='price_wholesale')
    isShownInRetailCatalog = Field(source='is_public_catalog')
    isShownInTradeCatalog = Field(source='is_wholesale')
    imageUrl = HyperlinkedFileField(source='photo', required=False)
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'sku',
            'typeId', 'typeName',
            'categoryId', 'categoryName',
            'measurementUnit', 'isDefault',
            'retailPrice', 'tradePrice', 'currency',
            'isShownInRetailCatalog', 'isShownInTradeCatalog',
            'imageUrl', 
        )

    def typeName_func(self, instance):
        return instance.get_ptype_display() or None

    def categoryId_func(self, instance):
        return instance.productcategory.pk

    def get_catalogs_prices(self):
        data = self.context['request'].DATA
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
        return is_public_catalog, is_wholesale, price, price_wholesale

    def restore_object(self, attrs, instance=None):
        data = self.context['request'].DATA
        image = self.context['request'].FILES.get('image')
        is_public_catalog, is_wholesale, price, price_wholesale = self.get_catalogs_prices()

        # В вызывающем post (добавление продукта) должны быть проверены
        # на обязательность соответствующие поля продукта
        # При правке продукта правим только то, что в полях kwargs
        # окажется None

        fields_got = dict(
            loru=self.context['request'].user.profile.org if not instance else None,
            name=data.get('name'),
            description=data.get('description'),
            measure=data.get('measurementUnit'),
            price=price,
            price_wholesale=price_wholesale,
            ptype=data.get('typeId'),
            default=str_to_bool_or_None(data.get('isDefault')),
            productcategory=ProductCategory.objects.get(pk=data.get('categoryId')) if data.get('categoryId') else None,
            sku=data.get('sku'),
            is_public_catalog=is_public_catalog,
            is_wholesale=is_wholesale,
            photo=image if image else None,
        )
        fields = dict()
        for k in fields_got:
            if fields_got[k] is not None:
                fields[k] = fields_got[k]
        if instance:
            for k in fields:
                setattr(instance, k, fields[k])
            return instance
        else:
            fields['price'] = fields.get('price', 0)
            fields['price_wholesale'] = fields.get('price_wholesale', 0)
            return Product(**fields)

    def is_valid(self):
        message = ''
        valid = True
        try:
            is_public_catalog, is_wholesale, price, price_wholesale = self.get_catalogs_prices()
        except ServiceException as excpt:
            message = excpt.message
            valid = False
        else:
            valid = not self.errors
            if self.object:
                is_public_catalog = self.object.is_public_catalog if is_public_catalog is None else is_public_catalog
                is_wholesale = self.object.is_wholesale if is_wholesale is None else is_wholesale
                price = self.object.price if price is None else price
                price_wholesale = self.object.price_wholesale if price_wholesale is None else price_wholesale
            else:
                price = price or 0
                price_wholesale = price_wholesale or 0
            if is_public_catalog and price <= 0:
                message = _(u'Не задана или неверна розничная цена при помещении товара/услуги в публичный каталог')
            elif is_wholesale and price_wholesale <= 0:
                message = _(u'Не задана или неверна оптовая цена при помещении товара/услуги в оптовый каталог')
        if message:
            self._errors = self._errors or {}
            self._errors.update(dict(
                status='error',
                message=message,
            ))
            valid = False
        return valid

    @transaction.commit_on_success
    def save_object(self, obj, **kwargs):
        new_obj = obj.pk is None
        obj.save(**kwargs)
        if new_obj and (not obj.sku or not obj.sku.strip()):
            obj.sku = obj.pk
            obj.save()

class MeasureSerializer(serializers.ModelSerializer):

    class Meta:
        model = Measure
        fields = ('name', 'title', )

class ServiceSerializer(serializers.ModelSerializer):
    type = Field(source='name')
    measures = MeasureSerializer(many=True, source='measure_set')

    class Meta:
        model = Service
        fields = ('type', 'title', 'description', 'measures', )

class OrgServicePriceSerializer(serializers.ModelSerializer):
    name = serializers.Field(source='measure_name')
    price = serializers.Field(source='price_float')

    class Meta:
        model = OrgServicePrice
        fields = ('name', 'price', )

class OrgServiceSerializer(serializers.ModelSerializer):
    type = serializers.Field(source='service_name')
    isActive = serializers.Field(source='enabled')
    measures = OrgServicePriceSerializer(many=True, source='orgserviceprice_set')
    
    class Meta:
        model = OrgService
        fields = ('type', 'isActive', 'measures', )
