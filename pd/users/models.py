# coding=utf-8
from django.db import models
from django.utils.translation import ugettext_lazy as _

from geo.models import DFiasAddrobj


class Profile(models.Model):

    user = models.OneToOneField('auth.User', editable=False, null=True)
    org = models.ForeignKey('users.Org', null=True)

    is_agent = models.BooleanField(_(u"Агент"), default=False, blank=True)

    cemetery = models.ForeignKey('burials.Cemetery', verbose_name=_(u"Кладбище"), blank=True, null=True)
    area = models.ForeignKey('burials.Area', verbose_name=_(u"Участок"), blank=True, null=True)

    country = models.ForeignKey('geo.Country', verbose_name=_(u"Страна"), blank=True, null=True)
    region_fias = models.CharField(_(u"Регион"), blank=True, null=True, max_length=255)

    lat = models.DecimalField(max_digits=30, decimal_places=27, blank=True, null=True)
    lng = models.DecimalField(max_digits=30, decimal_places=27, blank=True, null=True)

    def __unicode__(self):
        return self.user and (self.user.get_full_name() or self.user.username) or u'%s' % self.pk

    def is_loru(self):
        return self.org and self.org.type == Org.PROFILE_LORU

    def is_ugh(self):
        return self.org and self.org.type == Org.PROFILE_UGH

    def can_create_burials(self):
        return self.is_ugh() or self.is_loru()

    def full_name(self):
        return self.user.get_full_name()

    def get_region(self):
        if self.region_fias:
            return DFiasAddrobj.objects.get(parentguid='', aoguid=self.region_fias)

    def get_coords(self):
        if self.lat and self.lng:
            return ','.join([self.lat, self.lng])
        return ''

class Org(models.Model):
    PROFILE_ZAGS = 'zags'
    PROFILE_LORU = 'loru'
    PROFILE_UGH = 'ugh'
    PROFILE_TYPES = (
        (PROFILE_LORU, _(u"ЛОРУ")),
        (PROFILE_UGH, _(u"УГХ")),
        (PROFILE_ZAGS, _(u"ЗАГС")),
    )

    type = models.CharField(_(u"Тип"), max_length=255, choices=PROFILE_TYPES)
    name = models.CharField(_(u"Название организации"), max_length=255, default='')
    full_name = models.CharField(_(u"Полное название"), max_length=255, default='')
    inn = models.CharField(_(u"ИНН"), max_length=255, default='')
    director = models.CharField(_(u"Директор"), max_length=255, default='')
    email = models.EmailField(_(u"Email"), null=True, blank=True)

    class Meta:
        verbose_name = _(u'Организация')
        verbose_name_plural = _(u'Организации')

    def __unicode__(self):
        return self.name

class ProfileLORU(models.Model):
    ugh = models.ForeignKey(Org, related_name='loru_list', limit_choices_to={'type': Org.PROFILE_UGH}, verbose_name=_(u"УГХ"))
    loru = models.ForeignKey(Org, related_name='ugh_list', limit_choices_to={'type': Org.PROFILE_LORU}, verbose_name=_(u"ЛОРУ"))

class Dover(models.Model):
    agent = models.ForeignKey(Profile, verbose_name=_(u"Агент"), limit_choices_to={'is_agent': True})
    number = models.CharField(_(u"Номер"), max_length=255)
    begin = models.DateField(_(u"Начало"))
    end = models.DateField(_(u"Окончание"))
    document = models.FileField(_(u"Скан доверенности"), upload_to='dover', blank=True, null=True)

    class Meta:
        verbose_name = _(u'Доверенность')
        verbose_name_plural = _(u'Доверенности')

    def __unicode__(self):
        return u'%s (%s - %s)' % (self.number, self.begin.strftime('%d.%m.%Y'), self.end.strftime('%d.%m.%Y'))



