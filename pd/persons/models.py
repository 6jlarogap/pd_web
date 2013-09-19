# -*- coding: utf-8 -*-

import copy
from django.db import models
from django.utils.translation import ugettext as _
from django.db.models.deletion import ProtectedError

import datetime
from geo.models import Location
from pd.models import UnclearDate, UnclearDateModelField, BaseModel, Files
from users.models import Org

class SafeDeleteMixin(object):
    
    def safe_delete(self, field_name, instance):
        """
        Безопасно удалить что-то из записи таблицы
        
        field       - строка (!) имени поля
        instance    - запись в таблице
        Поле устанавливается в null, запись сохраняется, потом
        удаляется то, на что указывало поле.
        Типичный пример - удаление заявителя, заказчика, покойника.
        """
        field_to_delete = getattr(instance, field_name)
        if field_to_delete:
            setattr(instance, field_name, None)
            instance.save()
            try:
                field_to_delete.delete()
            except ProtectedError:
                pass

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

    def delete(self):
        try:
            super(BasePerson, self).delete()
        except ProtectedError:
            pass
        else:
            try:
                self.address.delete()
            except (AttributeError, ProtectedError):
                pass

    def deep_copy(self):
        new_person_addr = None
        if self.address:
            new_person_addr = copy.deepcopy(self.address)
            new_person_addr.id = None
            new_person_addr.save(force_insert=True)
        new_person = copy.deepcopy(self)
        new_person.id = None
        try:
            new_person.baseperson_ptr_id = None
        except AttributeError:
            pass
        new_person.address = new_person_addr
        new_person.save(force_insert=True)
        try:
            new_person_pid = copy.deepcopy(self.personid)
            new_person_pid.id = None
            new_person_pid.person = new_person
            new_person_pid.save(force_insert=True)
        except PersonID.DoesNotExist:
            pass
        return new_person

    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name', ]
        verbose_name = _(u"физ. лицо")
        verbose_name_plural = _(u"физ. лица")

class DeadPerson(BasePerson):
    """
    Мертвое ФЛ
    """
    birth_date = UnclearDateModelField(_(u"Дата рождения"), blank=True, null=True)
    death_date = UnclearDateModelField(_(u"Дата смерти"), blank=True, null=True)

    def save(self, *args, **kwargs):
        self.first_name = self.first_name.capitalize().strip(' ').strip('*')
        self.last_name = self.last_name.capitalize().strip(' ').strip('*')
        self.middle_name = self.middle_name.capitalize().strip(' ').strip('*')
        super(DeadPerson, self).save(*args, **kwargs)

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

    def save(self, *args, **kwargs):
        self.first_name = self.first_name.capitalize().strip(' ').strip('*')
        self.last_name = self.last_name.capitalize().strip(' ').strip('*')
        self.middle_name = self.middle_name.capitalize().strip(' ').strip('*')
        super(AlivePerson, self).save(*args, **kwargs)

class DocumentSource(models.Model):
    name = models.CharField(_(u"Наименование органа"), max_length=255, unique=True)

    def __unicode__(self):
        return self.name

class PersonID(models.Model):
    """
    Удостоверение личности
    """

    person = models.OneToOneField(BasePerson)
    id_type = models.ForeignKey(IDDocumentType, verbose_name=_(u"Тип документа"), blank=True, null=True)
    series = models.CharField(_(u"Серия"), max_length=255, blank=True, null=True)
    number = models.CharField(_(u"Номер"), max_length=255, blank=True, null=True)
    source = models.ForeignKey(DocumentSource, verbose_name=_(u"Кем выдан"), blank=True, null=True)
    date = models.DateField(_(u"Дата выдачи"), blank=True, null=True)

    class Meta:
        verbose_name = _(u"Удостоверение личности")
        verbose_name_plural = _(u"Удостоверения личности")

    def __unicode__(self):
        return _(u"%s %s %s") % (self.id_type, self.series, self.number)

    def save(self, *args, **kwargs):
        self.series = self.series.upper()
        super(PersonID, self).save(*args, **kwargs)

class DeathCertificate(BaseModel):
    """
    Свидетельство о смерти.
    """

    person = models.OneToOneField(DeadPerson)

    s_number = models.CharField(_(u"Номер"), max_length=255, blank=True, null=True)
    series = models.CharField(_(u"Серия"), max_length=255, blank=True, null=True)
    release_date = models.DateField(_(u"Дата выдачи"), null=True, blank=True)
    zags = models.ForeignKey(Org, verbose_name=_(u"ЗАГС"), null=True, blank=True, limit_choices_to={'type': Org.PROFILE_ZAGS})

    class Meta:
        verbose_name = _(u"свидетельство о смерти")
        verbose_name_plural = _(u"свидетельства о смерти")

    def __unicode__(self):
        return _(u"Свид. о смерти (%s)") % self.person.__unicode__()

    def save(self, *args, **kwargs):
        self.series = self.series.upper()
        super(DeathCertificate, self).save(*args, **kwargs)

class DeathCertificateScan(Files):
    """
    Файлы-сканы свидетельства о смерти, по одному на СоС
    """
    deathcertificate = models.OneToOneField(DeathCertificate)

