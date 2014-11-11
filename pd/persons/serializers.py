# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field, TimeField, DecimalField

from persons.models import AlivePerson, DeadPerson, Phone
from rest_api.fields import UnclearDateFieldSerializer


class PhoneSerializer(serializers.HyperlinkedModelSerializer):
    #person = serializers.PrimaryKeyRelatedField()
    ct = serializers.PrimaryKeyRelatedField()
    class Meta:
        model = Phone
        fields = ('id', 'phonetype', 'number', 'ct', 'obj_id')


class AlivePersonSerializer(serializers.HyperlinkedModelSerializer):
    #address = Field(source='address_id')
    address = serializers.PrimaryKeyRelatedField()
    phones = Field(source='phones')
    address_str = Field(source='address')
    # login_phone объявлен editable=False для django форм,
    # посему здесь прописываем явно, чтоб можно было изменить
    login_phone = DecimalField(source='login_phone')
    class Meta:
        model = AlivePerson
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'address', 'phones', 'login_phone', 'address_str')


class DeadPersonSerializer(serializers.HyperlinkedModelSerializer):
    birth_date = UnclearDateFieldSerializer()
    death_date = UnclearDateFieldSerializer()
    class Meta:
        model = DeadPerson
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'death_date')

