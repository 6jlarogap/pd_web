from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import Org

# Create your models here.

class Currency(models.Model):
    name = models.CharField(_("Название"), max_length=255)
    short_name = models.CharField(_("Сокращенное название"), max_length=255)
    code = models.CharField(_("Код"), max_length=10)
    rounding = models.SmallIntegerField(_("Округление"), default=2)
    icon = models.FileField("Иконка", upload_to='icons', blank=True, null=True)

    class Meta:
        verbose_name = _("Валюта")
        verbose_name_plural = _("Валюты")
        unique_together = ('code',)

    def __str__(self):
        return self.code

    def one_char_name(self):
        return self.short_name[:1] or 'р'

class Wallet(models.Model):
    org = models.ForeignKey(Org, verbose_name=_("Организация"), on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, verbose_name=_("Валюта"), on_delete=models.CASCADE)
    amount = models.DecimalField(_("Остаток"), max_digits=20, decimal_places=2, default='0.00')

    class Meta:
        verbose_name = _("Кошелек")
        verbose_name_plural = _("Кошельки")
        unique_together = ('org', 'currency',)

class Rate(models.Model):
    RATE_ACTION_PUBLISH = 'publish'
    RATE_ACTION_UPDATE = 'update'
    RATE_ACTION_DISABLE = 'disable'
    RATE_ACTIONS = (
        (RATE_ACTION_PUBLISH, _("Показ")),
        (RATE_ACTION_UPDATE, _("Обновление")),
        (RATE_ACTION_DISABLE, _("Снятие с показа")),
    )

    wallet = models.ForeignKey(Wallet, verbose_name=_("Кошелек"), on_delete=models.CASCADE)
    action = models.CharField(_("Действие"), max_length=255, choices=RATE_ACTIONS[:2])
    date_from = models.DateField(_("Дата начала действия тарифа"))
    rate = models.DecimalField(_("Тариф"), max_digits=20, decimal_places=2)

    class Meta:
        verbose_name = _("Тариф")
        verbose_name_plural = _("Тарифы")
        unique_together = ('wallet', 'action', 'date_from')

class Payment(models.Model):
    dt = models.DateTimeField(_("Дата/время"), auto_now_add=True)
    wallet_from = models.ForeignKey(Wallet, verbose_name=_("Кошелек откуда"), related_name='payment_from', null=True, on_delete=models.CASCADE)
    wallet_to = models.ForeignKey(Wallet, verbose_name=_("Кошелек куда"), related_name='payment_to', null=True, on_delete=models.CASCADE)
    amount = models.DecimalField(_("Сумма"), max_digits=20, decimal_places=2)
    comment = models.TextField(verbose_name=_("Примечание"), default='')
    ct = models.ForeignKey('contenttypes.ContentType', verbose_name=_("Вид платежа"), on_delete=models.CASCADE)

class Io(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    bank = models.CharField(_("Банк"), max_length=255)
    transaction = models.CharField(_("Транзакция"), max_length=255)

class Ad(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    ugh = models.ForeignKey(Org, limit_choices_to={'type': Org.PROFILE_UGH}, verbose_name=_("ОМС"), on_delete=models.CASCADE)
    product = models.ForeignKey('orders.Product', verbose_name=_("Продукт"), on_delete=models.CASCADE)
    action = models.CharField(_("Действие"), max_length=255, choices=Rate.RATE_ACTIONS)
    # снятие с показа - тариф, в котором null=True:
    rate = models.ForeignKey(Rate, verbose_name=_("Тариф"), null=True, on_delete=models.CASCADE)

class Commission(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    share = models.FloatField(_("Процент"))
    source_ct = models.ForeignKey('contenttypes.ContentType', verbose_name=_("Вид платежа, за что комиссия"), on_delete=models.CASCADE)
    source_id = models.PositiveIntegerField(verbose_name=_("ID платежа, за что комиссия"), db_index=True)
    source = GenericForeignKey('source_ct', 'source_id')
