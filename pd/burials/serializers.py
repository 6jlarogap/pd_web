# coding=utf-8

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework.fields import Field, TimeField


from burials.models import Cemetery, Place, Area, Grave, Burial, AreaPhoto, BurialFiles, ExhumationRequest, \
    AreaPurpose, PlaceSize, PlaceStatus, CemeteryCoordinates, AreaCoordinates, PlaceSize, PlacePhoto, \
    Reason, CemeteryPhoto, CemeterySchema, OrderPlace

from geo.models import Location
from geo.serializers import AddressLatLonMixin
from geo.serializers import LocationSerializer

from persons.serializers import AlivePersonSerializer, \
        DeadPersonSerializer, DeadPerson2Serializer, \
        PhoneSerializer

from rest_api.fields import UnclearDateFieldSerializer, UnclearDateFieldSafeSerializer

from django.core.exceptions import ValidationError


class GetGalleryMixin(object):

    def gallery_func(self, obj):
        request = self.context.get('request')
        return obj.get_photo_gallery(request) if request else []

class SubCemeterySerializer(serializers.ModelSerializer):

    class Meta:
        model = Cemetery
        fields = ('id', 'name')

class CemeteryTitleSerializer(serializers.ModelSerializer):
    title = serializers.Field('name')

    class Meta:
        model = Cemetery
        fields = ('id', 'title')

class CemeteryPhotoMixin(object):

    def photoUrl_func(self, instance):
        photo = ''
        if hasattr(self, 'context') and 'request' in self.context:
            try:
                photo = CemeteryPhoto.objects.get(cemetery=instance).photo
            except CemeteryPhoto.DoesNotExist:
                pass
            if photo:
                photo = self.context['request'].build_absolute_uri(photo.url)
        return photo

    def schemaUrl_func(self, instance):
        photo = ''
        if hasattr(self, 'context') and 'request' in self.context:
            try:
                photo = CemeterySchema.objects.get(cemetery=instance).photo
            except CemeterySchema.DoesNotExist:
                pass
            if photo:
                photo = self.context['request'].build_absolute_uri(photo.url)
        return photo

class CemeteryClientSiteSerializer(AddressLatLonMixin, CemeteryPhotoMixin, serializers.ModelSerializer):
    phones = Field(source='phone_list')
    address = serializers.RelatedField()
    location = serializers.SerializerMethodField('location_func')
    workTimes = Field(source='worktimes')
    executive = serializers.SerializerMethodField('executive_func')
    photoUrl = serializers.SerializerMethodField('photoUrl_func')
    schemaUrl = serializers.SerializerMethodField('schemaUrl_func')

    class Meta:
        model = Cemetery
        fields = ('id', 'name', 'address', 'location', 'phones',
                  'workTimes', 'executive', 'photoUrl', 'schemaUrl',
        )

    def executive_func(self, obj):
        if obj.caretaker:
            return dict(fullName=u"%s" % obj.caretaker.profile)
        else:
            return None

class AreaTitleSerializer(serializers.ModelSerializer):
    title = serializers.Field('name')

    class Meta:
        model = Area
        fields = ('id', 'title')

class PlaceTitleSerializer(serializers.ModelSerializer):
    title = serializers.Field('place')

    class Meta:
        model = Place
        fields = ('id', 'title', 'row')

class AreaPurposeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaPurpose
        fields = ('id', 'name')

class SubPlaceItemSerializer(serializers.ModelSerializer):
    responsible = AlivePersonSerializer(source='responsible')
    class Meta:
        model = Place
        fields = ('id', 'row', 'place', 'responsible')


class CemeterySerializer(CemeteryPhotoMixin, serializers.ModelSerializer):
    area_cnt = Field(source='area_cnt')
    work_time = Field(source='work_time')
    address = Field(source='address_id')
    time_begin = TimeField()
    time_end = TimeField()
    caretaker = serializers.PrimaryKeyRelatedField(required=False)
    #phones = serializers.SerializerMethodField('get_phones')
    photoUrl = serializers.SerializerMethodField('photoUrl_func')
    schemaUrl = serializers.SerializerMethodField('schemaUrl_func')

    class Meta:
        model = Cemetery
        fields = ('id', 'name', 'work_time', 'area_cnt', 'code', 'time_begin', 'time_end', \
                  'places_algo', 'places_algo_archive', \
                  'archive_burial_fact_date_required', 'archive_burial_account_number_required', \
                  'address', 'time_slots', 'caretaker', 'photoUrl', 'schemaUrl', )
    
    def get_phones(self, obj):
        return PhoneSerializer(obj.phone_set.all()).data


