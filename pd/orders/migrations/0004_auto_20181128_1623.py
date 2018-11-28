# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_auto_20181128_1458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='customplace',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='persons.CustomPlace', null=True, verbose_name='\u0423\u0447\u0430\u0441\u0442\u043e\u043a \u0434\u043b\u044f \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='product',
            name='is_for_visit',
            field=models.BooleanField(default=False, verbose_name='\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u043e \u0434\u043b\u044f \u043f\u043e\u0441\u0435\u0449\u0435\u043d\u0438\u044f \u0443\u0447\u0430\u0441\u0442\u043a\u0430 \u0434\u043b\u044f \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f'),
            preserve_default=True,
        ),
    ]
