# coding=utf-8

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field


from burials.models import Cemetery, Place, Area, BurialFiles
from geo.models import Location, Country, Region, City, Street
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework.compat import smart_text


class CountrySerializer(serializers.ModelSerializer):
    text = serializers.Field(source='name')
    class Meta:
        model = Country
        fields = ('id','name', 'text') 


class RegionSerializer(serializers.ModelSerializer):
    text = serializers.Field(source='name')
    class Meta:
        model = Region
        fields = ('id','name', 'text') # 'country',


class CitySerializer(serializers.ModelSerializer):
    text = serializers.Field(source='name')
    class Meta:
        model = City
        fields = ('id','name', 'text') # 'region',


class StreetSerializer(serializers.ModelSerializer):
    text = serializers.Field(source='name')
    class Meta:
        model = Street
        fields = ('id','name', 'text') #'city',




# Nested tables fields serializer
class CountrySlugRelatedField(serializers.SlugRelatedField):
    def from_native(self, data):
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')
        
        try:
            name = self.parent.init_data.get(u"country"," ")
            item, created = Country.objects.get_or_create(name=name, defaults={})
        except (TypeError, ValueError):
            msg = self.error_messages['invalid']
            raise ValidationError(msg)
        else:
            return item


class RegionSlugRelatedField(serializers.SlugRelatedField):
    def from_native(self, data):
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')
        
        try:
            name = self.parent.init_data.get(u"country"," ")
            country, created = Country.objects.get_or_create(name=name, defaults={})
        except:
            raise ValidationError(_(u'Страна не найдена'))

        try:
            name = self.parent.init_data.get(u"region"," ")
            item, created = Region.objects.get_or_create(name=name, country=country)
        except (TypeError, ValueError):
            msg = self.error_messages['invalid']
            raise ValidationError(msg)
        else:
            return item


class CitySlugRelatedField(serializers.SlugRelatedField):    
    def from_native(self, data):
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')
        
        name = self.parent.init_data.get(u"country"," ")
        country, created = Country.objects.get_or_create(name=name, defaults={})

        name = self.parent.init_data.get(u"region"," ")
        region, created = Region.objects.get_or_create(name=name, country=country)
        

        try:
            name = self.parent.init_data.get(u"city"," ")
            item, created = City.objects.get_or_create(name=name, region=region)
        except (TypeError, ValueError):
            msg = self.error_messages['invalid']
            raise ValidationError(msg)
        else:
            return item


class StreetSlugRelatedField(serializers.SlugRelatedField):
    def from_native(self, data):
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')
        
        name = self.parent.init_data.get(u"country"," ")
        country, created = Country.objects.get_or_create(name=name, defaults={})

        name = self.parent.init_data.get(u"region"," ")
        region, created = Region.objects.get_or_create(name=name, country=country)

        name = self.parent.init_data.get(u"city"," ")
        city, created = City.objects.get_or_create(name=name, region=region)

        try:
            name = self.parent.init_data.get(u"street"," ")
            item, created = Street.objects.get_or_create(name=data, city=city)
        except (TypeError, ValueError):
            msg = self.error_messages['invalid']
            raise ValidationError(msg)
        else:
            return item
# EOF Nested tables fields serializer


class LocationSerializer(serializers.ModelSerializer):
    country = CountrySlugRelatedField(many=False, required=False, read_only=False, slug_field='name')
    region  = RegionSlugRelatedField(many=False, required=False,read_only=False, slug_field='name')
    city    = CitySlugRelatedField(many=False, required=False, read_only=False, slug_field='name')
    street  = StreetSlugRelatedField(many=False, required=False, read_only=False, slug_field='name')
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
    class Meta:
        model = Location
        fields = ('id', 'post_index', 'house', 'block', 'building', 'flat', 'gps_x', 'gps_y', 'info' ) 


class ArchCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name',) 

class ArchRegionSerializer(serializers.ModelSerializer):
    country_id = serializers.Field('country.id')

    class Meta:
        model = Region
        fields = ('id', 'country_id', 'name',) 

class ArchCitySerializer(serializers.ModelSerializer):
    region_id = serializers.Field('region.id')

    class Meta:
        model = City
        fields = ('id', 'region_id', 'name',) 

class ArchStreetSerializer(serializers.ModelSerializer):
    city_id = serializers.Field('city.id')

    class Meta:
        model = Street
        fields = ('id', 'city_id', 'name',) 

class ArchLocationSerializer(serializers.ModelSerializer):
    country_id = serializers.Field('country.id')
    region_id = serializers.Field('region.id')
    city_id = serializers.Field('city.id')
    street_id = serializers.Field('street.id')

    class Meta:
        model = Location
        fields = ('id','country_id', 'region_id', 'city_id', 'street_id',
                  'addr_str',
                  'post_index', 'house', 'block', 'building', 'flat', 'gps_x', 'gps_y', 'info',
        )