class CemeteryBriefSerializer(serializers.ModelSerializer):
    phones = Field(source='phone_list')
    address = serializers.RelatedField()

    class Meta:
        model = Cemetery
        fields = ('id', 'address', 'phones', )

class AreaSerializer(serializers.ModelSerializer):
    purpose = serializers.PrimaryKeyRelatedField()
    cemetery = serializers.PrimaryKeyRelatedField()
    places_count = serializers.IntegerField(required=True)
    caretaker = serializers.PrimaryKeyRelatedField(required=False)

    class Meta:
        model = Area
        fields = ('id', 'cemetery', 'name', 'availability', 'kind', 'places_count', 'purpose', 'caretaker')

    def is_valid(self):
        valid = not self.errors
        if not self.many and self.object:
            max_graves_count = self.context['request'].user.profile.org.max_graves_count
            if self.object.places_count<=0 or self.object.places_count>max_graves_count:
                self._errors = self._errors or {}
                self._errors["__all__"] = [_(u"Количество могил должно быть от 1 до %d") % max_graves_count,]
                valid = False
        return valid


class ApiPlacesSerializer(serializers.ModelSerializer):
    location = serializers.Field(source='location')
    status = serializers.Field(source='status_list')


class ApiOmsPlacesSerializer(ApiPlacesSerializer):
    cemeteryId = serializers.PrimaryKeyRelatedField(source='cemetery')
    areaId = serializers.PrimaryKeyRelatedField(source='area')

    class Meta:
        model = Place
        fields = ('id', 'cemeteryId', 'areaId', 'location', 'status', )


class ApiCatalogPlacesSerializer(GetGalleryMixin, ApiPlacesSerializer):
    photos = serializers.SerializerMethodField('gallery_func')
    address = serializers.Field(source='full_name')
    cemetery = CemeteryBriefSerializer()

    class Meta:
        model = Place
        fields = ('id', 'location', 'address', 'status',  'photos', 'cemetery' )


class PlaceDeadmenMixin(object):

    def deadmen_func(self, place):
        result = []
        for burial in place.burial_set.filter(annulated=False):
            if burial.deadman:
                result.append(DeadPerson2Serializer(burial.deadman).data)
        return result

class ApiClientSitePlacesSerializer(PlaceDeadmenMixin, ApiPlacesSerializer):
    address = serializers.Field(source='address_short')
    photo = serializers.SerializerMethodField('photo_func')
    deadmen = serializers.SerializerMethodField('deadmen_func')
    hasResponsible = serializers.SerializerMethodField('hasResponsible_func')
    responsible = serializers.SerializerMethodField('responsible_func')

    class Meta:
        model = Place
        fields = ('id', 'address', 'location', 'photo', 'deadmen', 'hasResponsible', 'responsible')

    def photo_func(self, place):
        return place.last_photo(self.context['request'])

    def hasResponsible_func(self, place):
        return bool(place.responsible and place.responsible.last_name)

    def responsible_func(self, place):
        return self.hasResponsible_func(place) and place.responsible.full_name() or ''

class PlaceSerializer(GetGalleryMixin, serializers.ModelSerializer):
    cemetery = serializers.PrimaryKeyRelatedField()
    area = serializers.PrimaryKeyRelatedField()
    responsible = serializers.PrimaryKeyRelatedField(required=False)
    #available_count = Field(source='available_count')
    responsible_txt = serializers.SerializerMethodField('responsible_str')
    gallery = serializers.SerializerMethodField('gallery_func')
    dt_free = serializers.DateTimeField(required=False)
    dt_wrong_fio = serializers.DateTimeField(required=False)
    dt_military = serializers.DateTimeField(required=False)
    dt_size_violated = serializers.DateTimeField(required=False)
    dt_unowned = serializers.DateTimeField(required=False)
    dt_unindentified = serializers.DateTimeField(required=False)
    caretaker = serializers.PrimaryKeyRelatedField(required=False)
    create_cabinet = serializers.SerializerMethodField('create_cabinet_func')
    location = serializers.Field('location')

    class Meta:
        model = Place
        fields = ('id', 'cemetery', 'lat', 'lng', 'area', 'row', 'place', 'responsible', 'responsible_txt',
                  'place_length', 'place_width', 'gallery',
                  'dt_free',
                  'dt_wrong_fio', 'dt_military', 'dt_size_violated', 'dt_unowned', 'dt_unindentified',
                  'caretaker', 'create_cabinet',
                  'location',
                 ) 

    def create_cabinet_func(self, obj):
        return settings.CREATE_CABINET_ALLOW

    def responsible_str(self, obj):
        if obj.responsible:
            return "%s %s %s" % (obj.responsible.first_name, obj.responsible.middle_name, obj.responsible.last_name)

    def is_valid(self):
        valid = not self.errors
        if not self.many and self.object:
            max_graves_count = self.context['request'].user.profile.org.max_graves_count or 10
            try:
                places_count = int(self.context['request'].DATA.get('places_count',1))
                assert places_count>0 and places_count<=max_graves_count
            except:
                self._errors = self._errors or {}
                self._errors["__all__"] = [_(u"Количество могил должно быть от 1 до %d") % max_graves_count,]
                valid = False
        return valid
        
