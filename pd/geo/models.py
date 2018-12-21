# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.query_utils import Q
from django.db.models.loading import get_model
from django.utils.translation import ugettext as _

from pd.models import BaseModel 

import re, urllib2, json

YANDEX_GEOCODE_URL = "http://geocode-maps.yandex.ru/1.x/?geocode=%s&format=json&results=1"

class GeoPointModel(models.Model):
    """
    Базовая GEO модель
    """
    lat = models.FloatField(_(u"Широта"), blank=True, null=True)
    lng = models.FloatField(_(u"Долгота"), blank=True, null=True)

    class Meta:
        abstract = True

    def location_dict(self):
        if self.lat is not None and self.lng is not None:
            return dict(latitude=self.lat, longitude=self.lng)
        else:
            return None

class CoordinatesModel(models.Model):
    """
    Базовая модель для списка координат объекта: вершин многоугольника
    """
    # TODO  Убрать этот базовый класс, а модель на его основе, burials.CemeteryCoordinates
    #       привести к PointsModel (неудачное название angle_number)
    #
    angle_number = models.PositiveIntegerField(_(u"Порядок следования углов многоугольника"))
    lat = models.FloatField(_(u"Широта"))
    lng = models.FloatField(_(u"Долгота"))

    class Meta:
        abstract = True


class PointsModel(models.Model):
    """
    Базовая модель для списка координат: маршрута или вершин многоугольника
    """
    index = models.PositiveIntegerField(_(u"Порядок следования точек, начиная с 0"))
    lat = models.FloatField(_(u"Широта"))
    lng = models.FloatField(_(u"Долгота"))

    class Meta:
        abstract = True


class Country(models.Model):
    """
    Страна.
    """

    name = models.CharField(_(u"Название"), max_length=255, db_index=True, unique=True)

    def __unicode__(self):
        return self.name[:24]

    @classmethod
    def get_yandex_address_info(cls, latitude, longitude):
        """
        Получить сырые данные для последующей выемки из них страны, адреса ...
        """
        if latitude is None or longitude is None:
            return None
        query = u"%s,%s" % (longitude, latitude, )
        try:
            r = urllib2.urlopen(YANDEX_GEOCODE_URL % query)
            raw_data = r.read().decode(r.info().getparam('charset') or 'utf-8')
        except (urllib2.HTTPError, urllib2.URLError):
            return None
        try:
            return json.loads(raw_data)
        except ValueError:
            return None

    @classmethod
    def get_country_currency_by_coords(cls, latitude, longitude):
        """
        Получить страну, валюту по координатам
        """
        result = None, None

        DOMAINS = dict(
            ru=dict(name=u'Россия', currency='RUR',),
            by=dict(name=u'Беларусь', currency='BYN',),
        )

        data = cls.get_yandex_address_info(latitude, longitude)
        if data:
            try:
                country = data['response']['GeoObjectCollection']['featureMember'][0]\
                            ['GeoObject']['metaDataProperty']['GeocoderMetaData']\
                            ['AddressDetails']['Country']
                country_parms = DOMAINS[country['CountryNameCode'].lower()]
                country_name = country_parms['name']
                currency_code = country_parms['currency']
                country, created_country = cls.objects.get_or_create(name=country_name)
                Currency = models.get_model('billing', 'Currency')
                currency, created_currency = Currency.objects.get_or_create(code=currency_code)
                result = country, currency
            except (KeyError, IndexError):
                pass
        return result

    @classmethod
    def get_address_by_coords(cls, latitude, longitude):
        """
        Получить адрес по координатам
        """
        result = None
        data = cls.get_yandex_address_info(latitude, longitude)
        if data:
            try:
                data = data['response']['GeoObjectCollection']['featureMember'][0]\
                            ['GeoObject']
                if 'name' in data and 'description' in data:
                    result = u"%s, %s" % (data['name'], data['description'])
                elif 'description' in data:
                    result = data['description']
                elif 'name' in data:
                    result = data['name']
            except (KeyError, IndexError):
                pass
        return result

    class Meta:
        db_table = "common_geocountry"
        ordering = ['name']
        verbose_name = _(u"страна")
        verbose_name_plural = _(u"страны")


class Region(models.Model):
    """
    Регион.
    """

    country = models.ForeignKey(Country)
    name = models.CharField(_(u"Название"), max_length=255, db_index=True)

    def __unicode__(self):
        return self.name[:24]

    class Meta:
        unique_together = (("country", "name"),)
        verbose_name = _(u"регион")
        verbose_name_plural = _(u"регионы")
        db_table = "common_georegion"
        ordering = ['name']

class City(models.Model):
    """
    Город.
    """

    region = models.ForeignKey(Region)
    name = models.CharField(_(u"Название"), max_length=255, db_index=True)

    def __unicode__(self):
        return self.name[:24]

    class Meta:
        unique_together = (("region", "name"),)
        verbose_name = _(u"населенный пункт")
        verbose_name_plural = _(u"населенные пункты")
        db_table = "common_geocity"
        ordering = ['name']

class Street(models.Model):
    """
    Улица.
    """

    city = models.ForeignKey(City)
    name = models.CharField(max_length=255, db_index=True)

    class Meta:
        ordering = ['name']
        unique_together = (("city", "name"),)
        verbose_name = (_(u"улица"))
        verbose_name_plural = (_(u"улицы"))

    def __unicode__(self):
        return self.name

