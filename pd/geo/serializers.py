# coding=utf-8

from rest_framework import serializers

from burials.models import Cemetery, Place, Area, BurialFiles
from geo.models import Location, Country, Region, City, Street

class AddressLatLonMixin(serializers.ModelSerializer):

    def location_func(self, obj):
        if obj.address and obj.address.gps_x and obj.address.gps_y:
            return {
                'latitude': obj.address.gps_y,
                'longitude': obj.address.gps_x,
            }
        else:
            return None

class CountrySerializer(serializers.ModelSerializer):
    text = serializers.ReadOnlyField(source='name')
    class Meta:
        model = Country
        fields = ('id','name', 'text') 

class RegionSerializer(serializers.ModelSerializer):
    text = serializers.ReadOnlyField(source='name')
    class Meta:
        model = Region
        fields = ('id','name', 'text') # 'country',

class CitySerializer(serializers.ModelSerializer):
    text = serializers.ReadOnlyField(source='name')
    class Meta:
        model = City
        fields = ('id','name', 'text') # 'region',

class StreetSerializer(serializers.ModelSerializer):
    text = serializers.ReadOnlyField(source='name')
    class Meta:
        model = Street
        fields = ('id','name', 'text') #'city',

class LocationSerializer(serializers.ModelSerializer):
    country = serializers.SlugRelatedField(many=False, required=False, read_only=True, slug_field='name')
    region  = serializers.SlugRelatedField(many=False, required=False, read_only=True, slug_field='name')
    city    = serializers.SlugRelatedField(many=False, required=False, read_only=True, slug_field='name')
    street  = serializers.SlugRelatedField(many=False, required=False, read_only=True, slug_field='name')
    class Meta:
        model = Location
        fields = ('id','country', 'region', 'city', 'street', \
                 'post_index', 'house', 'block', 'building', 'flat', 'gps_x', 'gps_y', 'info' ) 

class LocationStaticSerializer(serializers.ModelSerializer):
    country = CountrySerializer(many=False, required=False,)
    region  = RegionSerializer(many=False, required=False,)
    city    = CitySerializer(many=False, required=False,)
    street  = StreetSerializer()
    class Meta:
        model = Location
        fields = ('id','country', 'region', 'city', 'street', \
                 'post_index', 'house', 'block', 'building', 'flat', 'gps_x', 'gps_y', 'info' ) 

class LocationDataSerializer(serializers.ModelSerializer):
    gps_x = serializers.FloatField(required=False, allow_null=True)
    gps_y = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = Location
        fields = ('id', 'post_index', 'house', 'block', 'building', 'flat', 'gps_x', 'gps_y', 'info' ) 