class PlaceLockSerializer(PlaceDeadmenMixin, serializers.ModelSerializer):
    cemetery = CemeteryTitleSerializer('cemetery')
    area = AreaTitleSerializer('area')
    place = serializers.SerializerMethodField('place_func')
    gallery = serializers.SerializerMethodField('photos_func')
    burials = serializers.SerializerMethodField('deadmen_func')

    class Meta:
        model = Place
        fields = ('id', 'cemetery', 'area', 'row', 'place', 'gallery', 'burials', )

    def place_func(self, obj):
        return PlaceTitleSerializer(obj).data

    def photos_func(self, obj):
        request = self.context.get('request')
        return obj.get_photos(request) if request else []

class GraveSerializer(serializers.ModelSerializer):
    place = serializers.PrimaryKeyRelatedField()
    dt_free = serializers.DateTimeField(required=False)

    class Meta:
        model = Grave
        fields = ('id', 'place', 'grave_number', 'lat', 'lng',
                  'is_wrong_fio', 'is_military', 'dt_free')


class BurialListSerializer(serializers.ModelSerializer):
    grave = serializers.PrimaryKeyRelatedField()
    deadman = DeadPersonSerializer()
    plan_date = serializers.DateField(format=u"%d.%m.%Y")
    fact_date = UnclearDateFieldSerializer()
    class Meta:
        model = Burial
        fields = ('id', 'grave',  'deadman', 'burial_type', 'burial_container', \
                  'source_type', 'account_number', 'row', 'place_number', 'grave_number', \
                  'plan_date', 'plan_time', 'fact_date', 'status', 'annulated')


class BurialSerializer(serializers.ModelSerializer):
    #place = Field(source='place_id')
    cemetery = serializers.PrimaryKeyRelatedField()
    area = serializers.PrimaryKeyRelatedField()
    place = serializers.PrimaryKeyRelatedField()
    deadman = DeadPersonSerializer()
    grave = serializers.PrimaryKeyRelatedField()
    responsible = AlivePersonSerializer(source='responsible')
    applicant = AlivePersonSerializer(source='applicant')  
    # applicant_organization dover agent_director
    fact_date = UnclearDateFieldSerializer()
    plan_date = serializers.DateField(format=u"%d.%m.%Y")
    
    class Meta:
        model = Burial
        fields = ('id', 'deadman', 'burial_type', 'burial_container', \
                  'source_type', 'account_number', 'row', 'place_number', 'grave_number', \
                  'plan_date', 'plan_time', 'fact_date', 'status', 'annulated', \
                  'place', 'cemetery', 'area', 'grave', 'responsible', 'applicant')


class BurialPutGraveSerializer(serializers.ModelSerializer):

    class Meta:
        model = Burial
        fields = ('id', 'grave_number',)


class AreaPhotoSerializer(serializers.ModelSerializer):
    area = serializers.PrimaryKeyRelatedField()
    date_of_creation = serializers.DateField(format=u"%d.%m.%Y")
    class Meta:
        model = AreaPhoto
        fields = ('id', 'area', 'bfile', 'comment', 'original_name', 'lat', 'lng', 'date_of_creation') 


class ExhumationRequestSerializer(serializers.ModelSerializer):
    burial = serializers.PrimaryKeyRelatedField()
    place = serializers.PrimaryKeyRelatedField()
    applicant = AlivePersonSerializer(source='responsible')
    #applicant_organization = serializers.PrimaryKeyRelatedField()
    class Meta:
        model = ExhumationRequest
        fields = ('id', 'burial', 'plan_date', 'plan_time', 'fact_date', 'applicant', \
                  'applicant_organization',)
        #agent_director, agent, dover


class PlaceSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceSize
        fields = ('graves_count', 'place_length', 'place_width')
      
class OrderPlaceSerializer(serializers.ModelSerializer):
    cemeteryId = serializers.Field('cemetery.id')
    cemeteryText = serializers.Field('cemetery_text')
    areaId = serializers.Field('area.id')
    placeNumber = serializers.Field('place')

    class Meta:
        model = OrderPlace
        fields = (
            'cemeteryId', 'cemeteryText', 'areaId', 'row',
            'placeNumber', 'size'
        )
