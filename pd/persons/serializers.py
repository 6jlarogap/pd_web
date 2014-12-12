# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field, TimeField, DecimalField

from persons.models import AlivePerson, DeadPerson, Phone, CustomPlace, CustomPerson
from rest_api.fields import UnclearDateFieldSerializer, UnclearDateFieldMixin


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


class CustomPlaceSerializer(serializers.HyperlinkedModelSerializer):
    titlePhoto = serializers.SerializerMethodField('titlePhoto_func')
    omsData = serializers.SerializerMethodField('omsData_func')
    address = Field(source='address')
    location = Field(source='location_dict')

    class Meta:
        model = CustomPlace
        fields = ('id', 'omsData', 'titlePhoto', 'address', 'location', )

    def titlePhoto_func(self, customplace):
        return customplace.title_photo(self.context['request'])

    def omsData_func(self, customplace):
        place = customplace.place
        if place:
            return dict(
                address=place.address(),
                location=place.location_dict(),
            )
        else:
            return None

class DeadPersonSerializer(serializers.HyperlinkedModelSerializer):
    birth_date = UnclearDateFieldSerializer()
    death_date = UnclearDateFieldSerializer()
    class Meta:
        model = DeadPerson
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'death_date')

class CustomPersonSerializer(UnclearDateFieldMixin, serializers.HyperlinkedModelSerializer):
    birthDate = serializers.SerializerMethodField('birth_date')
    deathDate = serializers.SerializerMethodField('death_date')
    fio = Field(source='full_human_name')
    graveNumber = serializers.SerializerMethodField('graveNumber_func')

    class Meta:
        model = CustomPerson
        fields = ('id', 'fio', 'first_name', 'last_name', 'middle_name',
                  'birthDate', 'deathDate', 'graveNumber',
        )

    def graveNumber_func(self, customperson):
        result = None
        try:
            return customperson.person.deadperson.burial_set.all()[0].grave_number
        except (AttributeError, DeadPerson.DoesNotExist,):
            pass
        return

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
