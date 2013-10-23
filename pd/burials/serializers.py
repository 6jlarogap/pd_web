from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field, TimeField


from burials.models import Cemetery, Place, Area, Grave, Burial, AreaPhoto, GravePhoto, BurialFiles, ExhumationRequest, \
    AreaPurpose


from geo.models import Location
from geo.serializers import LocationSerializer

from persons.serializers import AlivePersonSerializer, DeadPersonSerializer

from rest_api.fields import UnclearDateFieldSerializer

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
    class Meta:
        model = Cemetery
        fields = ('id', 'name', 'work_time', 'area_cnt', 'time_begin', 'time_end', 'places_algo', 'address', 'time_slots') 


class AreaSerializer(serializers.ModelSerializer):
    purpose = serializers.PrimaryKeyRelatedField()
    cemetery = serializers.PrimaryKeyRelatedField()
    class Meta:
        model = Area
        fields = ('id', 'cemetery', 'name', 'availability', 'places_count', 'purpose')





class PlaceSerializer(serializers.ModelSerializer):
    cemetery = serializers.PrimaryKeyRelatedField()
    area = serializers.PrimaryKeyRelatedField()
    responsible = serializers.PrimaryKeyRelatedField(required=False)
    available_count = Field(source='available_count')
    responsible_txt = serializers.SerializerMethodField('responsible_str') 
    class Meta:
        model = Place
        fields = ('id', 'cemetery', 'lat', 'lng', 'area', 'row', 'place', 'responsible', 'responsible_txt', 
                  'available_count', 'place_length', 'place_width')

    def responsible_str(self, obj):
        if obj.responsible:
            return "%s %s %s" % (obj.responsible.first_name, obj.responsible.middle_name, obj.responsible.last_name)



class GraveSerializer(serializers.ModelSerializer):
    place = serializers.PrimaryKeyRelatedField()
    class Meta:
        model = Grave
        fields = ('id', 'place', 'grave_number', 'lat', 'lng')


class BurialListSerializer(serializers.ModelSerializer):
    grave = serializers.PrimaryKeyRelatedField()
    deadman = DeadPersonSerializer()
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
    class Meta:
        model = Burial
        fields = ('id', 'deadman', 'burial_type', 'burial_container', \
                  'source_type', 'account_number', 'row', 'place_number', 'grave_number', \
                  'plan_date', 'plan_time', 'fact_date', 'status', 'annulated', \
                  'place', 'cemetery', 'area', 'grave', 'responsible', 'applicant')


class GravePhotoSerializer(serializers.ModelSerializer):
    grave = serializers.PrimaryKeyRelatedField()
    class Meta:
        model = GravePhoto
        fields = ('id', 'grave', 'bfile', 'comment', 'original_name', 'lat', 'lng', 'date_of_creation') 


class AreaPhotoSerializer(serializers.ModelSerializer):
    area = serializers.PrimaryKeyRelatedField()
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

