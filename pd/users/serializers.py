# coding=utf-8

from rest_framework import serializers
from rest_framework.fields import Field

from django.db.models.query_utils import Q

from pd.utils import PhonesFromTextMixin, utcisoformat
from geo.models import Location
from users.models import Org, Store, FavoriteSupplier, is_loru_user
from persons.models import Phone
from orders.models import Product

class OrgSerializerMixin(object):

    def catalog_qs(self, loru, catalog=None):
        """
        Выборка продуктов по каталогу: оптовому, публичному или по обоим

        catalog =   None: оба каталога
                    'public': публичный
                    'wholesale': оптовый
        """
        q_catalog = Q(is_public_catalog=True) | Q(is_wholesale=True)
        if catalog is not None:
            if catalog == 'public':
                q_catalog = Q(is_public_catalog=True)
            elif catalog == 'wholesale':
                q_catalog = Q(is_wholesale=True)
        return Q(loru=loru) & q_catalog

    def location_func(self, instance):
        if instance.off_address and instance.off_address.gps_x is not None and instance.off_address.gps_y is not None:
            return {
                'latitude': instance.off_address.gps_y,
                'longitude': instance.off_address.gps_x,
            }
        else:
            return None

    def isFavorite_func(self, instance):
        result = None
        if hasattr(self, 'context') and 'request' in self.context:
            user = self.context['request'].user
            if is_loru_user(user):
                result = FavoriteSupplier.objects.filter(
                    loru=user.profile.org,
                    supplier=instance,
                    ).exists()
        return result

class StoreSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField('address_func')
    phones = serializers.SerializerMethodField('phones_func')
    location = serializers.SerializerMethodField('location_func')
    hasComponents = serializers.SerializerMethodField('has_wholesales_func')

    class Meta:
        model = Store
        fields = ('id', 'name', 'address', 'location', 'phones', 'hasComponents', )

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

    def has_wholesales_func(self, instance):
        return Product.objects.filter(loru=instance.loru, is_wholesale=True).exists()

    def phones_func(self, instance):
        return [ phone.number for phone in instance.phone_set ]

    def location_func(self, instance):
        if instance.address and instance.address.gps_x is not None and instance.address.gps_y is not None:
            return {
                'latitude': instance.address.gps_y,
                'longitude': instance.address.gps_x,
            }
        else:
            return None

class OrgSerializer(PhonesFromTextMixin, OrgSerializerMixin, serializers.ModelSerializer):
    fullname = Field(source='full_name')
    address = serializers.RelatedField('off_address')
    stores = StoreSerializer(many=True, source='store_set')
    phones = serializers.SerializerMethodField('phones_func')
    categories = serializers.SerializerMethodField('categories_func')
    location = serializers.SerializerMethodField('location_func')
    isFavorite = serializers.SerializerMethodField('isFavorite_func')

    class Meta:
        model = Org
        fields = ('id', 'name', 'slug', 'fullname', 'address', 'description',
                  'phones', 'fax', 'worktime', 'site', 'email', 'stores',
                  'categories', 'location', 'isFavorite',
        )

    def categories_func(self, obj):
        return [
                {
                    'id': pc['productcategory__pk'],
                    'title': pc['productcategory__name']
                } for pc in Product.objects.filter(self.catalog_qs(loru=obj)).\
                                order_by('productcategory__pk').\
                                values('productcategory__pk', 'productcategory__name').distinct()
        ]

class OrgShortSerializer(PhonesFromTextMixin, serializers.ModelSerializer):
    address = serializers.RelatedField(source='off_address')
    phones = serializers.SerializerMethodField('phones_func')

    class Meta:
        model = Org
        fields = ('id', 'name', 'slug', 'address', 'phones', 'worktime', 'site', )

class OrgShort2Serializer(OrgSerializerMixin, serializers.ModelSerializer):
    location = serializers.SerializerMethodField('location_func')
    categories = serializers.SerializerMethodField('categories_func')
    stores = StoreSerializer(many=True, source='store_set')

    class Meta:
        model = Org
        fields = ('id', 'name', 'slug', 'location', 'categories', 'stores', )

    def categories_func(self, obj):
        catalog = 'wholesale' if self.context['request'].GET.get('supplierType', '').lower() == 'opt' else 'public'
        return [ pc['productcategory__pk'] for pc in \
            Product.objects.filter(self.catalog_qs(loru=obj, catalog=catalog)).\
                order_by('productcategory__pk').\
                values('productcategory__pk').distinct()
        ]

class OrgShort3Serializer(serializers.ModelSerializer):

    class Meta:
        model = Org
        fields = ('id', 'name',)

class OrgShort4Serializer(PhonesFromTextMixin, serializers.ModelSerializer):
    shortName = Field(source='name')
    phones = serializers.SerializerMethodField('phones_func')

    class Meta:
        model = Org
        fields = ('id', 'shortName', 'phones', )

class OrgShort5Serializer(OrgSerializerMixin, OrgShort4Serializer):
    isFavorite = serializers.SerializerMethodField('isFavorite_func')

    class Meta:
        model = Org
        fields = ('id', 'shortName', 'phones', 'isFavorite', )

class OrgOptSupplierSerializer(serializers.ModelSerializer):
    tin = Field(source='inn')
    dtLastOrder = serializers.SerializerMethodField('dt_last_order_func')

    class Meta:
        model = Org
        fields = ('id', 'name', 'tin', 'dtLastOrder', )

    def dt_last_order_func(self, loru):
      try:
          return utcisoformat(
              Iorder.objects.filter(supplier=loru).order_by('-dt_created')[0].dt_created
          )
      except IndexError:
          return None
