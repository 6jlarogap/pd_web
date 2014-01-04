# coding: utf-8
from django.db import models
from django.utils.translation import ugettext as _

# Create your models here.

class Currency(models.Model):
    name = models.CharField(_(u"Название"), max_length=255)
    code = models.CharField(_(u"Код"), max_length=10)
    icon = models.FileField(u"Иконка", upload_to='icons', blank=True, null=True)
