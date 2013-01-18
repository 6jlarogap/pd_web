# -*- coding: utf-8 -*-
import datetime

from django.db import models

from persons.models import Person
from utils.models import LengthValidator, NotEmptyValidator, DigitsValidator, VarLengthValidator

class Organization(models.Model):
    """
    Юридическое лицо.
    """
    ogrn = models.CharField(u"ОГРН/ОГРИП", max_length=15, blank=True)                                  # ОГРН
    inn = models.CharField(u"ИНН", max_length=12, blank=True, validators=[VarLengthValidator((10, 12)), DigitsValidator(), ])                                    # ИНН
    kpp = models.CharField(u"КПП", max_length=9, blank=True, validators=[DigitsValidator(), ])                                     # КПП
    name = models.CharField(u"Краткое название организации", max_length=99)                      # Название краткое
    full_name = models.CharField(u"Полное название организации", max_length=255, null=True)      # Название полное
    ceo = models.ForeignKey(Person, verbose_name=u"Директор", null=True, blank=True, limit_choices_to={'death_date__isnull': True})
    ceo_name_who = models.CharField(u"ФИО директора р.п.", max_length=255, null=True, blank=True, help_text=u'родительный падеж, напр. ИВАНОВА И.И.')
    ceo_document = models.CharField(u"Документ директора", max_length=255, null=True, blank=True, help_text=u'на основании чего? например, УСТАВА')
    phones = models.TextField(u"Телефоны", blank=True, null=True)
    location = models.ForeignKey('geo.Location', blank=True, null=True, verbose_name=u'Адрес')

    def __unicode__(self):
        return self.name or self.full_name or u'Unknown'

    def bank_account(self):
        try:
            return self.bankaccount_set.all()[0]
        except IndexError:
            return

    @property
    def ceo_name(self):
        return self.ceo and self.ceo.full_human_name() or ''

    class Meta:
        ordering = ['name']
        verbose_name = (u'юр. лицо')
        verbose_name_plural = (u'юр. лица')

class BankAccount(models.Model):
    """
    Банковские реквизиты
    """
    organization = models.ForeignKey(Organization, verbose_name=u"Организация")      # Владелец счета
    rs = models.CharField(u"Расчетный счет", max_length=20, validators=[DigitsValidator(), LengthValidator(20), ]) # Расчетный счет
    ks = models.CharField(u"Корреспондентский счет", max_length=20, blank=True, validators=[DigitsValidator(), LengthValidator(20), ]) # Корреспондентский счет
    bik = models.CharField(u"БИК", max_length=9, validators=[DigitsValidator(), LengthValidator(9), ])                         # Банковский идентификационный код
    bankname = models.CharField(u"Наименование банка", max_length=64, validators=[NotEmptyValidator(1), ])    # Название банка
    ls = models.CharField(u"Л/с", max_length=11, blank=True, null=True, validators=[LengthValidator(11), ])

class Agent(models.Model):
    person = models.ForeignKey(Person)
    organization = models.ForeignKey(Organization, related_name="agents", verbose_name="Организация")

    def __unicode__(self):
        return u'%s' % self.person

    def doverennost(self):
        try:
            return self.doverennosti.filter(expire_date__gt=datetime.datetime.now()).order_by('issue_date')[0]
        except IndexError:
            return

class Doverennost(models.Model):
    agent = models.ForeignKey(Agent, related_name="doverennosti", verbose_name="Доверенность*")

    number = models.CharField(verbose_name="Номер доверенности", max_length=255, null=True)
    issue_date = models.DateField(verbose_name="Дата выдачи", blank=True, null=True)
    expire_date = models.DateField(verbose_name="Действует до", blank=True, null=True)

    def __unicode__(self):
        id = self.issue_date and self.issue_date.strftime('%d.%m.%Y') or ''
        ed = self.expire_date and self.expire_date.strftime('%d.%m.%Y') or ''
        return u'%s (%s - %s) - %s' % (self.number, id, ed, self.agent)

    class Meta:
        ordering = ['-issue_date']
        verbose_name = (u'доверенность')
        verbose_name_plural = (u'доверенности')

