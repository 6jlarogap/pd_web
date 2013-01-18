# -*- coding: utf-8 -*-

from django.db import models

import datetime
from geo.models import Location
from utils.models import UnclearDate

class IDDocumentType(models.Model):
    name = models.CharField(u"Тип документа", max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = (u'тип документа')
        verbose_name_plural = (u'типы документов')

class Person(models.Model):
    """
    Физическое лицо (клиент, сотрудник, кто угодно).
    """
    user = models.ForeignKey('auth.User', editable=False, null=True)

    last_name = models.CharField(u"Фамилия", max_length=255, blank=True)  # Фамилия.
    first_name = models.CharField(u"Имя", max_length=255, blank=True)  # Имя.
    middle_name = models.CharField(u"Отчество", max_length=255, blank=True)  # Отчество.

    birth_date = models.DateField(u"Дата рождения", blank=True, null=True)
    birth_date_no_month = models.BooleanField(default=False, editable=False)
    birth_date_no_day = models.BooleanField(default=False, editable=False)
    death_date = models.DateField(u"Дата смерти", blank=True, null=True)

    address = models.ForeignKey(Location, editable=False, null=True)
    phones = models.TextField(u"Телефоны", blank=True, null=True)

    def __unicode__(self):
        if self.last_name.strip():
            result = self.last_name
            if self.first_name:
                result += " %s" % self.first_name
                if self.middle_name:
                    result += " %s" % self.middle_name
        else:
            result = u'Неизвестный'
        return result

    def get_birth_date(self):
        if not self.birth_date:
            return None
        birth_date = UnclearDate(self.birth_date.year, self.birth_date.month, self.birth_date.day)
        if self.birth_date_no_day:
            birth_date.day = None
        if self.birth_date_no_month:
            birth_date.month = None
        return birth_date

    def set_birth_date(self, ubd):
        self.birth_date = ubd
        if ubd:
            if ubd.no_day:
                self.birth_date_no_day = True
            if ubd.no_month:
                self.birth_date_no_month = True

    unclear_birth_date = property(get_birth_date, set_birth_date)

    def unclear_birth_date_str(self):
        return self.unclear_birth_date and self.unclear_birth_date.strftime('%d.%m.%Y') or ''

    def full_human_name(self):
        return ' '.join((self.last_name, self.first_name, self.middle_name)).strip()

    def age(self):
        start = self.birth_date
        finish = (self.death_date or datetime.date.today())
        return int((finish - start).days / 365.25)

    def get_initials(self):
        initials = u""
        if self.first_name:
            initials = u"%s." % self.first_name[:1].upper()
            if self.middle_name:
                initials = u"%s%s." % (initials, self.middle_name[:1].upper())
        return initials

    def full_name(self):
        fio = u"%s %s" % (self.last_name, self.get_initials())
        return fio.strip()

    def full_name_complete(self):
        fio = u"%s %s %s" % (self.last_name, self.first_name, self.middle_name)
        return fio.strip() or u"Неизвестный"

    def save(self, *args, **kwargs):
        if self.user:
            if not self.last_name:
                self.last_name = self.user.last_name
            if not self.first_name:
                self.first_name = self.user.first_name
        self.first_name = self.first_name.capitalize().strip(' ').strip('*')
        self.last_name = self.last_name.capitalize().strip(' ').strip('*')
        self.middle_name = self.middle_name.capitalize().strip(' ').strip('*')
        super(Person, self).save(*args, **kwargs)

    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name', ]
        verbose_name = (u'физ. лицо')
        verbose_name_plural = (u'физ. лица')

class DocumentSource(models.Model):
    name = models.CharField(u"Наименование органа", max_length=255, unique=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super(DocumentSource, self).save(*args, **kwargs)

class PersonID(models.Model):
    person = models.OneToOneField(Person)
    id_type = models.ForeignKey(IDDocumentType, verbose_name=u"Тип документа*")
    series = models.CharField(u"Серия*", max_length=255, null=True)
    number = models.CharField(u"Номер*", max_length=255)
    source = models.ForeignKey(DocumentSource, verbose_name=u"Кем выдан", blank=True, null=True)
    date = models.DateField(u"Дата выдачи", blank=True, null=True)

    def save(self, *args, **kwargs):
        self.series = self.series.upper()
        super(PersonID, self).save(*args, **kwargs)

class ZAGS(models.Model):
    name = models.CharField(u"Название", max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = (u'ЗАГС')
        verbose_name_plural = (u'ЗАГС')

class DeathCertificate(models.Model):
    """
    Свидетельство о смерти.
    """

    person = models.OneToOneField(Person)

    s_number = models.CharField(u"Номер", max_length=255, blank=True, null=True)
    series = models.CharField(u"Серия", max_length=255, blank=True, null=True)
    release_date = models.DateField(u"Дата выдачи", null=True, blank=True)
    zags = models.ForeignKey(ZAGS, verbose_name=u"ЗАГС*", null=True)

    def __unicode__(self):
        return u"Свид. о смерти (%s)" % self.soul.__unicode__()

    class Meta:
        verbose_name = (u'свидетельство о смерти')
        verbose_name_plural = (u'свидетельства о смерти')

    def save(self, *args, **kwargs):
        self.series = self.series.upper()
        super(DeathCertificate, self).save(*args, **kwargs)

