# coding=utf-8

from rest_framework import serializers
from rest_framework.fields import Field

from django.db.models.query_utils import Q

from rest_api.fields import HyperlinkedFileField
from pd.utils import PhonesFromTextMixin, utcisoformat, CreatedAtMixin

from django.contrib.auth.models import User

from geo.models import Location
from users.models import Org, Store, FavoriteSupplier, UserPhoto, is_cabinet_user, is_trade_user, \
                         Profile, Dover, ProfileLORU, get_profile, OrgGallery, OrgReview, StorePhoto
from persons.models import Phone
from orders.models import Order, Product, Service, OrgServicePrice

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
            if is_trade_user(user):
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

class Store2Serializer(StoreSerializer):
    title = Field(source='name')
    workTimes = Field(source='worktimes')
    photoUrl = serializers.SerializerMethodField('photoUrl_func')

    class Meta:
        model = Store
        fields = ('id', 'title', 'address', 'location', 'phones', 'workTimes', 'photoUrl')

    def photoUrl_func(self, instance):
        try:
            photo = StorePhoto.objects.get(store=instance).photo
        except StorePhoto.DoesNotExist:
            photo = None
        return self.context['request'].build_absolute_uri(photo.url) if photo else ''

class StoreShortSerializer(serializers.ModelSerializer):
    title = serializers.Field(source='name')

    class Meta:
        model = Store
        fields = ('id', 'title', )

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

class OrgShort6Serializer(serializers.ModelSerializer):
    domainName = serializers.Field(source='subdomain')

    class Meta:
        model = Org
        fields = ('id', 'domainName')

class OrgClientSiteSerializer(PhonesFromTextMixin, OrgSerializerMixin, serializers.ModelSerializer):
    fullName = Field(source='full_name')
    address = serializers.RelatedField('off_address')
    phones = serializers.SerializerMethodField('phones_func')
    location = serializers.SerializerMethodField('location_func')
    shopSite = Field(source='shop_site')

    class Meta:
        model = Org
        fields = ('id', 'name', 'fullName',  'description', 'address',
                  'location', 'phones', 'fax', 'email', 'site', 'shopSite', 
        )

class OrgOptSupplierSerializer(serializers.ModelSerializer):
    tin = Field(source='inn')
    dtLastOrder = serializers.SerializerMethodField('dt_last_order_func')

    class Meta:
        model = Org
        fields = ('id', 'name', 'tin', 'dtLastOrder', )

    def dt_last_order_func(self, loru):
      try:
          return utcisoformat(
              Order.objects.filter(loru=loru, type=Order.TYPE_TRADE).order_by('-dt_created')[0].dt_created
          )
      except IndexError:
          return None

class ShopSerializerMixin(object):

    def titleImageUrl_func(self, instance):
        try:
            return self.context['request'].build_absolute_uri(
                OrgGallery.objects.filter(org=instance). \
                    order_by('-date_of_creation')[0].bfile.url
            )
        except IndexError:
            return None


class ShopSerializer(ShopSerializerMixin, serializers.ModelSerializer):
    title = Field(source='name')
    itemPrice = serializers.SerializerMethodField('itemPrice_func')
    titleImageUrl = serializers.SerializerMethodField('titleImageUrl_func')
    subdomainName = Field(source='subdomain')

    class Meta:
        model = Org
        fields = ('id', 'subdomainName', 'title', 'description', 'titleImageUrl', 'itemPrice',)

    def itemPrice_func(self, instance):
        try:
            price_km = OrgServicePrice.objects.get(
                orgservice__org=instance,
                orgservice__service__name=Service.SERVICE_DELIVERY,
                orgservice__enabled=True,
                measure__name='km',
            )
            return dict(
                price=float(price_km.price),
                currency=instance.currency.code,
            )
        except OrgServicePrice.DoesNotExist:
            return None

class ShopDetailSerializer(ShopSerializerMixin, serializers.ModelSerializer):
    title = Field(source='name')
    titleImageUrl = serializers.SerializerMethodField('titleImageUrl_func')
    contacts = serializers.SerializerMethodField('contacts_func')
    subdomainName = Field(source='subdomain')

    class Meta:
        model = Org
        fields = ('id', 'subdomainName', 'title', 'description', 'titleImageUrl', 'contacts')

    def contacts_func(self, org):
        return dict(
            email=org.email,
            phones=org.phone_list(),
            fax=org.fax,
            address=org.off_address,
            site=org.site,
        )

class OrgGallerySerializer(serializers.ModelSerializer):
    title = Field(source='comment')
    photoUrl = HyperlinkedFileField(source='bfile')

    class Meta:
        model = OrgGallery
        fields = ('id', 'title', 'photoUrl',)

class UserProfileMixin(object):

    def firstName_func(self, user):
        profile = get_profile(user)
        return profile.user_first_name or ''

    def middleName_func(self, user):
        profile = get_profile(user)
        return profile.user_middle_name or ''

    def lastName_func(self, user):
        profile = get_profile(user)
        return profile.user_last_name or ''

    def userPhotoUrl_func(self, user):
        try:
            userphoto = UserPhoto.objects.get(user=user)
            request = self.context['request']
            return request.build_absolute_uri(userphoto.bfile.url)
        except UserPhoto.DoesNotExist:
            return None

    def loginPhone_func(self, user):
        if is_cabinet_user(user):
            return str(user.customerprofile.login_phone)
        else:
            return None

