# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.query_utils import Q
from django.db.models.loading import get_model
from django.utils.translation import ugettext as _

from pd.models import BaseModel 

import re, urllib2, json

class GeoPointModel(BaseModel):
    """
    Базовая GEO модель
    """
    lat = models.FloatField(_(u"Широта"), blank=True, null=True)
    lng = models.FloatField(_(u"Долгота"), blank=True, null=True)

    class Meta:
        abstract = True

    def location_dict(self):
        return dict(latitude=self.lat, longitude=self.lng)

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
        return self.name[:16]

    @classmethod
    def get_country_currency_by_coords(cls, gps_x, gps_y):
        """
        Получить страну, валюту по координатам
        """

        DOMAINS = dict(
            ru=dict(name=u'Россия', currency='RUR',),
            by=dict(name=u'Беларусь', currency='BYR',),
        )
        YANDEX_GEOCODE_URL = "http://geocode-maps.yandex.ru/1.x/?geocode=%s,%s&format=json&results=1"

        result = None, None
        if gps_x is None or gps_y is None:
            return result
        try:
            r = urllib2.urlopen(YANDEX_GEOCODE_URL % (
                gps_x,
                gps_y,
            ))
            raw_data = r.read().decode(r.info().getparam('charset') or 'utf-8')
        except (urllib2.HTTPError, urllib2.URLError):
            return result
        try:
            data = json.loads(raw_data)
            country = data['response']['GeoObjectCollection']['featureMember'][0]\
                        ['GeoObject']['metaDataProperty']['GeocoderMetaData']\
                        ['AddressDetails']['Country']
            country_parms = DOMAINS[country['CountryNameCode'].lower()]
            country_name = country_parms['name']
            currency_code = country_parms['currency']
            country, created_country = cls.objects.get_or_create(name=country_name)
            Currency = models.get_model('billing', 'Currency')
            currency, created_currency = Currency.objects.get_or_create(code=currency_code)
        except (KeyError, ValueError):
            return result
        return country, currency

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

    def __unicode__(self):
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
            return _(u"незаполненный адрес")

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
        return dict(latitude=self.gps_y, longitude=self.gps_x)

    @classmethod
    def empty_location_dict(cls):
        return dict(latitude=None, longitude=None)
