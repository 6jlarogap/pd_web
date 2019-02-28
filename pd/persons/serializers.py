# -*- coding: utf-8 -*-
import re

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from geo.models import Location
from persons.models import AlivePerson, DeadPerson, Phone, CustomPlace, CustomPerson, \
                           MemoryGallery, IDDocumentType, DocumentSource, PersonID, \
                           DeathCertificate, DeathCertificateScan, \
                           CustomPersonPermission, MemoryGalleryPermission
from users.models import get_profile
from users.serializers import OrgShort6Serializer, UserProfileMixin
from rest_api.fields import UnclearDateFieldSerializer, UnclearDateFieldMixin, UnclearDateFieldSafeSerializer, \
                            HyperlinkedFileField

from pd.utils import CreatedAtMixin, utcisoformat, str_to_bool_or_None, capitalize, RestoreObjectMixin

class PhoneSerializer(serializers.ModelSerializer):
    #person = serializers.PrimaryKeyRelatedField()
    ct = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all())
    class Meta:
        model = Phone
        fields = ('id', 'phonetype', 'number', 'ct', 'obj_id')


class AlivePersonSerializer(serializers.ModelSerializer):
    address = serializers.PrimaryKeyRelatedField(read_only=True)
    address_str = serializers.StringRelatedField(source='address', read_only=True)
    # login_phone объявлен editable=False для django форм,
    # посему здесь прописываем явно, чтоб можно было изменить
    login_phone = serializers.DecimalField(15, 0, allow_null=True)
    is_inbook = serializers.BooleanField()

    class Meta:
        model = AlivePerson
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'address', 'phones', 'login_phone', 'address_str', 'is_inbook')


class AlivePerson2Serializer(serializers.ModelSerializer):
    lastName = serializers.CharField(source='last_name')
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    middleName = serializers.CharField(source='middle_name', required=False, allow_blank=True)
    address = serializers.StringRelatedField(read_only=True)
    phoneNumber = serializers.CharField(source='phones')

    class Meta:
        model = AlivePerson
        fields = ('id', 'firstName', 'lastName', 'middleName', 'address', 'phoneNumber',)


class CustomPlaceListSerializer(CreatedAtMixin, serializers.ModelSerializer):
    titlePhoto = HyperlinkedFileField(source='title_photo', read_only=True)
    deadmans = serializers.SerializerMethodField('deadmans_func')
    address = serializers.SerializerMethodField('address_func')
    location = serializers.SerializerMethodField('location_func')
    createdAt = serializers.SerializerMethodField('createdAt_func')

    class Meta:
        model = CustomPlace
        fields = ('id', 'name', 'titlePhoto', 'deadmans', 'address', 'location', 'createdAt', 'comment',)

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

class CustomPlaceEditSerializer(RestoreObjectMixin, serializers.ModelSerializer):
    location = serializers.ReadOnlyField(source='location_dict')
    performerId = serializers.PrimaryKeyRelatedField(source='favorite_performer', read_only=True)
    address = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CustomPlace
        fields = ('id', 'name', 'address', 'location', 'performerId', 'comment')

    def restore_object_(self, instance=None, validated_data=[]):
        data = self.context['request'].data

        name = data.get('name')
        address = data.get('address')
        location = data.get('location')
        comment = data.get('comment')
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
            if name is not None:
                instance.name = name
            if comment is not None:
                instance.comment = comment
            if 'favorite_performer' in self.context:
                instance.favorite_performer = self.context['favorite_performer']
            return instance
        else:
            return CustomPlace(
                name = name or '',
                user=self.context['request'].user,
                address=l,
                comment=comment,
            )

class CustomPlaceDetailSerializer(CustomPlaceEditSerializer):
    titlePhoto = HyperlinkedFileField(source='title_photo', read_only=True)
    omsData = serializers.ReadOnlyField(source='oms_data')
    performer = OrgShort6Serializer(source='favorite_performer')

    class Meta:
        model = CustomPlace
        fields = (
            'id', 'name', 'omsData', 'titlePhoto', 'address', 'location',
            'performer', 'comment',
        )

class DeadPersonSerializer(serializers.ModelSerializer):
    birth_date = UnclearDateFieldSerializer(required=False, allow_null=True)
    death_date = UnclearDateFieldSerializer(required=False, allow_null=True)
    class Meta:
        model = DeadPerson
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'death_date')

