
# coding=utf-8

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field

from rest_api.fields import HyperlinkedFileField
from orders.models import ProductCategory, Product
from users.models import Org
from users.serializers import OrgSerializer, OrgShortSerializer


class ProductCategorySerializer(serializers.HyperlinkedModelSerializer):
    icon = HyperlinkedFileField()
    
    class Meta:
        model = ProductCategory
        fields = ('id', 'name', 'icon', )


class ProductsSerializer(serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency = serializers.RelatedField(source='currency')
    supplier = OrgShortSerializer(source='loru')
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'photo', 'measure', 'price', 'currency',
                  'sku', 'supplier', 'slug',
        )

class ProductInfoSerializer(serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency = serializers.RelatedField(source='currency')
    category = serializers.RelatedField(source='productcategory')
    supplier = OrgSerializer(source='loru')
    model3d = serializers.SerializerMethodField('model3d_func')
    
    class Meta:
        model = Product
        fields = ('id', 'photo', 'price', 'currency', 'name', 'description', 'sku', 'category',
                  'supplier', 'model3d', 'slug',
        )

    def model3d_func(self, obj):
        return None
