# coding=utf-8

from rest_framework import serializers

from geo.models import Location
from users.models import Org, Store
from persons.models import Phone

class StoreSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField('address_func')
    phones = serializers.SerializerMethodField('phones_func')
    location = serializers.SerializerMethodField('location_func')

    class Meta:
        model = Store
        fields = ('id', 'name', 'address', 'location', 'phones', )

    def restore_object(self, attrs, instance=None):
        data = self.context['request'].DATA
        name = data.get('name', instance and instance.name or '')
        address = data.get('address', '')
        location = data.get('location')
        phones = data.get('phones')
        
        if instance:
            # Правим существующий
            instance.name = name 
            if address:
                instance.address.addr_str = address
            if location:
                instance.address.gps_x = location['longitude']
                instance.address.gps_y = location['latitude']
            if address or location:
                instance.address.save()
            if phones is not None:
                Phone.create_default_phones(instance, phones)
            return instance

        # Create new instance
        kwargs = dict(addr_str=address)
        if location:
            kwargs.update({
                'gps_y': location.get('latitude'),
                'gps_x': location.get('longitude'),
            })
        address = Location.objects.create(**kwargs)
        store = Store(
            loru=self.context['request'].user.profile.org,
            name=name,
            address=address,
        )
        return store

    def address_func(self, instance):
        return unicode(instance.address)

    def phones_func(self, instance):
        phones = []
        for phone in instance.phone_set:
            phones.append(phone.number)
        return phones

    def location_func(self, instance):
        if instance.address.gps_x is not None and instance.address.gps_y is not None:
            return {
                'latitude': instance.address.gps_y,
                'longitude': instance.address.gps_x,
            }
        else:
            return None

class OrgSerializer(serializers.ModelSerializer):

    class Meta:
        model = Org
        fields = ('id', 'name', 'slug',
        )
