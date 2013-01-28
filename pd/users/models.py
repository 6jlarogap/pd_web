# coding=utf-8
from django.db import models
from django.utils.translation import ugettext_lazy as _

class Profile(models.Model):
    PROFILE_USER = 'user'
    PROFILE_LORU = 'loru'
    PROFILE_UGH = 'ugh'
    PROFILE_TYPES = (
        (PROFILE_LORU, _(u"ЛОРУ")),
        (PROFILE_UGH, _(u"УГХ")),
        (PROFILE_USER, _(u"Прочие"))
    )
    user = models.OneToOneField('auth.User', editable=False)
    type = models.CharField(_(u"Тип"), max_length=255, choices=PROFILE_TYPES)
    name = models.CharField(_(u"Название организации"), max_length=255)

    def __unicode__(self):
        return self.name

    def is_loru(self):
        return self.type == self.PROFILE_LORU

    def is_ugh(self):
        return self.type == self.PROFILE_UGH

    def is_user(self):
        return self.type == self.PROFILE_USER

class ProfileLORU(models.Model):
    ugh = models.ForeignKey(Profile, related_name='loru_list', limit_choices_to={'type': Profile.PROFILE_UGH}, verbose_name=_(u"УГХ"))
    loru = models.ForeignKey(Profile, related_name='ugh_list', limit_choices_to={'type': Profile.PROFILE_LORU}, verbose_name=_(u"ЛОРУ"))
