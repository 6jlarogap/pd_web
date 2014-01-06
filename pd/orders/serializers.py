from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field

from rest_api.fields import HyperlinkedFileField
from orders.models import ProductCategory, Product


class ProductCategorySerializer(serializers.HyperlinkedModelSerializer):
    icon = HyperlinkedFileField()
    
    class Meta:
        model = ProductCategory
        fields = ('id', 'name', 'icon', )


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    photo = HyperlinkedFileField()
    currency_name = serializers.RelatedField(source='currency')
    supplier = serializers.RelatedField(source='loru')
    
    class Meta:
        model = Product
        fields = ('id', 'photo', 'measure', 'price', 'currency_name', 'sku', 'supplier', )