class DeadPerson2Serializer(
    UnclearDateFieldMixin,
    RestoreObjectMixin,
    serializers.ModelSerializer
    ):
    birthDate = UnclearDateFieldSerializer(source='birth_date', required=False, allow_null=True)
    deathDate = UnclearDateFieldSerializer(source='death_date', required=False, allow_null=True)
    lastName = serializers.CharField(source='last_name')
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    middleName = serializers.CharField(source='middle_name', required=False, allow_blank=True)

    class Meta:
        model = DeadPerson
        fields = ('id', 'firstName', 'lastName', 'middleName', 'birthDate', 'deathDate')

    def restore_object_(self, instance=None, validated_data=[]):
        data = self.context['request'].data

        fields_got = dict(
            last_name=data.get('lastName'),
            first_name=data.get('firstName'),
            middle_name=data.get('middleName'),
        )
        fields = dict()
        for k in fields_got:
            if fields_got[k] is not None:
                fields[k] = capitalize(fields_got[k])
        if 'birthDate' in data:
            fields['birth_date'] = self.set_unclear_date(data['birthDate'], format='d.m.y')
        if 'deathDate' in data:
            fields['death_date'] = self.set_unclear_date(data['deathDate'], format='d.m.y')
        if instance:
            for k in fields:
                setattr(instance, k, fields[k])
            return instance
        return DeadPerson(**fields)

class DeadPerson3Serializer(serializers.ModelSerializer):
    dob = UnclearDateFieldSerializer(source='birth_date', required=False, allow_null=True)
    dod = UnclearDateFieldSerializer(source='death_date', required=False, allow_null=True)
    lastName = serializers.CharField(source='last_name')
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    middleName = serializers.CharField(source='middle_name', required=False, allow_blank=True)

    class Meta:
        model = DeadPerson
        fields = ('id', 'firstName', 'lastName', 'middleName', 'dob', 'dod',)

class CustomPersonPermissionsMixin(object):

    def selected_func(self, instance):
        result = []
        for permitted in CustomPersonPermission.objects.filter(customperson=instance):
            if permitted.email:
                result.append(permitted.email)
            if permitted.login_phone:
                result.append(unicode(permitted.login_phone))
        return result

