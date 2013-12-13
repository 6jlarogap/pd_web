# coding=utf-8

from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.fields import Field, TimeField

from orders.models import Category, Product


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    loru = Field('loru')
    price = serializers.DecimalField()
    class Meta:
        model = Product
        fields = ('id', 'loru', 'name', 'measure', 'price', 'ptype')


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    loru = Field('loru')
    category = serializers.PrimaryKeyRelatedField()
    price = serializers.DecimalField()
    class Meta:
        model = Product
        fields = ('id', 'category', 'loru', 'name', 'measure', 'price', 'ptype')
