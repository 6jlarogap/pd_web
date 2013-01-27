# coding=utf-8
from django.db import models

class Profile(models.Model):
    PROFILE_LORU = 'loru'
    PROFILE_UGH = 'ugh'
    PROFILE_TYPES = (
        (PROFILE_LORU, u"ЛОРУ"),
        (PROFILE_UGH, u"УГХ"),
    )
    user = models.OneToOneField('auth.User')
    type = models.CharField(u"Тип", max_length=255, choices=PROFILE_TYPES)
    name = models.CharField(u"Название организации", max_length=255)

    def is_loru(self):
        return self.type == self.PROFILE_LORU

    def is_ugh(self):
        return self.type == self.PROFILE_UGH

