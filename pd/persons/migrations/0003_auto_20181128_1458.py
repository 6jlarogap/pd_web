# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('persons', '0002_auto_20181122_1628'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aliveperson',
            name='user',
            field=models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0437\u0430 \u043c\u0435\u0441\u0442\u043e \u0438\u043b\u0438 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c- \u0444\u0438\u0437. \u043b\u0438\u0446\u043e'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customperson',
            name='customplace',
            field=models.ForeignKey(verbose_name='\u041c\u0435\u0441\u0442\u043e \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f', blank=True, to='persons.CustomPlace', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customplace',
            name='place',
            field=models.ForeignKey(verbose_name='\u041c\u0435\u0441\u0442\u043e', to='burials.Place', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customplace',
            name='user',
            field=models.ForeignKey(verbose_name='\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0437\u0430 \u043c\u0435\u0441\u0442\u043e \u0438\u043b\u0438 \u0443\u043a\u0430\u0437\u0430\u0432\u0448\u0438\u0439 \u043c\u0435\u0441\u0442\u043e', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
