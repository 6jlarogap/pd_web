
# coding=utf-8

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field

from rest_api.fields import HyperlinkedFileField
from orders.models import ProductCategory, Product, Iorder
from users.models import Org
from users.serializers import OrgSerializer, OrgShortSerializer, OrgShort3Serializer
from pd.utils import utcisoformat

class ProductCategorySerializer(serializers.HyperlinkedModelSerializer):
    icon = HyperlinkedFileField()
    
    class Meta:
        model = ProductCategory
        fields = ('id', 'name', 'icon', )

class ProductsSerializer(serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency = serializers.RelatedField(source='currency')
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
            if int(self.context['request'].GET.get('filter[components_only]', 0)):
                price = product.price_wholesale
        except (IndexError, ValueError,):
            pass
        return price

class ProductsOptSerializer(serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency = serializers.RelatedField(source='currency')
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

class ProductInfoSerializer(serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency = serializers.RelatedField(source='currency')
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
    totalPrice = serializers.Field(source='total')
    createdAt = serializers.SerializerMethodField('createdAt_func')

    class Meta:
        model = Iorder
        fields = (
            'id', 'number', 'supplier', 'customer', 'itemsCount', 'totalPrice', 'status',
            'createdAt',
        )

    def createdAt_func(self, instance):
        return utcisoformat(instance.dt_created)

class IorderInfoSerializer(serializers.HyperlinkedModelSerializer):
    products = serializers.Field(source='products_json')
    supplierId = serializers.SerializerMethodField('supplierId_func')

    class Meta:
        model = Iorder
        fields = ('products', 'comment', 'supplierId', )

    def supplierId_func(self, instance):
        return instance.supplier.pk
