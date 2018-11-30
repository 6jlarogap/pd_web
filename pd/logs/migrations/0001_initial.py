# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DeleteLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('obj_id', models.PositiveIntegerField(verbose_name='ID \u043e\u0431\u044a\u0435\u043a\u0442\u0430', editable=False)),
                ('dt', models.DateTimeField(auto_now_add=True, verbose_name='\u0412\u0440\u0435\u043c\u044f', db_index=True)),
                ('parent_id', models.PositiveIntegerField(verbose_name='ID \u0440\u043e\u0434\u0438\u0442\u0435\u043b\u044f', null=True, editable=False, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('obj_id', models.PositiveIntegerField(verbose_name='ID \u043e\u0431\u044a\u0435\u043a\u0442\u0430', null=True, editable=False, db_index=True)),
                ('dt', models.DateTimeField(auto_now_add=True, verbose_name='\u0412\u0440\u0435\u043c\u044f', db_index=True)),
                ('msg', models.TextField(verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', editable=False)),
                ('code', models.CharField(default=b'', verbose_name='\u0421\u043f\u0435\u0446. \u043a\u043e\u0434', max_length=255, editable=False)),
                ('operation', models.PositiveIntegerField(verbose_name='\u041a\u043e\u0434 \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0438', null=True, editable=False, db_index=True)),
            ],
            options={
                'ordering': ['-dt'],
                'verbose_name': '\u0421\u043e\u0431\u044b\u0442\u0438\u0435',
                'verbose_name_plural': '\u0416\u0443\u0440\u043d\u0430\u043b \u0441\u043e\u0431\u044b\u0442\u0438\u0439',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LoginLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt', models.DateTimeField(auto_now_add=True, verbose_name='\u0412\u0440\u0435\u043c\u044f')),
                ('ip', models.GenericIPAddressField(null=True, unpack_ipv4=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
