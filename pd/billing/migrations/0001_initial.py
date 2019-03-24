# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ad',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(choices=[('publish', 'Показ'), ('update', 'Обновление'), ('disable', 'Снятие с показа')], max_length=255, verbose_name='Действие')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Commission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('share', models.FloatField(verbose_name='\u041f\u0440\u043e\u0446\u0435\u043d\u0442')),
                ('source_id', models.PositiveIntegerField(verbose_name='ID \u043f\u043b\u0430\u0442\u0435\u0436\u0430, \u0437\u0430 \u0447\u0442\u043e \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u044f', db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('short_name', models.CharField(max_length=255, verbose_name='\u0421\u043e\u043a\u0440\u0430\u0449\u0435\u043d\u043d\u043e\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('code', models.CharField(max_length=10, verbose_name='\u041a\u043e\u0434')),
                ('rounding', models.SmallIntegerField(default=2, verbose_name='\u041e\u043a\u0440\u0443\u0433\u043b\u0435\u043d\u0438\u0435')),
                ('icon', models.FileField(upload_to='icons', null=True, verbose_name='\u0418\u043a\u043e\u043d\u043a\u0430', blank=True)),
            ],
            options={
                'verbose_name': '\u0412\u0430\u043b\u044e\u0442\u0430',
                'verbose_name_plural': '\u0412\u0430\u043b\u044e\u0442\u044b',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Io',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bank', models.CharField(max_length=255, verbose_name='\u0411\u0430\u043d\u043a')),
                ('transaction', models.CharField(max_length=255, verbose_name='\u0422\u0440\u0430\u043d\u0437\u0430\u043a\u0446\u0438\u044f')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f')),
                ('amount', models.DecimalField(verbose_name='\u0421\u0443\u043c\u043c\u0430', max_digits=20, decimal_places=2)),
                ('comment', models.TextField(default='', verbose_name='\u041f\u0440\u0438\u043c\u0435\u0447\u0430\u043d\u0438\u0435')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Rate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=255, verbose_name='\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435', choices=[('publish', '\u041f\u043e\u043a\u0430\u0437'), ('update', '\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435')])),
                ('date_from', models.DateField(verbose_name='\u0414\u0430\u0442\u0430 \u043d\u0430\u0447\u0430\u043b\u0430 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f \u0442\u0430\u0440\u0438\u0444\u0430')),
                ('rate', models.DecimalField(verbose_name='\u0422\u0430\u0440\u0438\u0444', max_digits=20, decimal_places=2)),
            ],
            options={
                'verbose_name': '\u0422\u0430\u0440\u0438\u0444',
                'verbose_name_plural': '\u0422\u0430\u0440\u0438\u0444\u044b',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(default='0.00', verbose_name='\u041e\u0441\u0442\u0430\u0442\u043e\u043a', max_digits=20, decimal_places=2)),
                ('currency', models.ForeignKey(verbose_name='\u0412\u0430\u043b\u044e\u0442\u0430', to='billing.Currency')),
            ],
            options={
                'verbose_name': '\u041a\u043e\u0448\u0435\u043b\u0435\u043a',
                'verbose_name_plural': '\u041a\u043e\u0448\u0435\u043b\u044c\u043a\u0438',
            },
            bases=(models.Model,),
        ),
    ]
