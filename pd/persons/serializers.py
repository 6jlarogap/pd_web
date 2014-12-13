# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field, TimeField, DecimalField

from persons.models import AlivePerson, DeadPerson, Phone, CustomPlace, CustomPerson
from rest_api.fields import UnclearDateFieldSerializer, UnclearDateFieldMixin, HyperlinkedFileField

from pd.utils import CreatedAtMixin

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


class DeadPersonIdSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DeadPerson
        fields = ('id', )

class CustomPlaceListSerializer(CreatedAtMixin, serializers.HyperlinkedModelSerializer):
    titlePhoto = HyperlinkedFileField(source='title_photo')
    deadmans = DeadPersonIdSerializer(many=True, source='customperson_set')
    address = serializers.SerializerMethodField('address_func')
    location = serializers.SerializerMethodField('location_func')
    createdAt = serializers.SerializerMethodField('createdAt_func')

    class Meta:
        model = CustomPlace
        fields = ('id', 'titlePhoto', 'deadmans', 'address', 'location', 'createdAt', )

    def address_func(self, customplace):
        if customplace.address:
            address = unicode(customplace.address)
        elif customplace.place:
            address = customplace.place.address()
        else:
            address = None
        return address

    def location_func(self, customplace):
        if customplace.address:
            location = customplace.address.location_dict()
        elif customplace.place:
            location = customplace.place.location_dict()
        else:
            location = None
        return location

class CustomPlaceDetailSerializer(serializers.HyperlinkedModelSerializer):
    titlePhoto = HyperlinkedFileField(source='title_photo')
    omsData = Field(source='oms_data')
    address = Field(source='address')
    location = Field(source='location_dict')

    class Meta:
        model = CustomPlace
        fields = ('id', 'omsData', 'titlePhoto', 'address', 'location', )

class DeadPersonSerializer(serializers.HyperlinkedModelSerializer):
    birth_date = UnclearDateFieldSerializer()
    death_date = UnclearDateFieldSerializer()
    class Meta:
        model = DeadPerson
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'death_date')

class CustomPersonSerializer(UnclearDateFieldMixin, serializers.HyperlinkedModelSerializer):
    birthDate = serializers.SerializerMethodField('birth_date')
    deathDate = serializers.SerializerMethodField('death_date')
    omsData = Field('oms_data')

    class Meta:
        model = CustomPerson
        fields = ('id', 'first_name', 'last_name', 'middle_name',
                  'birthDate', 'deathDate', 'omsData',
        )

    def restore_object(self, attrs, instance=None):
        data = self.context['request'].DATA
        customplace = self.context.get('customplace')

        fields_got = dict(
            last_name=data.get('lastName'),
            first_name=data.get('firstName'),
            middle_name=data.get('middleName'),
        )
        fields = dict()
        for k in fields_got:
            if fields_got[k] is not None:
                fields[k] = fields_got[k]
        if 'birthDate' in data:
            fields['birth_date'] = self.set_unclear_date(data['birthDate'])
        if 'deathDate' in data:
            fields['death_date'] = self.set_unclear_date(data['deathDate'])
        if instance:
            for k in fields:
                setattr(instance, k, fields[k])
            return instance
        else:
            return CustomPerson(customplace=customplace, **fields)
