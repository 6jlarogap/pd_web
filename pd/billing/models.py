# coding: utf-8
from django.db import models
from django.utils.translation import ugettext as _

from users.models import Org

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
    org = models.ForeignKey(Org, verbose_name=_(u"Организация"))
    currency = models.ForeignKey(Currency, verbose_name=_(u"Валюта"))
    amount = models.DecimalField(_(u"Остаток"), max_digits=20, decimal_places=2, default='0.00')

    class Meta:
        verbose_name = _(u"Кошелек")
        verbose_name_plural = _(u"Кошельки")
        unique_together = ('org', 'currency',)

class Rate(models.Model):
    RATE_ACTION_SHOW = 'show'
    RATE_ACTION_UPDATE = 'update'
    RATE_ACTION_DISABLE = 'disable'
    RATE_ACTIONS = (
        (RATE_ACTION_SHOW, _(u"Показ")),
        (RATE_ACTION_UPDATE, _(u"Обновление")),
        (RATE_ACTION_DISABLE, _(u"Снятие с показа")),
    )

    wallet = models.ForeignKey(Wallet, verbose_name=_(u"Кошелек"))
    action = models.CharField(_(u"Действие"), max_length=255, choices=RATE_ACTIONS[:2])
    version = models.PositiveIntegerField(_(u"Версия"))
    rate = models.DecimalField(_(u"Тариф"), max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _(u"Тариф")
        verbose_name_plural = _(u"Тарифы")
        unique_together = ('wallet', 'action', 'version')

class Payment(models.Model):
    dt = models.DateTimeField(_(u"Дата/время"), auto_now_add=True)
    wallet_from = models.ForeignKey(Wallet, verbose_name=_(u"Кошелек откуда"), null=True)
    wallet_to = models.ForeignKey(Wallet, verbose_name=_(u"Кошелек куда"), null=True)
    amount = models.DecimalField(_(u"Сумма"), max_digits=20, decimal_places=2)
    comment = models.TextField(verbose_name=_(u"Примечание"), default='')
    ct = models.ForeignKey('contenttypes.ContentType', verbose_name=_(u"Вид платежа"))

class Io(models.Model):
    payment = models.OneToOneField(Payment)
    bank = models.CharField(_(u"Банк"), max_length=255)
    transaction = models.CharField(_(u"Банк"), max_length=255)

class Ad(models.Model):
    payment = models.OneToOneField(Payment)
    ugh = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_UGH}, verbose_name=_(u"ОМС"))
    product = models.ForeignKey('orders.Product', verbose_name=_(u"Продукт"))
    action = models.CharField(_(u"Действие"), max_length=255, choices=Rate.RATE_ACTIONS)
    # снятие с показа - тариф, null=True:
    rate = models.ForeignKey(Rate, verbose_name=_(u"Тариф"), null=True)

class Commission(models.Model):
    payment = models.OneToOneField(Payment)
    share = models.FloatField(_(u"Процент"))
