# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435', db_index=True)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'common_geocity',
                'verbose_name': '\u043d\u0430\u0441\u0435\u043b\u0435\u043d\u043d\u044b\u0439 \u043f\u0443\u043d\u043a\u0442',
                'verbose_name_plural': '\u043d\u0430\u0441\u0435\u043b\u0435\u043d\u043d\u044b\u0435 \u043f\u0443\u043d\u043a\u0442\u044b',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435', db_index=True)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'common_geocountry',
                'verbose_name': '\u0441\u0442\u0440\u0430\u043d\u0430',
                'verbose_name_plural': '\u0441\u0442\u0440\u0430\u043d\u044b',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('post_index', models.CharField(max_length=255, verbose_name='\u041f\u043e\u0447\u0442\u043e\u0432\u044b\u0439 \u0438\u043d\u0434\u0435\u043a\u0441', blank=True)),
                ('house', models.CharField(max_length=255, verbose_name='\u0414\u043e\u043c', blank=True)),
                ('block', models.CharField(max_length=255, verbose_name='\u041a\u043e\u0440\u043f\u0443\u0441', blank=True)),
                ('building', models.CharField(max_length=255, verbose_name='\u0421\u0442\u0440\u043e\u0435\u043d\u0438\u0435', blank=True)),
                ('flat', models.CharField(max_length=255, verbose_name='\u041a\u0432\u0430\u0440\u0442\u0438\u0440\u0430', blank=True)),
                ('gps_x', models.FloatField(verbose_name='\u041a\u043e\u043e\u0440\u0434\u0438\u043d\u0430\u0442\u0430 X', null=True, editable=False, blank=True)),
                ('gps_y', models.FloatField(verbose_name='\u041a\u043e\u043e\u0440\u0434\u0438\u043d\u0430\u0442\u0430 Y', null=True, editable=False, blank=True)),
                ('info', models.TextField(null=True, verbose_name='\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f', blank=True)),
                ('addr_str', models.CharField(max_length=255, verbose_name='\u0410\u0434\u0440\u0435\u0441', blank=True)),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='\u0413\u043e\u0440\u043e\u0434', blank=True, to='geo.City', null=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='\u0421\u0442\u0440\u0430\u043d\u0430', blank=True, to='geo.Country', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435', db_index=True)),
                ('country', models.ForeignKey(to='geo.Country')),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'common_georegion',
                'verbose_name': '\u0440\u0435\u0433\u0438\u043e\u043d',
                'verbose_name_plural': '\u0440\u0435\u0433\u0438\u043e\u043d\u044b',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Street',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('city', models.ForeignKey(to='geo.City')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': '\u0443\u043b\u0438\u0446\u0430',
                'verbose_name_plural': '\u0443\u043b\u0438\u0446\u044b',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='street',
            unique_together=set([('city', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='region',
            unique_together=set([('country', 'name')]),
        ),
        migrations.AddField(
            model_name='location',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='\u0420\u0435\u0433\u0438\u043e\u043d', blank=True, to='geo.Region', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='location',
            name='street',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='\u0423\u043b\u0438\u0446\u0430', blank=True, to='geo.Street', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='city',
            name='region',
            field=models.ForeignKey(to='geo.Region'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='city',
            unique_together=set([('region', 'name')]),
        ),
    ]
