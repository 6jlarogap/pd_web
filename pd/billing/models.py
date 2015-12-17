# coding: utf-8
from django.contrib.contenttypes import generic
from django.db import models
from django.utils.translation import ugettext as _

from users.models import Org

# Create your models here.

class Currency(models.Model):
    name = models.CharField(_(u"Название"), max_length=255)
    short_name = models.CharField(_(u"Сокращенное название"), max_length=255)
    code = models.CharField(_(u"Код"), max_length=10)
    rounding = models.SmallIntegerField(_(u"Округление"), default=2)
    icon = models.FileField(u"Иконка", upload_to='icons', blank=True, null=True)

    class Meta:
        verbose_name = _(u"Валюта")
        verbose_name_plural = _(u"Валюты")
        unique_together = ('code',)

    def __unicode__(self):
        return self.code

    def one_char_name(self):
        return self.short_name[:1] or u'р'

class Wallet(models.Model):
    org = models.ForeignKey(Org, verbose_name=_(u"Организация"))
    currency = models.ForeignKey(Currency, verbose_name=_(u"Валюта"))
    amount = models.DecimalField(_(u"Остаток"), max_digits=20, decimal_places=2, default='0.00')

    class Meta:
        verbose_name = _(u"Кошелек")
        verbose_name_plural = _(u"Кошельки")
        unique_together = ('org', 'currency',)

class Rate(models.Model):
    RATE_ACTION_PUBLISH = 'publish'
    RATE_ACTION_UPDATE = 'update'
    RATE_ACTION_DISABLE = 'disable'
    RATE_ACTIONS = (
        (RATE_ACTION_PUBLISH, _(u"Показ")),
        (RATE_ACTION_UPDATE, _(u"Обновление")),
        (RATE_ACTION_DISABLE, _(u"Снятие с показа")),
    )

    wallet = models.ForeignKey(Wallet, verbose_name=_(u"Кошелек"))
    action = models.CharField(_(u"Действие"), max_length=255, choices=RATE_ACTIONS[:2])
    date_from = models.DateField(_(u"Дата начала действия тарифа"))
    rate = models.DecimalField(_(u"Тариф"), max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _(u"Тариф")
        verbose_name_plural = _(u"Тарифы")
        unique_together = ('wallet', 'action', 'date_from')

class Payment(models.Model):
    dt = models.DateTimeField(_(u"Дата/время"), auto_now_add=True)
    wallet_from = models.ForeignKey(Wallet, verbose_name=_(u"Кошелек откуда"), related_name='payment_from', null=True)
    wallet_to = models.ForeignKey(Wallet, verbose_name=_(u"Кошелек куда"), related_name='payment_to', null=True)
    amount = models.DecimalField(_(u"Сумма"), max_digits=20, decimal_places=2)
    comment = models.TextField(verbose_name=_(u"Примечание"), default='')
    ct = models.ForeignKey('contenttypes.ContentType', verbose_name=_(u"Вид платежа"))

class Io(models.Model):
    payment = models.OneToOneField(Payment)
    bank = models.CharField(_(u"Банк"), max_length=255)
    transaction = models.CharField(_(u"Транзакция"), max_length=255)

class Ad(models.Model):
    payment = models.OneToOneField(Payment)
    ugh = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_UGH}, verbose_name=_(u"ОМС"))
    product = models.ForeignKey('orders.Product', verbose_name=_(u"Продукт"))
    action = models.CharField(_(u"Действие"), max_length=255, choices=Rate.RATE_ACTIONS)
    # снятие с показа - тариф, в котором null=True:
    rate = models.ForeignKey(Rate, verbose_name=_(u"Тариф"), null=True)

class Commission(models.Model):
    payment = models.OneToOneField(Payment)
    share = models.FloatField(_(u"Процент"))
    source_ct = models.ForeignKey('contenttypes.ContentType', verbose_name=_(u"Вид платежа, за что комиссия"))
    source_id = models.PositiveIntegerField(verbose_name=_(u"ID платежа, за что комиссия"), db_index=True)
    source = generic.GenericForeignKey('source_ct', 'source_id')
