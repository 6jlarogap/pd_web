# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _

import re

def cleanup_geo_name(s):
    s = s.capitalize()
    s = re.sub(u'(\.\s?)([\wа-я])', lambda m: u''.join(map(lambda g: g.capitalize(), m.groups())), s)
    return s

class Country(models.Model):
    """
    Страна.
    """

    name = models.CharField(_(u"Название"), max_length=255, db_index=True, unique=True)

    def __unicode__(self):
        return self.name[:16]

    def save(self, *args, **kwargs):
        if not self.pk:
            self.name = cleanup_geo_name(self.name)
        return super(Country, self).save(*args, **kwargs)

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

    def save(self, *args, **kwargs):
        if not self.pk:
            self.name = cleanup_geo_name(self.name)
        return super(Region, self).save(*args, **kwargs)

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

    def save(self, *args, **kwargs):
        if not self.pk:
            self.name = cleanup_geo_name(self.name)
        return super(City, self).save(*args, **kwargs)

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

    def save(self, *args, **kwargs):
        if not self.pk:
            self.name = cleanup_geo_name(self.name)
        return super(Street, self).save(*args, **kwargs)

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

    def __unicode__(self):
        if self.street or self.region:
            addr = u''
            if self.street:
                addr += u'%s' % self.street
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

            if addr:
                addr += u', %s' % (self.city or self.street and self.street.city or '')
            else:
                addr += u'%s' % (self.city or self.street and self.street.city or '')
            addr += u', %s' % (self.region or self.street and self.street.city.region or '')
            addr += u', %s' % (self.country or self.street and self.street.city.region.country or '')
            return addr.replace(', ,', ', ')
        else:
            return _(u"незаполненный адрес")