class BaseCustomPersonSerializer(
        UnclearDateFieldMixin,
        RestoreObjectMixin,
        CustomPersonPermissionsMixin,
        serializers.ModelSerializer
    ):
    birthDate = serializers.SerializerMethodField('birth_date')
    deathDate = serializers.SerializerMethodField('death_date')
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    middleName = serializers.CharField(source='middle_name', required=False, allow_blank=True)
    permissions = serializers.CharField(source='permission', required=False, allow_blank=True)
    selected = serializers.SerializerMethodField('selected_func')

    def restore_object_(self, instance=None, validated_data=[]):
        data = self.context['request'].data

        # - post:   из view всегда придет context['customplace']
        # - put:    может прийти context['customplace'] (реальный или null),
        #           тогда правим customplace в instance. Корректность
        #           customplace проверяется во view.
        #           Если не придет, то не затрагиваем customplace при правке.
        #
        customplace = self.context.get('customplace')

        fields_got = dict(
            last_name=data.get('lastName'),
            first_name=data.get('firstName'),
            middle_name=data.get('middleName'),
            permission=data.get('permissions'),
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
            if 'customplace' in self.context:
                fields['customplace'] = customplace
            for k in fields:
                setattr(instance, k, fields[k])
            return instance
        else:
            return CustomPerson(customplace=customplace, user=self.context['request'].user, **fields)

class CustomPersonSerializer(BaseCustomPersonSerializer):
    omsData = serializers.ReadOnlyField(source='oms_data')
    titlePhoto = HyperlinkedFileField(source='photo', read_only=True)

    class Meta:
        model = CustomPerson
        fields = ('id', 'firstName', 'lastName', 'middleName',
                  'birthDate', 'deathDate', 'omsData', 'titlePhoto',
        )

class CustomPerson2Serializer(BaseCustomPersonSerializer):
    grave = serializers.SerializerMethodField('grave_func')
    photo = HyperlinkedFileField(read_only=True)

    class Meta:
        model = CustomPerson
        fields = ('id', 'firstName', 'lastName', 'middleName', 'photo',
                  'birthDate', 'deathDate', 'grave',
        )

    def grave_func(self, customperson):
        try:
            return customperson.person.deadperson.burial_set.all()[0].grave_number
        except (AttributeError, DeadPerson.DoesNotExist, IndexError,):
            return None

class MemoryGallerySerializer(CreatedAtMixin, serializers.ModelSerializer):
    mediaContent = HyperlinkedFileField(source='bfile', read_only=True)
    addedAt = serializers.SerializerMethodField('createdAt_func')
    eventDate = UnclearDateFieldSafeSerializer(source='event_date')

    class Meta:
        model = MemoryGallery
        fields = ('id', 'type', 'text', 'mediaContent', 'addedAt', 'eventDate', )

class MemoryGallery2Serializer(MemoryGallerySerializer, UserProfileMixin):
    createdBy = serializers.SerializerMethodField('createdBy_func')
    permissions = serializers.ReadOnlyField(source='permission')
    selected = serializers.SerializerMethodField('selected_func')

    class Meta:
        model = MemoryGallery
        fields = (
            'id', 'type', 'text', 'mediaContent', 'addedAt', 'eventDate',
            'createdBy', 'permissions', 'selected',
        )

    def createdBy_func(self, instance):
        user = instance.creator
        if user:
           profile = get_profile(user)
           return dict(
               id=user.pk,
               lastname=profile.user_last_name,
               firstname=profile.user_first_name,
               middlename=profile.user_middle_name,
               photo_url=self.userPhotoUrl_func(user),
           )
        else:
            return None

    def selected_func(self, instance):
        result = []
        for permitted in MemoryGalleryPermission.objects.filter(memorygallery=instance):
            if permitted.email:
                result.append(permitted.email)
            if permitted.login_phone:
                result.append(unicode(permitted.login_phone))
        return result

class CustomPerson3Serializer(
        UnclearDateFieldMixin,
        RestoreObjectMixin,
        CustomPersonPermissionsMixin,
        serializers.ModelSerializer
    ):
    lastname = serializers.CharField(source='last_name', required=False, allow_blank=True)
    firstname = serializers.CharField(source='first_name', required=False, allow_blank=True)
    middlename = serializers.CharField(source='middle_name', required=False, allow_blank=True)
    commonText = serializers.CharField(source='memory_text', required=False, allow_blank=True)
    dob = serializers.SerializerMethodField('birth_date', required=False, allow_null=True)
    dod = serializers.SerializerMethodField('death_date', required=False, allow_null=True)
    photo = HyperlinkedFileField(read_only=True)
    gallery = serializers.SerializerMethodField('gallery_func')
    isDead = serializers.BooleanField(source='is_dead', required=False)
    placeId = serializers.PrimaryKeyRelatedField(source='customplace', read_only=True)
    permissions = serializers.CharField(source='permission', required=False, allow_blank=True)
    selected = serializers.SerializerMethodField('selected_func')

    class Meta:
        model = CustomPerson
        fields = (
            'id', 'lastname', 'firstname', 'middlename',
            'commonText', 'dob', 'dod', 'photo', 'gallery',
            'isDead', 'placeId', 'permissions', 'selected',
        )

    def gallery_func(self, instance):
        return [
            dict(
                photoUrl=self.context['request'].build_absolute_uri(item.bfile.url),
                title=item.text,
                addedAt=utcisoformat(item.date_of_creation),
            ) \
            for item in MemoryGallery.objects.filter(
                        customperson=instance,
                        type=MemoryGallery.TYPE_IMAGE,
                        bfile__gt='',
                        )
        ]

    def restore_object_(self, instance=None, validated_data=[]):
        data = self.context['request'].data
        customplace = self.context.get('customplace')

        fields_got = dict(
            last_name=data.get('lastname'),
            first_name=data.get('firstname'),
            middle_name=data.get('middlename'),
            memory_text=data.get('commonText'),
            is_dead=str_to_bool_or_None(data.get('isDead')),
            permission=data.get('permissions'),
        )
        fields = dict()
        for k in fields_got:
            if fields_got[k] is not None:
                fields[k] = fields_got[k]
        if 'dob' in data:
            fields['birth_date'] = self.set_unclear_date(data['dob'])
        if 'dod' in data:
            fields['death_date'] = self.set_unclear_date(data['dod'])
        photo = self.context['request'].data.get('photo')
        remove_photo = 'photo' in data and data['photo'] is None
        if photo or remove_photo:
            fields.update(dict(photo=photo))
            if instance:
                instance.delete_from_media()
        if instance:
            if 'customplace' in self.context:
                fields['customplace'] = customplace
            for k in fields:
                setattr(instance, k, fields[k])
            return instance
        else:
            return CustomPerson(customplace=customplace, user=self.context['request'].user, **fields)

class CustomPerson4Serializer(BaseCustomPersonSerializer):
    titlePhoto = HyperlinkedFileField(source='photo', read_only=True)
    placeId = serializers.PrimaryKeyRelatedField(source='customplace', read_only=True)

    class Meta:
        model = CustomPerson
        fields = ('id', 'firstName', 'lastName', 'middleName',
                  'birthDate', 'deathDate', 'titlePhoto', 'placeId',
                  'permissions', 'selected',
        )
