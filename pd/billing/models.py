# coding: utf-8
from django.db import models
from django.utils.translation import ugettext as _

# Create your models here.

class Currency(models.Model):
    name = models.CharField(_(u"Название"), max_length=255)
    short_name = models.CharField(_(u"Сокращенное название"), max_length=255)
    code = models.CharField(_(u"Код"), max_length=10)
    icon = models.FileField(u"Иконка", upload_to='icons', blank=True, null=True)

    class Meta:
        verbose_name = _(u"Валюта")
        verbose_name_plural = _(u"Валюты")

    def __unicode__(self):
        return self.name

class Wallet(models.Model):
    org = models.ForeignKey('users.Org', verbose_name=_(u"Организация"))
    currency = models.ForeignKey(Currency, verbose_name=_(u"Валюта"))
    amount = models.DecimalField(_(u"Остаток"), max_digits=20, decimal_places=2, default='0.00')

    class Meta:
        verbose_name = _(u"Кошелек")
        verbose_name_plural = _(u"Кошельки")
        unique_together = ('org', 'currency',)

class Rate(models.Model):
    RATE_ACTION_SHOW = 'show'
    RATE_ACTION_UPDATE = 'update'
    RATE_ACTIONS = (
        (RATE_ACTION_SHOW, _(u"Показ")),
        (RATE_ACTION_UPDATE, _(u"Обновление")),
    )

    wallet = models.ForeignKey(Wallet, verbose_name=_(u"Кошелек"))
    action = models.CharField(_(u"Действие"), max_length=255, choices=RATE_ACTIONS)
    version = models.PositiveIntegerField(_(u"Версия"), editable=False)
    rate = models.DecimalField(_(u"Тариф"), max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _(u"Тариф")
        verbose_name_plural = _(u"Тарифы")
        unique_together = ('wallet', 'action', 'version')

class WalletLog(models.Model):
    dt = models.DateTimeField(_(u"Дата/время"), auto_now_add=True)
    wallet_from = models.ForeignKey(Wallet, verbose_name=_(u"Кошелек"), null=True)
    wallet_to = models.ForeignKey(Wallet, verbose_name=_(u"Кошелек"), null=True)
    amount = models.DecimalField(_(u"Сумма"), max_digits=20, decimal_places=2)
    comment = models.TextField(verbose_name=_(u"Примечание"), default='')