class Location(models.Model):
    """
    Адрес.
    """
    country = models.ForeignKey(Country, verbose_name=_(u"Страна"), blank=True, null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, verbose_name=_(u"Регион"), blank=True, null=True, on_delete=models.SET_NULL)
    city = models.ForeignKey(City, verbose_name=_(u"Город"), blank=True, null=True, on_delete=models.SET_NULL)
    street = models.ForeignKey(Street, verbose_name=_(u"Улица"), blank=True, null=True, on_delete=models.SET_NULL)
    post_index = models.CharField(_(u"Почтовый индекс"), max_length=255, blank=True)

    house = models.CharField(_(u"Дом"), max_length=255, blank=True)
    block = models.CharField(_(u"Корпус"), max_length=255, blank=True)
    building = models.CharField(_(u"Строение"), max_length=255, blank=True)
    flat = models.CharField(_(u"Квартира"), max_length=255, blank=True)
    gps_x = models.FloatField(_(u"Координата X"), blank=True, null=True, editable=False)
    gps_y = models.FloatField(_(u"Координата Y"), blank=True, null=True, editable=False)
    info = models.TextField(_(u"Дополнительная информация"), blank=True, null=True)
    # Строка адреса в произвольной форме. Такая может приходить при входе в систему
    # пользователя лору, если его организация не имела доселе адреса и пользователь
    # этот адрес заполнил вручную. Преобразовать подобный адрес а структуру
    # страна, регион и т.д не всегда возможно, отсюда и необходимость в таком поле
    addr_str = models.CharField(_(u"Адрес"), max_length=255, blank=True)

    def get_local_addr(self, addr):
        if self.house:
            if addr:
                addr += _(u', дом %s') % self.house
            else:
                addr += _(u'дом %s') % self.house
        if self.block:
            addr += _(u', корп. %s') % self.block
        if self.building:
            addr += _(u', строен. %s') % self.building
        if self.flat:
            addr += _(u', кв. %s') % self.flat
        if self.info:
            addr += u', %s' % self.info
        return addr

    def city_addr(self):
        """
        Только адрес города, строка
        """
        if self.city:
            return u'%s, %s, %s' % (self.city, self.region, self.country,)
        else:
            return u''

    def address_(self, is_short=False, empty=False):
        if self.addr_str and self.addr_str.strip():
            return self.addr_str.strip()
        elif self.street or self.region or self.country:
            addr = u''
            if self.street:
                addr += u'%s' % self.street
            addr = self.get_local_addr(addr)

            if addr:
                addr += u', %s' % (self.city or self.street and self.street.city or '')
            else:
                addr += u'%s' % (self.city or self.street and self.street.city or '')
            
            if is_short:
                return addr.replace(', ,', ', ')

            if addr:
                addr += u', %s' % (self.region or self.street and self.street.city.region or '')
            else:
                addr += u'%s' % (self.region or self.street and self.street.city.region or '')

            if addr:
                addr += u', %s' % (self.country or self.street and self.street.city.region.country or '')
            else:
                addr += u'%s' % (self.country or self.street and self.street.city.region.country or '')

            if addr and self.post_index:
                addr += u' %s' % self.post_index

            return addr.replace(', ,', ', ')
        else:
            if empty:
                return ''
            else:
                return _(u"незаполненный адрес")

    def __unicode__(self):
        return self.address_(is_short=False)

    def short(self):
        return self.address_(is_short=True)

    def set_related_addr(self, data):
            self.country = None
            self.region = None
            self.city = None
            self.street = None
            try:
                name = data['country'].get('name')
                if name:
                    self.country, created = Country.objects.get_or_create(name=name)
                    name = data['region'].get('name')
                    if name:
                         self.region, created = Region.objects.get_or_create(name=name, country=self.country)
    
                         name = data['city'].get('name')
                         if name:
                             self.city, created = City.objects.get_or_create(name=name, region=self.region)
        
                             name = data['street'].get('name')
                             if name:
                                 self.street, created = Street.objects.get_or_create(name=name, city=self.city)
            except ValueError:
                pass
            self.save()

    def location_dict(self):
        if self.gps_y is not None and self.gps_x is not None:
            return dict(latitude=self.gps_y, longitude=self.gps_x)
        else:
            return None

    def get_yandex_coords(self):
        """
        Получить координаты места от yandex
        """
        location = None
        if self.addr_str:
            query = self.addr_str.strip()
        elif self.country and self.country.name:
            query = self.__unicode__()
        else:
            query = ''
        if len(query) > 3:
            try:
                query = urllib2.quote(query.encode('utf-8'))
                r = urllib2.urlopen(YANDEX_GEOCODE_URL % query, timeout=10)
                raw_data = r.read().decode(r.info().getparam('charset') or 'utf-8')
                data = json.loads(raw_data)
                pos  = data['response']['GeoObjectCollection']['featureMember'][0] \
                                ['GeoObject']['Point']['pos']
                longitude, latitude = pos.split()
                location = dict(
                    latitude=float(latitude),
                    longitude=float(longitude),
                )
            except (
                    urllib2.HTTPError,
                    urllib2.URLError,
                    IndexError,
                    KeyError,
                    ValueError,
                    AttributeError,
                   ):
                pass
        return location

class LocationMixin(object):

    def location_dict(self):
        if self.address:
            return self.address.location_dict()
        else:
            return None
