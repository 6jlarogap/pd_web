# coding=utf-8
from django.db import models
from django.utils.translation import ugettext_lazy as _

class Profile(models.Model):
    PLACE_CEMETERY = 'cemetery'
    PLACE_AREA = 'area'
    PLACE_ROW = 'row'
    PLACE_K2 = 'k2'
    PLACE_MANUAL = 'manual'
    PLACE_TYPES = (
        (PLACE_CEMETERY, _(u'По кладбищу')),
        (PLACE_AREA, _(u'По участку')),
        (PLACE_ROW, _(u'По ряду')),
        (PLACE_K2, _(u'Кладбище + год')),
        (PLACE_MANUAL, _(u'Ручное')),
    )

    user = models.OneToOneField('auth.User', editable=False, null=True)
    org = models.ForeignKey('users.Org', null=True)

    places_type = models.CharField(_(u"Номера мест"), max_length=255, choices=PLACE_TYPES, default=PLACE_MANUAL)
    is_agent = models.BooleanField(_(u"Агент"), default=False, blank=True)

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