class UserFioSerializer(UserProfileMixin, serializers.ModelSerializer):
    firstName = serializers.SerializerMethodField('firstName_func')
    middleName = serializers.SerializerMethodField('middleName_func')
    lastName = serializers.SerializerMethodField('lastName_func')

    class Meta:
        model = User
        fields = ('id', 'firstName', 'lastName', 'middleName')

class UserFioLoginSerializer(UserProfileMixin, serializers.ModelSerializer):
    fio = serializers.SerializerMethodField('fio_func')

    class Meta:
        model = User
        fields = ('id', 'fio')

    def fio_func(self, user):
        profile = get_profile(user)
        if profile.user_last_name:
            return profile.full_name()
        else:
            return u"(%s)" % user.username

class ProfileFioLoginSerializer(serializers.ModelSerializer):
    fio = serializers.SerializerMethodField('fio_func')

    class Meta:
        model = Profile
        fields = ('id', 'fio')

    def fio_func(self, profile):
        if profile.user_last_name:
            return profile.full_name()
        else:
            return u"(%s)" % profile.user.username

class ProfileClientSiteSerializer(PhonesFromTextMixin, serializers.ModelSerializer):
    phones = serializers.SerializerMethodField('phones_func')
    fullName = Field(source='full_name')
    role = Field(source='title')
    photoUrl = serializers.SerializerMethodField('userPhotoUrl_func')
    department = StoreShortSerializer(source='store')

    class Meta:
        model = Profile
        fields = ('id', 'fullName', 'role', 'photoUrl', 'phones', 'department',)

    def userPhotoUrl_func(self, profile):
        try:
            userphoto = UserPhoto.objects.get(user=profile.user)
            request = self.context['request']
            return request.build_absolute_uri(userphoto.bfile.url)
        except UserPhoto.DoesNotExist:
            return None


class OrgReviewSerializer(CreatedAtMixin, serializers.ModelSerializer):
    isPositive = Field(source='is_positive')
    author = UserFioSerializer(source='creator')
    createdAt = serializers.SerializerMethodField('createdAt_func')
    title = Field(source='subject')
    commonText = Field(source='common_text')
    positiveText = Field(source='positive_text')
    negativeText = Field(source='negative_text')

    class Meta:
        model = OrgReview
        fields = ('id', 'isPositive', 'title', 'commonText', 'positiveText', 
                  'negativeText', 'createdAt', 'author')

class UserSettingsSerializer(UserProfileMixin, serializers.ModelSerializer):
    firstName = serializers.SerializerMethodField('firstName_func')
    middleName = serializers.SerializerMethodField('middleName_func')
    lastName = serializers.SerializerMethodField('lastName_func')
    avatarUrl = serializers.SerializerMethodField('userPhotoUrl_func')
    loginPhone = serializers.SerializerMethodField('loginPhone_func')

    class Meta:
        model = User
        fields = ('firstName', 'lastName', 'middleName', 'avatarUrl', 'loginPhone', )

class UserSettings2Serializer(UserSettingsSerializer):
    photoUrl = serializers.SerializerMethodField('userPhotoUrl_func')

    class Meta:
        model = User
        fields = ('id', 'firstName', 'lastName', 'middleName', 'photoUrl', )

class ArchUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_active', )

class ArchProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.Field('user.id')
    org_id = serializers.Field('org.id')
    cemetery_id = serializers.Field('cemetery.id')
    area_id = serializers.Field('area.id')

    class Meta:
        model = Profile
        fields = ('id', 'user_id', 'org_id', 'user_last_name',
                  'user_first_name', 'user_middle_name',
                  'cemetery_id', 'area_id',
        )

class ArchOrgSerializer(serializers.ModelSerializer):
    off_address_id = serializers.Field('off_address.id')
    currency_id = serializers.Field('currency.id')

    class Meta:
        model = Org
        fields = (
            'id', 'type', 'name', 'full_name', 'description',
            'inn', 'kpp', 'ogrn', 'director', 'basis', 'email',
            'phones', 'sms_phone', 'fax', 'off_address_id',
            'numbers_algo', 'plan_date_days_before',
            'max_graves_count', 'worktime', 'site',
            'currency_id', 
        )

class ArchDoverSerializer(serializers.ModelSerializer):
    agent_id = serializers.Field('agent.id')
    target_org_id = serializers.Field('target_org.id')

    class Meta:
        model = Dover
        fields = ('id', 'agent_id', 'target_org_id', 'number', 'begin', 'end', 'document')

class ArchProfileLORUSerializer(serializers.ModelSerializer):
    ugh_id = serializers.Field('ugh.id')
    loru_id = serializers.Field('loru.id')

    class Meta:
        model = ProfileLORU
        fields = ('id', 'ugh_id', 'loru_id',)
