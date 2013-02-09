# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext as _

import re

class Country(models.Model):
    """
    Страна.
    """

    name = models.CharField(_(u"Название"), max_length=255, db_index=True, unique=True)

    def __unicode__(self):
        return self.name[:16]

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
        if self.street or self.region:
            addr = u''
            if self.street:
                addr += u'%s' % self.street
            addr = self.get_local_addr(addr)

            if addr:
                addr += u', %s' % (self.city or self.street and self.street.city or '')
            else:
                addr += u'%s' % (self.city or self.street and self.street.city or '')
            addr += u', %s' % (self.region or self.street and self.street.city.region or '')
            addr += u', %s' % (self.country or self.street and self.street.city.region.country or '')
            return addr.replace(', ,', ', ')
        elif self.fias_parents.all():
            addr = u", ".join(map(unicode, self.fias_parents.all()))
            return self.get_local_addr(addr)
        else:
            return _(u"незаполненный адрес")

class LocationFIAS(models.Model):
    loc = models.ForeignKey(Location, related_name='fias_parents')
    guid = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=255)
    level = models.PositiveSmallIntegerField(db_index=True)

    class Meta:
        ordering = ['level', ]

    def __unicode__(self):
        return self.name

class DFiasAddrobj(models.Model):
    """
    Импорт из ФИАС
    """
    aoid = models.CharField(max_length=108, primary_key=True)
    formalname = models.CharField(max_length=360)
    regioncode = models.CharField(max_length=6)
    autocode = models.CharField(max_length=3)
    areacode = models.CharField(max_length=9)
    citycode = models.CharField(max_length=9)
    ctarcode = models.CharField(max_length=9)
    placecode = models.CharField(max_length=9)
    streetcode = models.CharField(max_length=12)
    extrcode = models.CharField(max_length=12)
    sextcode = models.CharField(max_length=9)
    offname = models.CharField(max_length=360)
    postalcode = models.CharField(max_length=18)
    ifnsfl = models.CharField(max_length=12)
    terrifnsfl = models.CharField(max_length=12)
    ifnsul = models.CharField(max_length=12)
    terrifnsul = models.CharField(max_length=12)
    okato = models.CharField(max_length=33)
    oktmo = models.CharField(max_length=24)
    updatedate = models.DateField()
    shortname = models.CharField(max_length=30)
    aolevel = models.IntegerField()
    parentguid = models.CharField(max_length=108)
    aoguid = models.CharField(max_length=108)
    previd = models.CharField(max_length=108)
    nextid = models.CharField(max_length=108)
    code = models.CharField(max_length=51)
    plaincode = models.CharField(max_length=45)
    actstatus = models.IntegerField()
    centstatus = models.IntegerField()
    operstatus = models.IntegerField()
    currstatus = models.IntegerField()
    startdate = models.DateField()
    enddate = models.DateField()
    normdoc = models.CharField(max_length=108)

    class Meta:
        db_table = u'd_fias_addrobj'

    def __unicode__(self):
        return u'%s %s' % (self.offname, self.shortname)