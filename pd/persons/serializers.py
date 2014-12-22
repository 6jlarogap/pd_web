# -*- coding: utf-8 -*-
import re

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field, TimeField, DecimalField

from geo.models import Location
from persons.models import AlivePerson, DeadPerson, Phone, CustomPlace, CustomPerson, \
                           IDDocumentType, DocumentSource, PersonID, \
                           DeathCertificate, DeathCertificateScan
from rest_api.fields import UnclearDateFieldSerializer, UnclearDateFieldMixin, UnclearDateFieldSafeSerializer, \
                            HyperlinkedFileField

from pd.utils import CreatedAtMixin
from pd.serializers import ArchFilesSerializer

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


class CustomPlaceListSerializer(CreatedAtMixin, serializers.HyperlinkedModelSerializer):
    titlePhoto = HyperlinkedFileField(source='title_photo')
    deadmans = serializers.SerializerMethodField('deadmans_func')
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

    def deadmans_func(self, customplace):
        return [ customperson.pk for customperson in CustomPerson.objects.filter(
            customplace=customplace,
        )]

class CustomPlaceEditSerializer(serializers.HyperlinkedModelSerializer):
    address = Field(source='address')
    location = Field(source='location_dict')

    class Meta:
        model = CustomPlace
        fields = ('id', 'address', 'location', )

    def restore_object(self, attrs, instance=None):
        data = self.context['request'].DATA

        address=data.get('address')
        location=data.get('location')
        l = None
        if address or location:
            if instance and instance.address:
                l = instance.address 
            else:
                l = Location()
            if address:
                l.addr_str = address
            if location:
                l.gps_x = location.get("longitude")
                l.gps_y = location.get("latitude")
            l.save()
        if instance:
            return instance
        else:
            return CustomPlace(
                user=self.context['request'].user,
                address=l,
            )

class CustomPlaceDetailSerializer(CustomPlaceEditSerializer):
    titlePhoto = HyperlinkedFileField(source='title_photo')
    omsData = Field(source='oms_data')

    class Meta:
        model = CustomPlace
        fields = ('id', 'omsData', 'titlePhoto', 'address', 'location', )

class DeadPersonSerializer(serializers.HyperlinkedModelSerializer):
    birth_date = UnclearDateFieldSerializer()
    death_date = UnclearDateFieldSerializer()
    class Meta:
        model = DeadPerson
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'death_date')

class BaseCustomPersonSerializer(UnclearDateFieldMixin, serializers.HyperlinkedModelSerializer):
    birthDate = serializers.SerializerMethodField('birth_date')
    deathDate = serializers.SerializerMethodField('death_date')
    lastName = Field(source='last_name')
    firstName = Field(source='first_name')
    middleName = Field(source='middle_name')

class CustomPersonSerializer(BaseCustomPersonSerializer):
    omsData = Field(source='oms_data')

    class Meta:
        model = CustomPerson
        fields = ('id', 'firstName', 'lastName', 'middleName',
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

class CustomPerson2Serializer(BaseCustomPersonSerializer):
    grave = serializers.SerializerMethodField('grave_func')

    class Meta:
        model = CustomPerson
        fields = ('id', 'firstName', 'lastName', 'middleName',
                  'birthDate', 'deathDate', 'grave'
        )

    def grave_func(self, customperson):
        try:
            return customperson.person.deadperson.burial_set.all()[0].grave_number
        except (AttributeError, DeadPerson.DoesNotExist, IndexError,):
            return None

class ArchIDDocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDDocumentType
        fields = ('id', 'name', )

class ArchDocumentSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentSource
        fields = ('id', 'name', )

class ArchPersonIDSerializer(serializers.ModelSerializer):
    person_id = serializers.Field('person.id')
    id_type_id = serializers.Field('id_type.id')
    source_id = serializers.Field('source.id')

    class Meta:
        model = PersonID
        fields = ('id', 'person_id', 'id_type_id', 'series', 'number', 'source_id', 'date')

class ArchPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phone
        fields = ('phonetype', 'number',)

class ArchAlivePersonSerializer(serializers.ModelSerializer):
    address_id = serializers.Field('address.id')
    user_id = serializers.Field('user.id')
    birth_date = UnclearDateFieldSafeSerializer()
    phones = serializers.SerializerMethodField('phones_func')

    class Meta:
        model = AlivePerson
        fields = (
            'id', 'last_name', 'first_name', 'middle_name', 'birth_date',
            'address_id', 'phones',
            # 'user_id' # расшифровку пользователя-кабинетчика не даем в ОМС.
            #             Кабинетчик мог их поменять, а эти изменения волновать
            #             ОМС не должны
            'login_phone',
        )

    def phones_func(self, aliveperson):
        phones = list()
        if hasattr(aliveperson, 'phones') and aliveperson.phones:
            for phone in re.split(r'[,;\n]+', aliveperson.phones):
                phone = re.sub(r'[-\s]+', '', phone)
                if re.match(r'^\d{5,}$', phone):
                    phones.append(dict(
                        phonetype=Phone.PHONE_TYPE_OTHER,
                        number=phone,
                    ))
        for phone in aliveperson.phone_set.all():
            phones.append(ArchPhoneSerializer(phone).data)
        return phones

class ArchDeathCertificateSerializer(serializers.ModelSerializer):
    deadperson_id = serializers.Field('person.id')
    zags_id = serializers.Field('zags.id')

    class Meta:
        model = DeathCertificate
        fields = ('id', 'deadperson_id', 's_number', 'release_date', 'zags_id')

class ArchDeathCertificateScanSerializer(ArchFilesSerializer):
    deathcertificate_id = serializers.Field('deathcertificate.id')

    class Meta:
        model = DeathCertificateScan
        fields = ('id', 'deathcertificate_id',
                  'bfile', 'comment', 'original_name', 'comment', 'creator_id', 'date_of_creation', )

class ArchDeadPersonSerializer(serializers.ModelSerializer):
    birth_date = UnclearDateFieldSafeSerializer()
    death_date = UnclearDateFieldSafeSerializer()
    address_id = serializers.Field('address.id')

    class Meta:
        model = DeadPerson
        fields = (
            'id', 'last_name', 'first_name', 'middle_name', 'birth_date', 'death_date', 'address_id',
        )

