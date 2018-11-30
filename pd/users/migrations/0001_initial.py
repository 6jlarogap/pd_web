# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import users.models
import pd.utils
import autoslug.fields
import pd.models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('burials', '0001_initial'),
        ('geo', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('billing', '0001_initial'),
        ('persons', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rs', models.CharField(max_length=20, verbose_name='\u0420\u0430\u0441\u0447\u0435\u0442\u043d\u044b\u0439 \u0441\u0447\u0435\u0442', validators=[pd.utils.DigitsValidator(), pd.utils.LengthValidator(20)])),
                ('ks', models.CharField(blank=True, max_length=20, verbose_name='\u041a\u043e\u0440\u0440\u0435\u0441\u043f\u043e\u043d\u0434\u0435\u043d\u0442\u0441\u043a\u0438\u0439 \u0441\u0447\u0435\u0442', validators=[pd.utils.DigitsValidator(), pd.utils.LengthValidator(20)])),
                ('bik', models.CharField(max_length=9, verbose_name='\u0411\u0418\u041a', validators=[pd.utils.DigitsValidator(), pd.utils.LengthValidator(9)])),
                ('bankname', models.CharField(max_length=64, verbose_name='\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u0431\u0430\u043d\u043a\u0430', validators=[pd.utils.NotEmptyValidator(1)])),
                ('ls', models.CharField(blank=True, max_length=11, null=True, verbose_name='\u041b/\u0441', validators=[pd.utils.LengthValidator(11)])),
                ('off_address', models.ForeignKey(editable=False, to='geo.Location', null=True, verbose_name='\u042e\u0440. \u0430\u0434\u0440\u0435\u0441')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BankAccountRegister',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rs', models.CharField(max_length=20, verbose_name='\u0420\u0430\u0441\u0447\u0435\u0442\u043d\u044b\u0439 \u0441\u0447\u0435\u0442', validators=[pd.utils.DigitsValidator(), pd.utils.LengthValidator(20)])),
                ('ks', models.CharField(blank=True, max_length=20, verbose_name='\u041a\u043e\u0440\u0440\u0435\u0441\u043f\u043e\u043d\u0434\u0435\u043d\u0442\u0441\u043a\u0438\u0439 \u0441\u0447\u0435\u0442', validators=[pd.utils.DigitsValidator(), pd.utils.LengthValidator(20)])),
                ('bik', models.CharField(max_length=9, verbose_name='\u0411\u0418\u041a', validators=[pd.utils.DigitsValidator(), pd.utils.LengthValidator(9)])),
                ('bankname', models.CharField(max_length=64, verbose_name='\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u0431\u0430\u043d\u043a\u0430', validators=[pd.utils.NotEmptyValidator(1)])),
                ('ls', models.CharField(blank=True, max_length=11, null=True, verbose_name='\u041b/\u0441', validators=[pd.utils.LengthValidator(11)])),
                ('off_address', models.ForeignKey(editable=False, to='geo.Location', null=True, verbose_name='\u042e\u0440. \u0430\u0434\u0440\u0435\u0441')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomerProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('user_last_name', models.CharField(max_length=255, null=True, verbose_name='\u0424\u0430\u043c\u0438\u043b\u0438\u044f', blank=True)),
                ('user_first_name', models.CharField(max_length=255, null=True, verbose_name='\u0418\u043c\u044f', blank=True)),
                ('user_middle_name', models.CharField(max_length=255, null=True, verbose_name='\u041e\u0442\u0447\u0435\u0441\u0442\u0432\u043e', blank=True)),
                ('phones', models.TextField(null=True, verbose_name='\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u044b (\u0435\u0441\u043b\u0438 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043e, \u0442\u043e \u0447\u0435\u0440\u0435\u0437 ; \u0438\u043b\u0438 ,)', blank=True)),
                ('birthday', models.DateField(verbose_name='\u0414\u0430\u0442\u0430 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f \u0443 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440\u0430', null=True, editable=False)),
                ('site', models.URLField(default=b'', verbose_name='\u0421\u0430\u0439\u0442 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f', max_length=255, editable=False)),
                ('tc_confirmed', models.DateTimeField(verbose_name='\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u043e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u0441\u043a\u043e\u0435 \u0441\u043e\u0433\u043b\u0430\u0448\u0435\u043d\u0438\u0435', null=True, editable=False)),
                ('login_phone', models.DecimalField(decimal_places=0, validators=[pd.models.validate_phone_as_number], max_digits=15, blank=True, help_text='\u0412 \u043c\u0435\u0436\u0434\u0443\u043d\u0430\u0440\u043e\u0434\u043d\u043e\u043c \u0444\u043e\u0440\u043c\u0430\u0442\u0435, \u043d\u0430\u0447\u0438\u043d\u0430\u044f \u0441 \u043a\u043e\u0434\u0430 \u0441\u0442\u0440\u0430\u043d\u044b, \u0431\u0435\u0437 "+", \u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440 79101234567', null=True, verbose_name='\u041c\u043e\u0431\u0438\u043b\u044c\u043d\u044b\u0439 \u0442\u0435\u043b\u0435\u0444\u043e\u043d \u0434\u043b\u044f \u0432\u0445\u043e\u0434\u0430 \u0432 \u043a\u0430\u0431\u0438\u043d\u0435\u0442', db_index=True)),
                ('user', models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Dover',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.CharField(max_length=255, verbose_name='\u041d\u043e\u043c\u0435\u0440')),
                ('begin', models.DateField(verbose_name='\u041d\u0430\u0447\u0430\u043b\u043e')),
                ('end', models.DateField(verbose_name='\u041e\u043a\u043e\u043d\u0447\u0430\u043d\u0438\u0435')),
                ('document', models.FileField(upload_to=b'dover', null=True, verbose_name='\u0421\u043a\u0430\u043d \u0434\u043e\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u0438', blank=True)),
            ],
            options={
                'verbose_name': '\u0414\u043e\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u044c',
                'verbose_name_plural': '\u0414\u043e\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u0438',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FavoriteSupplier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Oauth',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('provider', models.CharField(max_length=100, verbose_name='\u041f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440', choices=[(b'yandex', '\u042f\u043d\u0434\u0435\u043a\u0441'), (b'facebook', 'Facebook'), (b'google', 'Google'), (b'vk', '\u0412\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u0435'), (b'odnoklassniki', '\u041e\u0434\u043d\u043e\u043a\u043b\u0430\u0441\u0441\u043d\u0438\u043a\u0438')])),
                ('uid', models.CharField(max_length=255, verbose_name='\u0418\u0434 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f \u0443 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440\u0430')),
                ('last_name', models.CharField(default=b'', max_length=255, verbose_name='\u0424\u0430\u043c\u0438\u043b\u0438\u044f \u0443 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440\u0430')),
                ('first_name', models.CharField(default=b'', max_length=255, verbose_name='\u0418\u043c\u044f \u0443 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440\u0430')),
                ('middle_name', models.CharField(default=b'', max_length=255, verbose_name='\u041e\u0442\u0447\u0435\u0441\u0442\u0432\u043e \u0443 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440\u0430')),
                ('display_name', models.CharField(default=b'', max_length=255, verbose_name='\u041e\u0442\u043e\u0431\u0440\u0430\u0436\u0430\u0435\u043c\u043e\u0435 \u0438\u043c\u044f \u0443 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440\u0430')),
                ('email', models.EmailField(default=b'', max_length=255, verbose_name='Email \u0443 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440\u0430')),
                ('photo', models.URLField(default=b'', max_length=255, verbose_name='\u0424\u043e\u0442\u043e \u0443 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440\u0430')),
                ('birthday', models.DateField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f \u0443 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440\u0430')),
                ('phones', models.TextField(null=True, verbose_name='\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u044b (\u0435\u0441\u043b\u0438 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043e, \u0442\u043e \u0447\u0435\u0440\u0435\u0437 ; \u0438\u043b\u0438 ,)')),
                ('site', models.URLField(default=b'', max_length=255, verbose_name='\u0421\u0430\u0439\u0442 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Org',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('type', models.CharField(max_length=255, verbose_name='\u0422\u0438\u043f', choices=[(b'company', '\u042e\u0440\u043b\u0438\u0446\u043e'), (b'zags', '\u0417\u0410\u0413\u0421'), (b'medic', '\u041c\u0435\u0434. \u0443\u0447\u0440\u0435\u0436\u0434\u0435\u043d\u0438\u0435'), (b'loru', '\u041b\u041e\u0420\u0423'), (b'ugh', '\u041e\u041c\u0421')])),
                ('name', models.CharField(default=b'', max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438')),
                ('slug', autoslug.fields.AutoSlugField(null=True, editable=False, populate_from=b'name', max_length=255, always_update=True, unique=True)),
                ('client_site_token', models.CharField(verbose_name='\u0422\u043e\u043a\u0435\u043d \u043a\u043b\u0438\u0435\u043d\u0442\u0441\u043a\u043e\u0433\u043e \u0441\u0430\u0439\u0442\u0430', max_length=255, null=True, editable=False)),
                ('full_name', models.CharField(default=b'', max_length=255, verbose_name='\u041f\u043e\u043b\u043d\u043e\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435', blank=True)),
                ('description', models.TextField(null=True, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435, \u043d\u0430\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0434\u0435\u044f\u0442\u0435\u043b\u044c\u043d\u043e\u0441\u0442\u0438', blank=True)),
                ('inn', models.CharField(default=b'', max_length=255, verbose_name='\u0418\u041d\u041d', blank=True)),
                ('kpp', models.CharField(default=b'', max_length=255, verbose_name='\u041a\u041f\u041f', blank=True)),
                ('ogrn', models.CharField(default=b'', max_length=255, verbose_name='\u041e\u0413\u0420\u041d/\u041e\u0413\u0420\u042e\u041b', blank=True)),
                ('director', models.CharField(default=b'', max_length=255, verbose_name='\u0414\u0438\u0440\u0435\u043a\u0442\u043e\u0440', blank=True)),
                ('basis', models.CharField(default=b'charter', max_length=255, verbose_name='\u041e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f \u0434\u0438\u0440\u0435\u043a\u0442\u043e\u0440\u0430', choices=[(b'charter', '\u0443\u0441\u0442\u0430\u0432\u0430'), (b'condition', '\u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f'), (b'certificate', '\u0441\u0432\u0438\u0434\u0435\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430'), (b'proxy', '\u0434\u043e\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u0438')])),
                ('email', models.EmailField(max_length=75, null=True, verbose_name='Email', blank=True)),
                ('phones', models.TextField(null=True, verbose_name='\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u044b', blank=True)),
                ('fax', models.CharField(default=b'', max_length=20, verbose_name='\u0424\u0430\u043a\u0441', blank=True)),
                ('sms_phone', models.DecimalField(decimal_places=0, validators=[pd.models.validate_phone_as_number], max_digits=15, blank=True, help_text='\u0412 \u043c\u0435\u0436\u0434\u0443\u043d\u0430\u0440\u043e\u0434\u043d\u043e\u043c \u0444\u043e\u0440\u043c\u0430\u0442\u0435, \u043d\u0430\u0447\u0438\u043d\u0430\u044f \u0441 \u043a\u043e\u0434\u0430 \u0441\u0442\u0440\u0430\u043d\u044b, \u0431\u0435\u0437 "+", \u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440 79101234567', null=True, verbose_name='\u041c\u043e\u0431\u0438\u043b\u044c\u043d\u044b\u0439 \u0442\u0435\u043b\u0435\u0444\u043e\u043d \u0434\u043b\u044f \u0421\u041c\u0421- \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0439')),
                ('worktime', models.CharField(default=b'', max_length=255, verbose_name='\u0412\u0440\u0435\u043c\u044f \u0440\u0430\u0431\u043e\u0442\u044b (\u0427\u0427:\u041c\u041c - \u0427\u0427:\u041c\u041c)', blank=True)),
                ('site', models.URLField(default=b'', verbose_name='\u0421\u0430\u0439\u0442', blank=True)),
                ('shop_site', models.URLField(default=b'', verbose_name='\u0421\u0430\u0439\u0442 \u043c\u0430\u0433\u0430\u0437\u0438\u043d\u0430', blank=True)),
                ('is_wholesale_with_vat', models.BooleanField(default=False, verbose_name='\u041e\u043f\u0442\u043e\u0432\u044b\u0435 \u0446\u0435\u043d\u044b \u043f\u0440\u043e\u0434\u0443\u043a\u0442\u043e\u0432 \u0441 \u041d\u0414\u0421')),
                ('subdomain', models.CharField(verbose_name='\u041f\u043e\u0434\u0434\u043e\u043c\u0435\u043d', max_length=255, null=True, editable=False)),
                ('opf_order_customer_mandatory', models.BooleanField(default=True, verbose_name='\u0414\u0430\u043d\u043d\u044b\u0435 \u0437\u0430\u043a\u0430\u0437\u0447\u0438\u043a\u0430 \u043f\u0440\u0438 \u043e\u0444\u043e\u0440\u043c\u043b\u0435\u043d\u0438\u0438 \u0437\u0430\u043a\u0430\u0437\u0430 \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u044b')),
                ('opf_order', models.CharField(default=b'org', max_length=255, verbose_name='\u0417\u0430\u043a\u0430\u0437\u0447\u0438\u043a \u043f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e \u0432 \u0437\u0430\u043a\u0430\u0437\u0435', choices=[(b'org', '\u042e\u041b'), (b'person', '\u0424\u041b')])),
                ('numbers_algo', models.CharField(default=b'manual', max_length=255, verbose_name='\u0417\u0430\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u043d\u043e\u043c\u0435\u0440\u0430 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f', choices=[(b'empty', '\u041e\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u043f\u0443\u0441\u0442\u044b\u043c'), (b'manual', '\u0412\u0440\u0443\u0447\u043d\u0443\u044e'), (b'year_ugh', '\u0413\u043e\u0434 + \u043f\u043e\u0440\u044f\u0434\u043a\u043e\u0432\u044b\u0439 (\u0432 \u043f\u0440\u0435\u0434\u0435\u043b\u0430\u0445 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438)'), (b'year_cemetery', '\u0413\u043e\u0434 + \u043f\u043e\u0440\u044f\u0434\u043a\u043e\u0432\u044b\u0439 (\u0432 \u043f\u0440\u0435\u0434\u0435\u043b\u0430\u0445 \u043a\u043b\u0430\u0434\u0431\u0438\u0449\u0430)'), (b'year_month_ugh', '\u0413\u043e\u0434 + \u043c\u0435\u0441\u044f\u0446 + \u043f\u043e\u0440\u044f\u0434\u043a\u043e\u0432\u044b\u0439 (\u0432 \u043f\u0440\u0435\u0434\u0435\u043b\u0430\u0445 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438)'), (b'year_month_cemetery', '\u0413\u043e\u0434 + \u043c\u0435\u0441\u044f\u0446 + \u043f\u043e\u0440\u044f\u0434\u043a\u043e\u0432\u044b\u0439 (\u0432 \u043f\u0440\u0435\u0434\u0435\u043b\u0430\u0445 \u043a\u043b\u0430\u0434\u0431\u0438\u0449\u0430)')])),
                ('opf_burial', models.CharField(default=b'org', max_length=255, verbose_name='\u0417\u0430\u044f\u0432\u0438\u0442\u0435\u043b\u044c \u043f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e \u0432 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0438', choices=[(b'org', '\u042e\u041b'), (b'person', '\u0424\u041b')])),
                ('death_date_offer', models.BooleanField(default=False, verbose_name='\u041f\u0440\u0435\u0434\u043b\u0430\u0433\u0430\u0442\u044c \u0434\u0430\u0442\u0443 \u0441\u043c\u0435\u0440\u0442\u0438 \u0432 \u043d\u043e\u0432\u043e\u043c \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0438')),
                ('hide_deadman_address', models.BooleanField(default=False, verbose_name='\u0421\u043a\u0440\u044b\u0442\u044c \u0430\u0434\u0440\u0435\u0441 \u0443\u0441\u043e\u043f\u0448\u0435\u0433\u043e')),
                ('plan_time_required', models.BooleanField(default=True, verbose_name='\u041f\u043b\u0430\u043d\u043e\u0432\u043e\u0435 \u0432\u0440\u0435\u043c\u044f \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e')),
                ('plan_date_days_before', models.PositiveIntegerField(default=3, verbose_name='\u041a\u043e\u043b-\u0432\u043e \u0434\u043d\u0435\u0439 \u0434\u043b\u044f \u0432\u0432\u043e\u0434\u0430 \u043f\u043b\u0430\u043d\u043e\u0432\u043e\u0439 \u0434\u0430\u0442\u044b \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f \u0432 \u043f\u0440\u043e\u0448\u043b\u043e\u043c')),
                ('max_graves_count', models.PositiveIntegerField(default=5, verbose_name='\u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u043e\u0435 \u0447\u0438\u0441\u043b\u043e \u043c\u043e\u0433\u0438\u043b \u0432 \u043c\u0435\u0441\u0442\u0435', validators=[pd.models.validate_gt0])),
            ],
            options={
                'verbose_name': '\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f',
                'verbose_name_plural': '\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438',
            },
            bases=(pd.models.GetLogsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='OrgAbility',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435', choices=[(b'trade', '\u0422\u043e\u0440\u0433\u043e\u0432\u043b\u044f'), (b'personal-data', '\u041f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u044c\u043d\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435')])),
                ('title', models.CharField(max_length=255, verbose_name='\u0417\u0430\u0433\u043b\u0430\u0432\u0438\u0435')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrgCertificate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('org', models.OneToOneField(to='users.Org')),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='OrgContract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('org', models.OneToOneField(to='users.Org')),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='OrgGallery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('org', models.ForeignKey(to='users.Org')),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='OrgReview',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('subject', models.CharField(max_length=255, verbose_name='\u0422\u0435\u043c\u0430 \u043e\u0442\u0437\u044b\u0432\u0430', blank=True)),
                ('is_positive', models.NullBooleanField(verbose_name='\u041e\u0446\u0435\u043d\u043a\u0430 \u043f\u043e\u043b\u043e\u0436\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f/\u043e\u0442\u0440\u0438\u0446\u0430\u0442\u0435\u043b\u044c\u043d\u0430/\u0431\u0435\u0437 \u043e\u0446\u0435\u043d\u043a\u0438')),
                ('common_text', models.TextField(null=True, verbose_name='\u0422\u0435\u043a\u0441\u0442', blank=True)),
                ('positive_text', models.TextField(null=True, verbose_name='\u0422\u0435\u043a\u0441\u0442 \u043f\u043e\u043b\u043e\u0436\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0439 \u043e\u0446\u0435\u043d\u043a\u0438', blank=True)),
                ('negative_text', models.TextField(null=True, verbose_name='\u0422\u0435\u043a\u0441\u0442 \u043e\u0442\u0440\u0438\u0446\u0430\u0442\u0435\u043b\u044c\u043d\u043e\u0439 \u043e\u0446\u0435\u043d\u043a\u0438', blank=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('org', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='users.Org')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrgWebPay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('wsb_storeid', models.CharField(max_length=255, verbose_name='\u0418\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438 \u0432 \u0441\u0438\u0441\u0442\u0435\u043c\u0435 WebPay')),
                ('secret', models.CharField(max_length=255, verbose_name='\u0421\u0435\u043a\u0440\u0435\u0442\u043d\u044b\u0439 \u043a\u043b\u044e\u0447')),
                ('wsb_store', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438 \u043d\u0430 \u0444\u043e\u0440\u043c\u0435 \u043e\u043f\u043b\u0430\u0442\u044b WebPay')),
                ('wsb_currency_id', models.CharField(default=b'BYR', max_length=255, verbose_name='\u041a\u043e\u0434 \u0432\u0430\u043b\u044e\u0442\u044b \u0441\u043e\u0433\u043b\u0430\u0441\u043d\u043e ISO4271')),
                ('wsb_version', models.CharField(max_length=255, verbose_name='\u0412\u0435\u0440\u0441\u0438\u044f \u0444\u043e\u0440\u043c\u044b \u043e\u043f\u043b\u0430\u0442\u044b')),
                ('wsb_test', models.BooleanField(default=True, verbose_name='\u0422\u0435\u0441\u0442\u043e\u0432\u0430\u044f \u0441\u0440\u0435\u0434\u0430')),
                ('org', models.OneToOneField(to='users.Org')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('user_last_name', models.CharField(max_length=255, null=True, verbose_name='\u0424\u0430\u043c\u0438\u043b\u0438\u044f', blank=True)),
                ('user_first_name', models.CharField(max_length=255, null=True, verbose_name='\u0418\u043c\u044f', blank=True)),
                ('user_middle_name', models.CharField(max_length=255, null=True, verbose_name='\u041e\u0442\u0447\u0435\u0441\u0442\u0432\u043e', blank=True)),
                ('phones', models.TextField(null=True, verbose_name='\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u044b (\u0435\u0441\u043b\u0438 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043e, \u0442\u043e \u0447\u0435\u0440\u0435\u0437 ; \u0438\u043b\u0438 ,)', blank=True)),
                ('birthday', models.DateField(verbose_name='\u0414\u0430\u0442\u0430 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f \u0443 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440\u0430', null=True, editable=False)),
                ('site', models.URLField(default=b'', verbose_name='\u0421\u0430\u0439\u0442 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f', max_length=255, editable=False)),
                ('is_agent', models.BooleanField(default=False, verbose_name='\u0410\u0433\u0435\u043d\u0442')),
                ('out_of_staff', models.BooleanField(default=False, verbose_name='\u0412\u043d\u0435\u0448\u0442\u0430\u0442\u043d\u044b\u0439 \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a')),
                ('title', models.CharField(max_length=255, verbose_name='\u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u044c', blank=True)),
                ('phones_publish', models.BooleanField(default=False, verbose_name='\u041f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u0442\u044c \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u044b?')),
                ('lat', models.DecimalField(null=True, max_digits=30, decimal_places=27, blank=True)),
                ('lng', models.DecimalField(null=True, max_digits=30, decimal_places=27, blank=True)),
                ('area', models.ForeignKey(verbose_name='\u0423\u0447\u0430\u0441\u0442\u043e\u043a', blank=True, to='burials.Area', null=True)),
                ('cemeteries', models.ManyToManyField(related_name='rw_profiles', verbose_name='\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435 \u043a\u043b\u0430\u0434\u0431\u0438\u0449\u0430', to='burials.Cemetery', blank=True)),
                ('cemetery', models.ForeignKey(verbose_name='\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435', blank=True, to='burials.Cemetery', null=True)),
                ('org', models.ForeignKey(to='users.Org', null=True)),
            ],
            options={
                'ordering': ('user_last_name', 'user_first_name', 'user_middle_name'),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProfileLORU',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('loru', models.ForeignKey(related_name='ugh_list', verbose_name='\u041b\u041e\u0420\u0423', to='users.Org')),
                ('ugh', models.ForeignKey(related_name='loru_list', verbose_name='\u041e\u041c\u0421', to='users.Org')),
            ],
            options={
                'verbose_name': '\u041b\u041e\u0420\u0423 \u0443 \u041e\u041c\u0421',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RegisterProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('status', models.CharField(verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441 \u0437\u0430\u044f\u0432\u043a\u0438', max_length=255, editable=False, choices=[(b'to_confirm', '\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f'), (b'confirmed', '\u0417\u0430\u044f\u0432\u043a\u0430 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430'), (b'declined', '\u0412 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u0438 \u043e\u0442\u043a\u0430\u0437\u0430\u043d\u043e'), (b'approved', '\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0432 \u0441\u0438\u0441\u0442\u0435\u043c\u0435')])),
                ('user_name', models.CharField(help_text='\u0414\u043e 30 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432: \u043b\u0430\u0442\u0438\u043d\u0441\u043a\u0438\u0435 \u0431\u0443\u043a\u0432\u044b, \u0446\u0438\u0444\u0440\u044b, \u0434\u0435\u0444\u0438\u0441\u044b, \u0437\u043d\u0430\u043a\u0438 \u043f\u043e\u0434\u0447\u0435\u0440\u043a\u0438\u0432\u0430\u043d\u0438\u044f, @', max_length=30, verbose_name='\u0418\u043c\u044f \u0434\u043b\u044f \u0432\u0445\u043e\u0434\u0430 \u0432 \u0441\u0438\u0441\u0442\u0435\u043c\u0443 (login)', validators=[pd.models.validate_username])),
                ('user_last_name', models.CharField(max_length=255, verbose_name='\u0424\u0430\u043c\u0438\u043b\u0438\u044f')),
                ('user_first_name', models.CharField(max_length=255, verbose_name='\u0418\u043c\u044f')),
                ('user_middle_name', models.CharField(max_length=255, null=True, verbose_name='\u041e\u0442\u0447\u0435\u0441\u0442\u0432\u043e (\u043d\u0435\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e)', blank=True)),
                ('user_email', models.EmailField(max_length=75, verbose_name='Email')),
                ('user_password', models.CharField(default=b'', verbose_name='\u041f\u0430\u0440\u043e\u043b\u044c', max_length=255, editable=False)),
                ('user_activation_key', models.CharField(verbose_name='\u041a\u043b\u044e\u0447 \u0430\u043a\u0442\u0438\u0432\u0430\u0446\u0438\u0438', max_length=40, editable=False)),
                ('org_type', models.CharField(default=b'ugh', max_length=255, verbose_name='\u0422\u0438\u043f \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438', choices=[(b'ugh', '\u0423\u0447\u0435\u0442 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0439'), (b'loru', '\u0423\u0447\u0435\u0442 \u0437\u0430\u043a\u0430\u0437\u043e\u0432')])),
                ('org_name', models.CharField(default=b'', max_length=255, verbose_name='\u041a\u0440\u0430\u0442\u043a\u043e\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438')),
                ('org_full_name', models.CharField(default=b'', max_length=255, verbose_name='\u041f\u043e\u043b\u043d\u043e\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438')),
                ('org_inn', models.CharField(default=b'', max_length=255, verbose_name='\u0418\u041d\u041d')),
                ('org_ogrn', models.CharField(default=b'', max_length=255, verbose_name='\u041e\u0413\u0420\u041d/\u041e\u0413\u0420\u042e\u041b', blank=True)),
                ('org_director', models.CharField(default=b'', max_length=255, verbose_name='\u0414\u0438\u0440\u0435\u043a\u0442\u043e\u0440')),
                ('org_basis', models.CharField(default=b'charter', max_length=255, verbose_name='\u041e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f \u0434\u0438\u0440\u0435\u043a\u0442\u043e\u0440\u0430', choices=[(b'charter', '\u0443\u0441\u0442\u0430\u0432\u0430'), (b'condition', '\u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f'), (b'certificate', '\u0441\u0432\u0438\u0434\u0435\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430'), (b'proxy', '\u0434\u043e\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u0438')])),
                ('org_phones', models.TextField(help_text='\u0412 \u043c\u0435\u0436\u0434\u0443\u043d\u0430\u0440\u043e\u0434\u043d\u043e\u043c \u0444\u043e\u0440\u043c\u0430\u0442\u0435: +\u043a\u043e\u0434-\u0441\u0442\u0440\u0430\u043d\u044b-\u043a\u043e\u0434-\u0433\u043e\u0440\u043e\u0434\u0430-\u043d\u043e\u043c\u0435\u0440-\u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430', verbose_name='\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u044b')),
                ('org_fax', models.CharField(default=b'', max_length=20, verbose_name='\u0424\u0430\u043a\u0441', blank=True)),
                ('org_subdomain', models.CharField(verbose_name='\u041f\u043e\u0434\u0434\u043e\u043c\u0435\u043d', max_length=255, null=True, editable=False)),
                ('org_address', models.ForeignKey(editable=False, to='geo.Location', null=True)),
                ('org_currency', models.ForeignKey(default=users.models.get_default_currency, verbose_name='\u0412\u0430\u043b\u044e\u0442\u0430', to='billing.Currency')),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.SafeDeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='RegisterProfileContract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('registerprofile', models.OneToOneField(to='users.RegisterProfile')),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='RegisterProfileScan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('registerprofile', models.OneToOneField(to='users.RegisterProfile')),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(verbose_name='\u041a\u043e\u0434', max_length=255, editable=False)),
                ('title', models.CharField(verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435', max_length=255, editable=False)),
            ],
            options={
                'ordering': ('title',),
                'verbose_name': '\u0420\u043e\u043b\u044c \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('address', models.ForeignKey(verbose_name='\u0410\u0434\u0440\u0435\u0441', to='geo.Location')),
                ('loru', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041b\u041e\u0420\u0423', to='users.Org')),
            ],
            options={
            },
            bases=(models.Model, users.models.PhonesMixin),
        ),
        migrations.CreateModel(
            name='StorePhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('photo', models.ImageField(max_length=255, upload_to=pd.models.files_upload_to, null=True, verbose_name='\u0424\u043e\u0442\u043e', blank=True)),
                ('original_filename', models.CharField(max_length=255, null=True, editable=False)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('store', models.OneToOneField(to='users.Store')),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Thank',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('customperson', models.ForeignKey(verbose_name='\u041f\u0435\u0440\u0441\u043e\u043d\u0430', to='persons.CustomPerson')),
                ('user', models.ForeignKey(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ThankUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('login_phone', models.DecimalField(verbose_name='\u041c\u043e\u0431\u0438\u043b\u044c\u043d\u044b\u0439 \u0442\u0435\u043b\u0435\u0444\u043e\u043d \u0434\u043b\u044f \u0432\u0445\u043e\u0434\u0430 \u0432 \u043a\u0430\u0431\u0438\u043d\u0435\u0442', unique=True, editable=False, max_digits=15, decimal_places=0)),
                ('password', models.CharField(verbose_name='\u041f\u0430\u0440\u043e\u043b\u044c', max_length=255, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('user', models.OneToOneField(related_name='user_photo_list', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='YoutubeCaption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num', models.PositiveIntegerField(verbose_name='\u041f\u043e\u0440\u044f\u0434\u043a\u043e\u0432\u044b\u0439 \u043d\u043e\u043c\u0435\u0440 \u0441\u0443\u0431\u0442\u0438\u0442\u0440\u0430')),
                ('start', models.FloatField(verbose_name='\u0421\u0442\u0430\u0440\u0442 \u0441\u0443\u0431\u0442\u0438\u0442\u0440\u0430')),
                ('stop', models.FloatField(verbose_name='\u0421\u0442\u043e\u043f \u0441\u0443\u0431\u0442\u0438\u0442\u0440\u0430')),
                ('text', models.TextField(verbose_name='\u0422\u0435\u043a\u0441\u0442')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='YoutubeCaptionVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('like', models.CharField(default=b'up', max_length=100, verbose_name='\u0420\u0435\u0430\u043a\u0446\u0438\u044f', choices=[(b'up', '\u041d\u0440\u0430\u0432\u0438\u0442\u0441\u044f'), (b'up', '\u041d\u0435 \u043d\u0440\u0430\u0432\u0438\u0442\u0441\u044f')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('youtubecaption', models.ForeignKey(to='users.YoutubeCaption')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='YoutubeVideo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('yid', models.CharField(unique=True, max_length=255, verbose_name='Youtube ID')),
                ('url', models.URLField(default=b'', max_length=255, verbose_name='URL')),
                ('title', models.CharField(default=b'', max_length=255, verbose_name='\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a')),
                ('title_photo_url', models.URLField(default=b'', max_length=255, verbose_name='Preview URL')),
                ('is_hidden', models.BooleanField(default=False, verbose_name='\u0421\u043a\u0440\u044b\u0442\u043e \u0432 \u0441\u043f\u0438\u0441\u043a\u0435 \u0432\u0438\u0434\u0435\u043e')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='YoutubeVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('time', models.PositiveIntegerField(default=0, verbose_name='\u0412\u0440\u0435\u043c\u044f \u0440\u0435\u0430\u043a\u0446\u0438\u0438')),
                ('like', models.CharField(default=b'up', max_length=100, verbose_name='\u0420\u0435\u0430\u043a\u0446\u0438\u044f', choices=[(b'up', '\u041d\u0440\u0430\u0432\u0438\u0442\u0441\u044f'), (b'up', '\u041d\u0435 \u043d\u0440\u0430\u0432\u0438\u0442\u0441\u044f')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('youtubevideo', models.ForeignKey(to='users.YoutubeVideo')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='youtubecaption',
            name='youtubevideo',
            field=models.ForeignKey(to='users.YoutubeVideo'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='thank',
            unique_together=set([('user', 'customperson')]),
        ),
        migrations.AlterUniqueTogether(
            name='profileloru',
            unique_together=set([('ugh', 'loru')]),
        ),
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.ManyToManyField(to='users.Role', verbose_name='\u0420\u043e\u043b\u0438 \u0432 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='store',
            field=models.ForeignKey(verbose_name='\u041f\u043e\u0434\u0440\u0430\u0437\u0434\u0435\u043b\u0435\u043d\u0438\u0435', blank=True, to='users.Store', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='org',
            name='ability',
            field=models.ManyToManyField(to='users.OrgAbility', editable=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='org',
            name='currency',
            field=models.ForeignKey(default=users.models.get_default_currency, verbose_name='\u0412\u0430\u043b\u044e\u0442\u0430', to='billing.Currency', help_text=' \u041f\u0440\u0438 \u0441\u043c\u0435\u043d\u0435 \u0432\u0430\u043b\u044e\u0442\u044b \u043e\u043d\u0430 \u0431\u0443\u0434\u0435\u0442 \u0437\u0430\u043c\u0435\u043d\u0435\u043d\u0430 \u0443 \u0432\u0441\u0435\u0445 \u0442\u043e\u0432\u0430\u0440\u043e\u0432 (\u0443\u0441\u043b\u0443\u0433) \u0431\u0435\u0437 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0438 \u0446\u0435\u043d'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='org',
            name='off_address',
            field=models.ForeignKey(verbose_name='\u042e\u0440. \u0430\u0434\u0440\u0435\u0441', blank=True, to='geo.Location', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='org',
            unique_together=set([('subdomain',)]),
        ),
        migrations.AlterUniqueTogether(
            name='oauth',
            unique_together=set([('provider', 'uid')]),
        ),
        migrations.AddField(
            model_name='favoritesupplier',
            name='loru',
            field=models.ForeignKey(related_name='favorite_loru', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041b\u041e\u0420\u0423', to='users.Org'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='favoritesupplier',
            name='supplier',
            field=models.ForeignKey(related_name='favorite_supplier_list', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041b\u041e\u0420\u0423', to='users.Org'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='favoritesupplier',
            unique_together=set([('loru', 'supplier')]),
        ),
        migrations.AddField(
            model_name='dover',
            name='agent',
            field=models.ForeignKey(verbose_name='\u0410\u0433\u0435\u043d\u0442', to='users.Profile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dover',
            name='target_org',
            field=models.ForeignKey(editable=False, to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='customerprofile',
            unique_together=set([('login_phone',)]),
        ),
        migrations.AddField(
            model_name='bankaccountregister',
            name='registerprofile',
            field=models.ForeignKey(verbose_name='\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f', to='users.RegisterProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='organization',
            field=models.ForeignKey(verbose_name='\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f', to='users.Org'),
            preserve_default=True,
        ),
    ]
