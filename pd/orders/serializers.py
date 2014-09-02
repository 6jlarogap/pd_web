
# coding=utf-8

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field

from rest_api.fields import HyperlinkedFileField
from orders.models import ProductCategory, Product, Iorder
from users.models import Org
from users.serializers import OrgSerializer, OrgShortSerializer, OrgShort3Serializer, OrgShort4Serializer
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

class ProductEditSerializer(serializers.HyperlinkedModelSerializer):
    typeName = serializers.SerializerMethodField('typeName_func')
    categoryName = serializers.RelatedField(source='productcategory')
    measurementUnit = Field(source='measure')
    isDefault = Field(source='default')
    retailPrice = Field(source='price')
    tradePrice = Field(source='price_wholesale')
    isShownInRetailCatalog = Field(source='is_public_catalog')
    isShownInTradeCatalog = Field(source='is_wholesale')
    imageUrl = HyperlinkedFileField(source='photo')
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'sku', 'typeName', 'categoryName',
             'measurementUnit', 'isDefault',
             'retailPrice', 'tradePrice', 'isShownInRetailCatalog',
             'isShownInTradeCatalog', 'imageUrl', 
        )

    def typeName_func(self, instance):
        return instance.get_ptype_display() or None

    def restore_object(self, attrs, instance=None):
        data = self.context['request'].DATA
        image = self.context['request'].FILES.get('image')

        # В вызывающем post (добавление продукта) должны быть проверены
        # на обязательность соответствующие поля продукта
        # При правке продукта правим только то, что в полях kwargs
        # окажется None

        kwargs = dict(
            loru=self.context['request'].user.profile.org if not instance else None,
            name=data.get('name'),
            description=data.get('description'),
            measure=data.get('measurementUnit'),
            price=data.get('retailPrice'),
            price_wholesale=data.get('tradePrice'),
            ptype=data.get('typeId'),
            default=data.get('isDefault'),
            productcategory=ProductCategory.objects.get(data.get('categoryId')) if data.get('categoryId') else None,
            currency=self.context['request'].user.profile.org.currency if not instance else None,
            sku=data.get('sku'),
            is_public_catalog=data.get('isShownInRetailCatalog'),
            is_wholesale=data.get('isShownInTradeCatalog'),
        )
        for k in kwargs:
            if kwargs[k] is None:
                del kwargs[k]
        return Product(**kwargs)

    def save_object(self, obj, **kwargs):
        new_obj = obj.pk is None
        obj = obj.save(**kwargs)
        if new_obj and (not obj.sku or not obj.sku.strip()):
            obj.sku = obj.pk
            obj.save()
