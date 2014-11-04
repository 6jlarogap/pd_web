# -*- coding: utf-8 -*-

import copy
from django.db import models
from django.utils.translation import ugettext as _
from django.db.models.deletion import ProtectedError
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

import datetime
from geo.models import Location
from pd.models import UnclearDate, UnclearDateModelField, BaseModel, Files, validate_phone_as_number
from users.models import Org, PhonesMixin

class IDDocumentType(models.Model):
    name = models.CharField(_(u"Тип документа"), max_length=255, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = (_(u"тип документа"))
        verbose_name_plural = (_(u"типы документов"))
        ordering = ('name', )

class BasePerson(models.Model):
    """
    Физическое лицо
    """
    last_name = models.CharField(_(u"Фамилия"), max_length=255, blank=True)
    first_name = models.CharField(_(u"Имя"), max_length=255, blank=True)
    middle_name = models.CharField(_(u"Отчество"), max_length=255, blank=True)
    birth_date = UnclearDateModelField(_(u"Дата рождения"), serialize=False, blank=True, null=True)

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
            self.personid.delete()
        except (AttributeError, PersonID.DoesNotExist, ProtectedError):
            pass
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

    def save(self, *args, **kwargs):
        uname = lambda s: (s[:1].upper() + s[1:]).strip(' ').strip('*')
        self.first_name = uname(self.first_name)
        self.last_name = uname(self.last_name)
        self.middle_name = uname(self.middle_name)
        super(BasePerson, self).save(*args, **kwargs)

    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name', ]
        verbose_name = _(u"физ. лицо")
        verbose_name_plural = _(u"физ. лица")

class DeadPerson(BasePerson):
    """
    Мертвое ФЛ
    """
    # serialize=False - не выгружать значение поля в фикстуры. Для этого типа поля не описан сериализатор
    death_date = UnclearDateModelField(_(u"Дата смерти"), serialize=False, blank=True, null=True)

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

    def delete(self):
        try:
            self.deathcertificate.delete()
        except (AttributeError, DeathCertificate.DoesNotExist, ProtectedError):
            pass
        try:
            super(DeadPerson, self).delete()
        except ProtectedError:
            pass

class AlivePerson(BasePerson, PhonesMixin):
    """
    Живое ФЛ с телефоном
    """
    phones = models.TextField(_(u"Телефоны"), blank=True, null=True)
    user = models.ForeignKey('auth.User', verbose_name=_(u"Ответственный за место или пользователь- физ. лицо"),
           null=True, editable=False)
    # Оставляем здесь login_phone как хранилище для телефона логина ответственного,
    # для сохранения черновиков захоронений, а также для удобства отображения в формах.
    # Реальный телефон логина ответственного см. в self.user and self.user.customerprofile.login_phone.
    # Если пользователь меняет login_phone, то копия его попадет и сюда, т.е. будет поддерживаться:
    # self.login_phone == self.user.customerprofile.login_phone
    #
    login_phone = models.DecimalField(_(u"Мобильный телефон для входа в кабинет"), max_digits=15, decimal_places=0,
                  blank=True, null=True, db_index=True,
                  help_text=_(u'В международном формате, начиная с кода страны, без "+", например 79101234567'),
                  validators = [validate_phone_as_number, ],
                  editable=False)

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

    def delete(self):
        try:
            self.deathcertificatescan.delete()
        except (AttributeError, DeathCertificateScan.DoesNotExist, ProtectedError):
            pass
        try:
            super(DeathCertificate, self).delete()
        except ProtectedError:
            pass

    def get_burial(self):
        """
        Получить захоронение, в котором усопший с этим СоС
        
        Имеется недостатки в проектировании таблиц б.д.:
        - теоретически может быть один усопший на несколько
          захоронений (Burial.deadman is a ForeignKey)
        - может быть усопший, но не "привязан" ни к какому
          захоронению
        Посему теоретически функция может вернуть или
        первого из нескольких захоронений этого усопшего,
        или вообще ничего не вернуть.
        """
        burial = None
        if self.pk:
            try:
                burial = self.person.burial_set.all()[0]
            except IndexError:
                pass
        return burial
        
class DeathCertificateScan(Files):
    """
    Файлы-сканы свидетельства о смерти, по одному на СоС
    """
    deathcertificate = models.OneToOneField(DeathCertificate)


PHONE_TYPE_MOBILE = 0
PHONE_TYPE_CITY = 1
PHONE_TYPE_FAX = 2

PHONE_TYPE_CHOICES = (
    (PHONE_TYPE_MOBILE, _(u"Мобильный")),
    (PHONE_TYPE_CITY, _(u"Городской")),
    (PHONE_TYPE_FAX, _(u"Факс"))
)


class Phone(BaseModel):
    ct = models.ForeignKey('contenttypes.ContentType', null=True, blank=True, editable=False, verbose_name=_(u"Тип"))
    obj_id = models.PositiveIntegerField(null=True, blank=True, editable=False, verbose_name=_(u"ID объекта"), db_index=True)
    obj = generic.GenericForeignKey(ct_field='ct', fk_field='obj_id')
    number = models.CharField(_(u"Номер"), max_length=50, blank=True)
    phonetype = models.SmallIntegerField(_(u"Тип телефона"), choices=PHONE_TYPE_CHOICES, default=PHONE_TYPE_CITY)

    class Meta:
        verbose_name = _(u"телефон")
        verbose_name_plural = _(u"Телефоны")

    def __unicode__(self):
         for k, v in PHONE_TYPE_CHOICES:  
             if k == self.phonetype:  
                 return _(u"%s: %s") % (v, self.number)

    @classmethod
    def create_default_phones(cls, instance, phones):
        """
        Создать массив телефонов с типом по умолчанию
        """
        instance.phone_set.delete()
        ct = ContentType.objects.get_for_model(instance)
        for phone in phones:
            cls.objects.create(
                ct=ct,
                obj_id=instance.pk,
                number=phone.lstrip('+'),
            )

class CustomPlace(BaseModel):
    address = models.ForeignKey(Location, verbose_name=_(u"Адрес"), null=True)
    user = models.ForeignKey('auth.User', verbose_name=_(u"Владелец или указавший место"))

class CustomPerson(BaseModel):
    """
    Человек, чаще усопший, но возможно живой
    """
    class Meta:
        ordering = ('last_name', 'first_name', 'middle_name', )

    last_name = models.CharField(_(u"Фамилия"), max_length=255, blank=True)
    first_name = models.CharField(_(u"Имя"), max_length=255, blank=True)
    middle_name = models.CharField(_(u"Отчество"), max_length=255, blank=True)
    birth_date = UnclearDateModelField(_(u"Дата рождения"), blank=True, null=True)
    death_date = UnclearDateModelField(_(u"Дата смерти"), blank=True, null=True)
    is_dead = models.BooleanField(_(u"Уcопший"), default=True)
    customplace = models.ForeignKey(CustomPlace, verbose_name=_(u"Место захоронения"), blank=True, null=True)
    memory_text = models.TextField(_(u"Памятный текст"), null=True)

class MemoryGallery(Files):
    """
    Страницы памяти у CustomPerson
    """
    TYPE_IMAGE = 'image'
    TYPE_VIDEO = 'video'
    TYPE_TEXT = 'text'
    TYPE_CHOICES = (
        (TYPE_IMAGE, _(u"Фото")),
        (TYPE_VIDEO, _(u"Видео")),
        (TYPE_TEXT, _(u"Текст"))
    )

    customperson = models.ForeignKey(CustomPerson)
    type = models.CharField(_(u"Тип"), max_length=255, choices=TYPE_CHOICES)
    text = models.TextField(_(u"Текст"), null=True)
    event_date = UnclearDateModelField(_(u"Дата события"), null=True)
