# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _

import datetime
from geo.models import Location
from pd.utils import UnclearDate
from users.models import Org


class IDDocumentType(models.Model):
    name = models.CharField(_(u"Тип документа"), max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = (_(u"тип документа"))
        verbose_name_plural = (_(u"типы документов"))

class BasePerson(models.Model):
    """
    Физическое лицо
    """
    last_name = models.CharField(_(u"Фамилия"), max_length=255, blank=True)
    first_name = models.CharField(_(u"Имя"), max_length=255, blank=True)
    middle_name = models.CharField(_(u"Отчество"), max_length=255, blank=True)

    birth_date = models.DateField(_(u"Дата рождения"), blank=True, null=True)
    birth_date_no_month = models.BooleanField(default=False, editable=False)
    birth_date_no_day = models.BooleanField(default=False, editable=False)

    address = models.ForeignKey(Location, editable=False, null=True)

    def __unicode__(self):
        if self.last_name.strip():
            result = self.last_name
            if self.first_name:
                result += " %s" % self.first_name
                if self.middle_name:
                    result += " %s" % self.middle_name
        else:
            result = _(u"Неизвестный")
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
        return fio.strip() or _(u"Неизвестный")

    def save(self, *args, **kwargs):
        self.first_name = self.first_name.capitalize().strip(' ').strip('*')
        self.last_name = self.last_name.capitalize().strip(' ').strip('*')
        self.middle_name = self.middle_name.capitalize().strip(' ').strip('*')
        super(BasePerson, self).save(*args, **kwargs)

    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name', ]
        verbose_name = _(u"физ. лицо")
        verbose_name_plural = _(u"физ. лица")

class DeadPerson(BasePerson):
    """
    Мертвое ФЛ
    """
    death_date = models.DateField(_(u"Дата смерти"), blank=True, null=True)
    death_date_no_month = models.BooleanField(default=False, editable=False)
    death_date_no_day = models.BooleanField(default=False, editable=False)

    def get_death_date(self):
        if not self.death_date:
            return None
        death_date = UnclearDate(self.death_date.year, self.death_date.month, self.death_date.day)
        if self.death_date_no_day:
            death_date.day = None
        if self.death_date_no_month:
            death_date.month = None
        return death_date

    def set_death_date(self, ubd):
        self.death_date = ubd
        if ubd:
            if ubd.no_day:
                self.death_date_no_day = True
            if ubd.no_month:
                self.death_date_no_month = True

    unclear_death_date = property(get_death_date, set_death_date)

class AlivePerson(BasePerson):
    """
    Живое ФЛ с телефоном
    """
    phones = models.TextField(_(u"Телефоны"), blank=True, null=True)

class DocumentSource(models.Model):
    name = models.CharField(_(u"Наименование органа"), max_length=255, unique=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super(DocumentSource, self).save(*args, **kwargs)

class PersonID(models.Model):
    """
    Удостоверение личности
    """

    person = models.OneToOneField(BasePerson)
    id_type = models.ForeignKey(IDDocumentType, verbose_name=_(u"Тип документа"))
    series = models.CharField(_(u"Серия*"), max_length=255)
    number = models.CharField(_(u"Номер*"), max_length=255)
    source = models.ForeignKey(DocumentSource, verbose_name=_(u"Кем выдан"), blank=True, null=True)
    date = models.DateField(_(u"Дата выдачи"), blank=True, null=True)

    def save(self, *args, **kwargs):
        self.series = self.series.upper()
        super(PersonID, self).save(*args, **kwargs)

class DeathCertificate(models.Model):
    """
    Свидетельство о смерти.
    """

    person = models.OneToOneField(DeadPerson)

    s_number = models.CharField(_(u"Номер"), max_length=255, blank=True, null=True)
    series = models.CharField(_(u"Серия"), max_length=255, blank=True, null=True)
    release_date = models.DateField(_(u"Дата выдачи"), null=True, blank=True)
    zags = models.ForeignKey(Org, verbose_name=_(u"ЗАГС*"), null=True, limit_choices_to={'type': Org.PROFILE_ZAGS})

    def __unicode__(self):
        return _(u"Свид. о смерти (%s)") % self.person.__unicode__()

    class Meta:
        verbose_name = (_(u"свидетельство о смерти"))
        verbose_name_plural = (_(u"свидетельства о смерти"))

    def save(self, *args, **kwargs):
        self.series = self.series.upper()
        super(DeathCertificate, self).save(*args, **kwargs)
