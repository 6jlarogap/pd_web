# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_auto_20181129_1401'),
        ('users', '0001_initial'),
        ('billing', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallet',
            name='org',
            field=models.ForeignKey(verbose_name='\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f', to='users.Org'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='wallet',
            unique_together=set([('org', 'currency')]),
        ),
        migrations.AddField(
            model_name='rate',
            name='wallet',
            field=models.ForeignKey(verbose_name='\u041a\u043e\u0448\u0435\u043b\u0435\u043a', to='billing.Wallet'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='rate',
            unique_together=set([('wallet', 'action', 'date_from')]),
        ),
        migrations.AddField(
            model_name='payment',
            name='ct',
            field=models.ForeignKey(verbose_name='\u0412\u0438\u0434 \u043f\u043b\u0430\u0442\u0435\u0436\u0430', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='payment',
            name='wallet_from',
            field=models.ForeignKey(related_name='payment_from', verbose_name='\u041a\u043e\u0448\u0435\u043b\u0435\u043a \u043e\u0442\u043a\u0443\u0434\u0430', to='billing.Wallet', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='payment',
            name='wallet_to',
            field=models.ForeignKey(related_name='payment_to', verbose_name='\u041a\u043e\u0448\u0435\u043b\u0435\u043a \u043a\u0443\u0434\u0430', to='billing.Wallet', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='io',
            name='payment',
            field=models.OneToOneField(to='billing.Payment'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='currency',
            unique_together=set([('code',)]),
        ),
        migrations.AddField(
            model_name='commission',
            name='payment',
            field=models.OneToOneField(to='billing.Payment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='commission',
            name='source_ct',
            field=models.ForeignKey(verbose_name='\u0412\u0438\u0434 \u043f\u043b\u0430\u0442\u0435\u0436\u0430, \u0437\u0430 \u0447\u0442\u043e \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u044f', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ad',
            name='payment',
            field=models.OneToOneField(to='billing.Payment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ad',
            name='product',
            field=models.ForeignKey(verbose_name='\u041f\u0440\u043e\u0434\u0443\u043a\u0442', to='orders.Product'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ad',
            name='rate',
            field=models.ForeignKey(verbose_name='\u0422\u0430\u0440\u0438\u0444', to='billing.Rate', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ad',
            name='ugh',
            field=models.ForeignKey(verbose_name='\u041e\u041c\u0421', to='users.Org'),
            preserve_default=True,
        ),
    ]
