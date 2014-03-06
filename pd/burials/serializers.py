# coding=utf-8

from django.contrib.auth.models import Group, Permission
from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework.fields import Field, TimeField


from burials.models import Cemetery, Place, Area, Grave, Burial, AreaPhoto, GravePhoto, BurialFiles, ExhumationRequest, \
    AreaPurpose, PlaceSize


from geo.models import Location
from geo.serializers import LocationSerializer

from persons.serializers import AlivePersonSerializer, DeadPersonSerializer, PhoneSerializer

from rest_api.fields import UnclearDateFieldSerializer

from django.core.exceptions import ValidationError


class SubCemeterySerializer(serializers.ModelSerializer):
    """
    area subelement
    """
    class Meta:
        model = Cemetery
        fields = ('id', 'name')



class AreaPurposeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaPurpose
        fields = ('id', 'name')

class SubPlaceItemSerializer(serializers.ModelSerializer):
    responsible = AlivePersonSerializer(source='responsible')
    class Meta:
        model = Place
        fields = ('id', 'row', 'place', 'responsible')


class CemeterySerializer(serializers.ModelSerializer):
    area_cnt = Field(source='area_cnt')
    work_time = Field(source='work_time')
    address = Field(source='address_id')
    time_begin = TimeField()
    time_end = TimeField()
    #phones = serializers.SerializerMethodField('get_phones')

    class Meta:
        model = Cemetery
        fields = ('id', 'name', 'work_time', 'area_cnt', 'time_begin', 'time_end', 'places_algo', \
                  'archive_burial_fact_date_required', 'archive_burial_account_number_required', \
                  'address', 'time_slots')
    
    def get_phones(self, obj):
        return PhoneSerializer(obj.phone_set.all()).data


class AreaSerializer(serializers.ModelSerializer):
    purpose = serializers.PrimaryKeyRelatedField()
    cemetery = serializers.PrimaryKeyRelatedField()
    places_count = serializers.IntegerField(required=True)

    class Meta:
        model = Area
        fields = ('id', 'cemetery', 'name', 'availability', 'places_count', 'purpose')

    def is_valid(self):
        valid = not self.errors
        if not self.many and self.object:
            max_graves_count = self.context['request'].user.profile.org.max_graves_count
            if self.object.places_count<=0 or self.object.places_count>max_graves_count:
                self._errors = self._errors or {}
                self._errors["__all__"] = [_(u"Количество могил должно быть от 1 до %d") % max_graves_count,]
                valid = False
        return valid



class PlaceSerializer(serializers.ModelSerializer):
    cemetery = serializers.PrimaryKeyRelatedField()
    area = serializers.PrimaryKeyRelatedField()
    responsible = serializers.PrimaryKeyRelatedField(required=False)
    #available_count = Field(source='available_count')
    responsible_txt = serializers.SerializerMethodField('responsible_str')
    gallery = serializers.SerializerMethodField('gallery_func')
    dt_wrong_fio = serializers.DateTimeField(required=False)
    dt_military = serializers.DateTimeField(required=False)
    dt_size_violated = serializers.DateTimeField(required=False)
    dt_unowned = serializers.DateTimeField(required=False)
    dt_unindentified = serializers.DateTimeField(required=False)

    class Meta:
        model = Place
        fields = ('id', 'cemetery', 'lat', 'lng', 'area', 'row', 'place', 'responsible', 'responsible_txt', \
                  'place_length', 'place_width', 'gallery',
                  'dt_wrong_fio', 'dt_military', 'dt_size_violated', 'dt_unowned', 'dt_unindentified', 
                 ) 

    def gallery_func(self, obj):
        request = self.context.get('request')
        return obj.get_photo_gallery(request) if request else []
        
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
        

class GraveSerializer(serializers.ModelSerializer):
    place = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = Grave
        fields = ('id', 'place', 'grave_number', 'lat', 'lng', 'is_wrong_fio', 'is_military')


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


class GravePhotoSerializer(serializers.ModelSerializer):
    grave = serializers.PrimaryKeyRelatedField()
    date_of_creation = serializers.DateField(format=u"%d.%m.%Y")
    class Meta:
        model = GravePhoto
        fields = ('id', 'grave', 'bfile', 'comment', 'original_name', 'lat', 'lng', 'date_of_creation') 


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
      
