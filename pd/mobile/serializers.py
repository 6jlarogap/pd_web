# coding=utf-8
from geo.models import CoordinatesModel 
from rest_framework import serializers

from rest_api.fields import DateTimeUtcField

from burials.models import CemeteryPhoto

class BaseSerializer(serializers.Serializer):	
    pk = serializers.Field()    

class CoordinatesSerializer(BaseSerializer):
    lat = serializers.CharField(required=True)
    lng = serializers.CharField(required=True)
    angle_number = serializers.CharField(required=True)
    
    def restore_object(self, attrs, instance=None):
        if instance is not None:
            instance.pk = attrs.get('pk', instance.pk)
            instance.lat = attrs.get('lat', instance.lat)
            instance.lng = attrs.get('lng', instance.lng)
            instance.angle_number = attrs.get('angle_number', instance.angle_number)
            return instance
        return CoordinatesModel(**attrs)
        
class CemeteryPhotoSerializer(BaseSerializer):
    lat = serializers.CharField(required=False)
    lng = serializers.CharField(required=False)
    photo = serializers.FileField(max_length=None, allow_empty_file=False)
    dt_modified = serializers.DateTimeField(required=False)

class CemeterySerializer(BaseSerializer):
    name = serializers.CharField(required=True)
    square = serializers.CharField(required=True)
    ugh = BaseSerializer(required=True)
    dt_created = serializers.DateTimeField(required=False)

class CemeteryWithNestedObjectSerializer(CemeterySerializer):	
    coordinates = CoordinatesSerializer(many=True)
    photo = serializers.SerializerMethodField('photo_func')

    def photo_func(self, instance):
        return [CemeteryPhotoSerializer(photo).data \
                for photo in CemeteryPhoto.objects.filter(cemetery=instance)
        ]

class AreaSerializer(BaseSerializer):
    cemetery = BaseSerializer(required=True)
    name = serializers.CharField(required=True)
    square = serializers.CharField(required=True)
    dt_created = serializers.DateTimeField(required=False)
    
class AreaWithNestedObjectSerializer(AreaSerializer):    
    coordinates = CoordinatesSerializer(many=True)

class RegionSerializer(serializers.Serializer):    
    name = serializers.CharField(required=False)

class CitySerializer(serializers.Serializer):    
    name = serializers.CharField(required=False)
    
class StreetSerializer(serializers.Serializer):    
    name = serializers.CharField(required=False)
    
class CountrySerializer(serializers.Serializer):    
    name = serializers.CharField(required=False)
    
class LocationSerializer(serializers.Serializer):    
    house = serializers.CharField(required=False)
    block = serializers.CharField(required=False)
    building = serializers.CharField(required=False)
    flat = serializers.CharField(required=False)
    country = CountrySerializer(required=False)
    region = RegionSerializer(required=False)
    city = CitySerializer(required=False)
    street = StreetSerializer(required=False)

class BasePersonSerializer(serializers.Serializer):
    pk = serializers.Field()
    last_name = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    middle_name = serializers.CharField(required=False)    
    
class AlivePersonSerializer(BasePersonSerializer):    
    phones = serializers.CharField(required=False)
    login_phone = serializers.CharField(required=False)
    address = LocationSerializer(required=False)
    
class PlaceWithNestedObjectSerializer(BaseSerializer):    
    cemetery = BaseSerializer(required=False)
    area = BaseSerializer(required=True)    
    row = serializers.CharField(required=False)
    place = serializers.CharField(required=True)
    oldplace = serializers.CharField(required=False)
    place_width = serializers.CharField(required=False)
    place_length = serializers.CharField(required=False)
    dt_wrong_fio = serializers.DateTimeField(required=False)
    dt_military = serializers.DateTimeField(required=False)
    dt_size_violated = serializers.DateTimeField(required=False)
    dt_unowned = serializers.DateTimeField(required=False)
    dt_unindentified = serializers.DateTimeField(required=False)
    dt_free = serializers.DateTimeField(required=False)
    dt_created = serializers.DateTimeField(required=False)
    responsible = AlivePersonSerializer(required=False)
    
class PlaceSerializer(BaseSerializer):
    cemetery = BaseSerializer(required=False)
    area = BaseSerializer(required=True)
    row = serializers.CharField(required=False)
    place = serializers.CharField(required=True)
    place_width = serializers.FloatField(required=False)
    place_length = serializers.FloatField(required=False)
    dt_wrong_fio = DateTimeUtcField(required=False)
    dt_military = DateTimeUtcField(required=False)
    dt_size_violated = DateTimeUtcField(required=False)
    dt_unowned = DateTimeUtcField(required=False)
    dt_unindentified = DateTimeUtcField(required=False)
    dt_free = DateTimeUtcField(required=False)
    dt_created = DateTimeUtcField(required=False)
    responsible = AlivePersonSerializer(required=False)

class GraveSerializer(BaseSerializer):    
    place = BaseSerializer(required=True)    
    grave_number = serializers.CharField(required=True)
    is_military = serializers.CharField(required=False)
    is_wrong_fio = serializers.CharField(required=False)
    dt_free = serializers.DateTimeField(required=False)
    dt_created = serializers.DateTimeField(required=False)
    
class BurialSerializer(BaseSerializer):
    cemetery = BaseSerializer(required=True)
    area = BaseSerializer(required=True)
    row = serializers.CharField(required=False)
    place = BaseSerializer(required=True)
    grave = BaseSerializer(required=True)
    burial_container = serializers.CharField(required=False)
    deadman = BasePersonSerializer(required=False)
    fact_date = serializers.CharField(required=False)
    plan_date = serializers.DateField(required=False)
    plan_time = serializers.TimeField(required=False)
    status = serializers.CharField(required=False)
    responsible = AlivePersonSerializer(required=False)
    
class PlacePhotoSerializer(BaseSerializer):  
    place = BaseSerializer(required=False)    
    lat = serializers.CharField(required=False)
    lng = serializers.CharField(required=False)
    original_name = serializers.CharField(required=False)
    bfile = serializers.FileField(max_length=None, allow_empty_file=False)
    date_of_creation = serializers.DateTimeField(required=False)
    dt_created = serializers.DateTimeField(required=False)
