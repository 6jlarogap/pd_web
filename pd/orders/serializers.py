from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field

from rest_api.fields import HyperlinkedFileField
from orders.models import ProductCategory, Product
from users.models import Org


class ProductCategorySerializer(serializers.HyperlinkedModelSerializer):
    icon = HyperlinkedFileField()
    
    class Meta:
        model = ProductCategory
        fields = ('id', 'name', 'icon', )


class ProductsSerializer(serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency = serializers.RelatedField(source='currency')
    supplier = serializers.RelatedField(source='loru')
    
    class Meta:
        model = Product
        fields = ('id', 'photo', 'measure', 'price', 'currency', 'sku', 'supplier', )


class SupplierSerializer(serializers.HyperlinkedModelSerializer):
    address = serializers.RelatedField(source='off_address')
    phone = Field(source='phones')
    
    class Meta:
        model = Org
        fields = ('id', 'name', 'address', 'phone', 'worktime', 'site', )


class ProductInfoSerializer(serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency = serializers.RelatedField(source='currency')
    productcategory_name = serializers.RelatedField(source='productcategory')
    supplier = SupplierSerializer(source='loru')
    
    class Meta:
        model = Product
        fields = ('id', 'photo', 'price', 'currency', 'sku', 'productcategory_name', 'supplier', )

