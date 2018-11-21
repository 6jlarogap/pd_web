# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import users.models
import pd.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('availability', models.CharField(default=b'open', max_length=32, verbose_name='\u041e\u0442\u043a\u0440\u044b\u0442\u043e\u0441\u0442\u044c', choices=[(b'open', '\u041e\u0442\u043a\u0440\u044b\u0442'), (b'old_only', '\u0422\u043e\u043b\u044c\u043a\u043e \u043f\u043e\u0434\u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f'), (b'closed', '\u0417\u0430\u043a\u0440\u044b\u0442')])),
                ('kind', models.CharField(default=b'g', max_length=8, verbose_name='\u0422\u0438\u043f', choices=[(b'g', '\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435\u043d\u0441\u043a\u0438\u0439 (\u041c\u043e\u0433\u0438\u043b\u044b)'), (b'v', '\u041a\u043e\u043b\u0443\u043c\u0431\u0430\u0440\u043d\u0430\u044f \u0441\u0442\u0435\u043d\u0430'), (b'h', '\u0413\u043e\u0440\u0438\u0437\u043e\u043d\u0442\u0430\u043b\u044c\u043d\u044b\u0439 \u043a\u043e\u043b\u0443\u043c\u0431\u0430\u0440\u0438\u0439')])),
                ('places_count', models.PositiveIntegerField(default=1, verbose_name='\u041c\u0430\u043a\u0441. \u043a\u043e\u043b-\u0432\u043e \u043c\u043e\u0433\u0438\u043b \u0432 \u043c\u0435\u0441\u0442\u0435')),
                ('square', models.FloatField(verbose_name='\u041f\u043b\u043e\u0449\u0430\u0434\u044c', null=True, editable=False)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': '\u0423\u0447\u0430\u0441\u0442\u043e\u043a',
                'verbose_name_plural': '\u0423\u0447\u0430\u0441\u0442\u043a\u0438',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AreaCoordinates',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('angle_number', models.PositiveIntegerField(verbose_name='\u041f\u043e\u0440\u044f\u0434\u043e\u043a \u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u044f \u0443\u0433\u043b\u043e\u0432 \u043c\u043d\u043e\u0433\u043e\u0443\u0433\u043e\u043b\u044c\u043d\u0438\u043a\u0430')),
                ('lat', models.FloatField(verbose_name='\u0428\u0438\u0440\u043e\u0442\u0430')),
                ('lng', models.FloatField(verbose_name='\u0414\u043e\u043b\u0433\u043e\u0442\u0430')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AreaPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('lat', models.FloatField(null=True, verbose_name='\u0428\u0438\u0440\u043e\u0442\u0430', blank=True)),
                ('lng', models.FloatField(null=True, verbose_name='\u0414\u043e\u043b\u0433\u043e\u0442\u0430', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='AreaPurpose',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
            ],
            options={
                'verbose_name': '\u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435 \u0443\u0447\u0430\u0441\u0442\u043a\u043e\u0432',
                'verbose_name_plural': '\u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f \u0443\u0447\u0430\u0441\u0442\u043a\u043e\u0432',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Burial',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('burial_type', models.CharField(default=b'common', choices=[(b'common', '\u041d\u043e\u0432\u043e\u0435 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0435'), (b'additional', '\u041f\u043e\u0434\u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0435'), (b'overlap', '\u0417\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0435 \u0432 \u0441\u0443\u0449\u0435\u0441\u0442\u0432\u0443\u044e\u0449\u0443\u044e')], max_length=255, blank=True, null=True, verbose_name='\u0412\u0438\u0434 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f')),
                ('burial_container', models.CharField(default=b'container_coffin', choices=[(b'container_coffin', '\u0413\u0440\u043e\u0431'), (b'container_urn', '\u0423\u0440\u043d\u0430'), (b'container_ash', '\u041f\u0440\u0430\u0445'), (b'container_bio', '\u0411\u0438\u043e\u043e\u0442\u0445\u043e\u0434\u044b')], max_length=255, blank=True, null=True, verbose_name='\u0422\u0438\u043f \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f')),
                ('source_type', models.CharField(verbose_name='\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a', max_length=255, null=True, editable=False, choices=[(b'full', '\u042d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u043e\u0435'), (b'ugh', '\u0420\u0443\u0447\u043d\u043e\u0435'), (b'archive', '\u0410\u0440\u0445\u0438\u0432\u043d\u043e\u0435'), (b'transferred', '\u041f\u0435\u0440\u0435\u043d\u0435\u0441\u0435\u043d\u043d\u043e\u0435')])),
                ('account_number', models.CharField(max_length=255, null=True, verbose_name='\u2116 \u0432 \u043a\u043d\u0438\u0433\u0435 \u0443\u0447\u0435\u0442\u0430', blank=True)),
                ('row', models.CharField(default=b'', max_length=255, verbose_name='\u0420\u044f\u0434', blank=True)),
                ('place_number', models.CharField(default=b'', help_text='\u0415\u0441\u043b\u0438 \u043f\u0443\u0441\u0442\u043e - \u043d\u043e\u043c\u0435\u0440 \u0431\u0443\u0434\u0435\u0442 \u0441\u0433\u0435\u043d\u0435\u0440\u0438\u0440\u043e\u0432\u0430\u043d \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438', max_length=255, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u043c\u0435\u0441\u0442\u0430', blank=True)),
                ('grave_number', models.PositiveSmallIntegerField(default=1, verbose_name='\u041c\u043e\u0433\u0438\u043b\u0430')),
                ('desired_graves_count', models.PositiveSmallIntegerField(default=1, verbose_name='\u0427\u0438\u0441\u043b\u043e \u043c\u043e\u0433\u0438\u043b \u0432 \u043d\u043e\u0432\u043e\u043c \u043c\u0435\u0441\u0442\u0435')),
                ('place_length', models.DecimalField(decimal_places=2, validators=[pd.models.validate_gt0], max_digits=5, blank=True, null=True, verbose_name='\u0414\u043b\u0438\u043d\u0430, \u043c.')),
                ('place_width', models.DecimalField(decimal_places=2, validators=[pd.models.validate_gt0], max_digits=5, blank=True, null=True, verbose_name='\u0428\u0438\u0440\u0438\u043d\u0430, \u043c.')),
                ('plan_date', models.DateField(null=True, verbose_name='\u041f\u043b\u0430\u043d. \u0434\u0430\u0442\u0430', blank=True)),
                ('plan_time', models.TimeField(null=True, verbose_name='\u041f\u043b\u0430\u043d. \u0432\u0440\u0435\u043c\u044f', blank=True)),
                ('fact_date_no_month', models.BooleanField(default=False, editable=False)),
                ('fact_date_no_day', models.BooleanField(default=False, editable=False)),
                ('fact_date', pd.models.UnclearDateModelField(null=True, verbose_name='\u0424\u0430\u043a\u0442. \u0434\u0430\u0442\u0430', blank=True)),
                ('dt_register', models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0437\u0430\u043a\u0440\u044b\u0442\u0438\u044f, \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438 \u043f\u043e\u043b\u0435\u0439 \u0434\u043b\u044f \u0440\u0435\u0435\u0441\u0442\u0440\u0430', null=True, editable=False)),
                ('loru_agent_director', models.BooleanField(default=False, verbose_name='\u0414\u0438\u0440\u0435\u043a\u0442\u043e\u0440-\u0410\u0433\u0435\u043d\u0442')),
                ('agent_director', models.BooleanField(default=False, verbose_name='\u0414\u0438\u0440\u0435\u043a\u0442\u043e\u0440-\u0410\u0433\u0435\u043d\u0442')),
                ('status', models.CharField(default=b'draft', verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', max_length=255, editable=False, choices=[(b'backed', '\u041e\u0442\u043e\u0437\u0432\u0430\u043d\u043e'), (b'declined', '\u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u043e'), (b'draft', '\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a'), (b'ready', '\u041d\u0430 \u0441\u043e\u0433\u043b\u0430\u0441\u043e\u0432\u0430\u043d\u0438\u0438'), (b'inspecting', '\u041d\u0430 \u043e\u0431\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u0438'), (b'approved', '\u0421\u043e\u0433\u043b\u0430\u0441\u043e\u0432\u0430\u043d\u043e'), (b'closed', '\u0417\u0430\u043a\u0440\u044b\u0442\u043e'), (b'exhumated', '\u042d\u043a\u0441\u0433\u0443\u043c\u0438\u0440\u043e\u0432\u0430\u043d\u043e')])),
                ('annulated', models.BooleanField(default=False, verbose_name='\u0410\u043d\u043d\u0443\u043b\u0438\u0440\u043e\u0432\u0430\u043d\u043e')),
                ('flag_no_applicant_doc_required', models.BooleanField(default=False, verbose_name='\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442 \u0437\u0430\u044f\u0432\u0438\u0442\u0435\u043b\u044f-\u0424\u041b \u043d\u0435 \u0442\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f', editable=False)),
            ],
            options={
                'verbose_name': '\u0417\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0435',
                'verbose_name_plural': '\u0417\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0435',
            },
            bases=(pd.models.SafeDeleteMixin, pd.models.GetLogsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='BurialComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('comment', models.TextField(verbose_name='\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439')),
            ],
            options={
                'ordering': ['-dt_created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BurialFiles',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Cemetery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('time_begin', models.TimeField(null=True, verbose_name='\u041d\u0430\u0447\u0430\u043b\u043e \u0440\u0430\u0431\u043e\u0442\u044b', blank=True)),
                ('time_end', models.TimeField(null=True, verbose_name='\u041e\u043a\u043e\u043d\u0447\u0430\u043d\u0438\u0435 \u0440\u0430\u0431\u043e\u0442\u044b', blank=True)),
                ('places_algo', models.CharField(default=b'manual', max_length=255, verbose_name='\u0420\u0430\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430 \u043d\u043e\u043c\u0435\u0440\u043e\u0432 \u043c\u0435\u0441\u0442 \u043d\u043e\u0432\u044b\u0445 \u0440\u0443\u0447\u043d\u044b\u0445 \u0438 \u044d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u044b\u0445 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0439', choices=[(b'area', '\u041f\u043e \u0443\u0447\u0430\u0441\u0442\u043a\u0443'), (b'row', '\u041f\u043e \u0440\u044f\u0434\u0443'), (b'cem_year', '\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435 + \u0433\u043e\u0434'), (b'burial_account_number', '\u041f\u043e \u0440\u0435\u0433. \u043d\u043e\u043c\u0435\u0440\u0443 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f'), (b'manual', '\u0412\u0440\u0443\u0447\u043d\u0443\u044e')])),
                ('places_algo_archive', models.CharField(default=b'manual', max_length=255, verbose_name='\u0420\u0430\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430 \u043d\u043e\u043c\u0435\u0440\u043e\u0432 \u0441\u0443\u0449\u0435\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0445, \u043d\u043e \u043d\u0435\u0443\u0447\u0442\u0435\u043d\u043d\u044b\u0445 \u043c\u0435\u0441\u0442', choices=[(b'manual', '\u0412\u0440\u0443\u0447\u043d\u0443\u044e'), (b'-area', '\u041f\u043e \u043f\u043e\u0440\u044f\u0434\u043a\u0443 \u0432 \u043f\u0440\u0435\u0434\u0435\u043b\u0430\u0445 \u0443\u0447\u0430\u0441\u0442\u043a\u0430 (-0001 -0002...)'), (b'burial_account_number', '\u041f\u043e \u0440\u0435\u0433. \u043d\u043e\u043c\u0435\u0440\u0443 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f')])),
                ('time_slots', models.TextField(default=b'', help_text='\u0412 \u0444\u043e\u0440\u043c\u0430\u0442\u0435 \u0427\u0427:\u041c\u041c, \u043f\u043e \u043e\u0434\u043d\u043e\u043c\u0443 \u043d\u0430 \u0441\u0442\u0440\u043e\u043a\u0443', verbose_name='\u0412\u0440\u0435\u043c\u044f \u0434\u043b\u044f \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f', blank=True)),
                ('archive_burial_fact_date_required', models.BooleanField(default=False, verbose_name='\u0414\u0430\u0442\u0430 \u0430\u0440\u0445\u0438\u0432\u043d\u043e\u0433\u043e \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u0430')),
                ('archive_burial_account_number_required', models.BooleanField(default=False, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0430\u0440\u0445\u0438\u0432\u043d\u043e\u0433\u043e \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f \u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u0435\u043d')),
                ('square', models.FloatField(verbose_name='\u041f\u043b\u043e\u0449\u0430\u0434\u044c', null=True, editable=False)),
                ('code', models.CharField(default='', max_length=50, verbose_name='\u041a\u043e\u0434', blank=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': '\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435',
                'verbose_name_plural': '\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0430',
            },
            bases=(pd.models.GetLogsMixin, models.Model, users.models.PhonesMixin),
        ),
        migrations.CreateModel(
            name='CemeteryCoordinates',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('angle_number', models.PositiveIntegerField(verbose_name='\u041f\u043e\u0440\u044f\u0434\u043e\u043a \u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u044f \u0443\u0433\u043b\u043e\u0432 \u043c\u043d\u043e\u0433\u043e\u0443\u0433\u043e\u043b\u044c\u043d\u0438\u043a\u0430')),
                ('lat', models.FloatField(verbose_name='\u0428\u0438\u0440\u043e\u0442\u0430')),
                ('lng', models.FloatField(verbose_name='\u0414\u043e\u043b\u0433\u043e\u0442\u0430')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CemeteryPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('photo', models.ImageField(max_length=255, upload_to=pd.models.files_upload_to, null=True, verbose_name='\u0424\u043e\u0442\u043e', blank=True)),
                ('original_filename', models.CharField(max_length=255, null=True, editable=False)),
                ('lat', models.FloatField(null=True, verbose_name='\u0428\u0438\u0440\u043e\u0442\u0430', blank=True)),
                ('lng', models.FloatField(null=True, verbose_name='\u0414\u043e\u043b\u0433\u043e\u0442\u0430', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='CemeterySchema',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('photo', models.ImageField(max_length=255, upload_to=pd.models.files_upload_to, null=True, verbose_name='\u0424\u043e\u0442\u043e', blank=True)),
                ('original_filename', models.CharField(max_length=255, null=True, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ExhumationRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('plan_date', models.DateField(null=True, verbose_name='\u041f\u043b\u0430\u043d. \u0434\u0430\u0442\u0430', blank=True)),
                ('plan_time', models.TimeField(null=True, verbose_name='\u041f\u043b\u0430\u043d. \u0432\u0440\u0435\u043c\u044f', blank=True)),
                ('fact_date', models.DateField(null=True, verbose_name='\u0424\u0430\u043a\u0442. \u0434\u0430\u0442\u0430')),
                ('agent_director', models.BooleanField(default=False, verbose_name='\u0414\u0438\u0440\u0435\u043a\u0442\u043e\u0440-\u0410\u0433\u0435\u043d\u0442')),
            ],
            options={
                'verbose_name': '\u0417\u0430\u043f\u0440\u043e\u0441 \u043d\u0430 \u044d\u043a\u0441\u0433\u0443\u043c\u0430\u0446\u0438\u044e',
                'verbose_name_plural': '\u0417\u0430\u043f\u0440\u043e\u0441\u044b \u043d\u0430 \u044d\u043a\u0441\u0433\u0443\u043c\u0430\u0446\u0438\u044e',
            },
            bases=(pd.models.SafeDeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Grave',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('lat', models.FloatField(null=True, verbose_name='\u0428\u0438\u0440\u043e\u0442\u0430', blank=True)),
                ('lng', models.FloatField(null=True, verbose_name='\u0414\u043e\u043b\u0433\u043e\u0442\u0430', blank=True)),
                ('grave_number', models.PositiveSmallIntegerField(default=1, verbose_name='\u041d\u043e\u043c\u0435\u0440')),
                ('is_wrong_fio', models.BooleanField(default=False, verbose_name='\u041d\u0435\u0432\u0435\u0440\u043d\u043e\u0435 \u0424\u0418\u041e')),
                ('is_military', models.BooleanField(default=False, verbose_name='\u0412\u043e\u0438\u043d\u0441\u043a\u0430\u044f \u043c\u043e\u0433\u0438\u043b\u0430')),
                ('dt_free', models.DateTimeField(verbose_name='\u0421\u0432\u043e\u0431\u043e\u0434\u043d\u0430\u044f \u043c\u043e\u0433\u0438\u043b\u0430/\u0434\u0430\u0442\u0430 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0438 \u043f\u0440\u0438\u0437\u043d\u0430\u043a\u0430/', null=True, editable=False)),
            ],
            options={
                'ordering': ['grave_number'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderPlace',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cemetery_text', models.CharField(default=b'', max_length=255, verbose_name='\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435')),
                ('row', models.CharField(default=b'', max_length=255, verbose_name='\u0420\u044f\u0434')),
                ('place', models.CharField(default=b'', max_length=255, verbose_name='\u041c\u0435\u0441\u0442\u043e')),
                ('size', models.CharField(default=b'', max_length=255, verbose_name='\u0420\u0430\u0437\u043c\u0435\u0440 \u0433\u0440\u043e\u0431\u0430')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('lat', models.FloatField(null=True, verbose_name='\u0428\u0438\u0440\u043e\u0442\u0430', blank=True)),
                ('lng', models.FloatField(null=True, verbose_name='\u0414\u043e\u043b\u0433\u043e\u0442\u0430', blank=True)),
                ('row', models.CharField(default=b'', max_length=255, verbose_name='\u0420\u044f\u0434', blank=True)),
                ('oldplace', models.CharField(max_length=255, null=True, verbose_name='\u0421\u0442\u0430\u0440\u043e\u0435 \u043c\u0435\u0441\u0442\u043e', blank=True)),
                ('place', models.CharField(default=b'', max_length=255, verbose_name='\u041c\u0435\u0441\u0442\u043e', blank=True)),
                ('available_count', models.PositiveSmallIntegerField(default=0, verbose_name='\u0427\u0438\u0441\u043b\u043e \u0441\u0432\u043e\u0431\u043e\u0434\u043d\u044b\u0445 \u043c\u043e\u0433\u0438\u043b')),
                ('kind_crypt', models.BooleanField(default=False, verbose_name='\u042d\u0442\u043e \u0441\u043a\u043b\u0435\u043f')),
                ('place_length', models.DecimalField(decimal_places=2, validators=[pd.models.validate_gt0], max_digits=5, blank=True, null=True, verbose_name='\u0414\u043b\u0438\u043d\u0430, \u043c.')),
                ('place_width', models.DecimalField(decimal_places=2, validators=[pd.models.validate_gt0], max_digits=5, blank=True, null=True, verbose_name='\u0428\u0438\u0440\u0438\u043d\u0430, \u043c.')),
                ('dt_wrong_fio', models.DateTimeField(verbose_name='\u041d\u0435\u0432\u0435\u0440\u043d\u043e\u0435 \u0424\u0418\u041e /\u0434\u0430\u0442\u0430 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0438 \u043f\u0440\u0438\u0437\u043d\u0430\u043a\u0430/', null=True, editable=False)),
                ('dt_military', models.DateTimeField(verbose_name='\u0412\u043e\u0438\u043d\u0441\u043a\u043e\u0435 /\u0434\u0430\u0442\u0430 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0438 \u043f\u0440\u0438\u0437\u043d\u0430\u043a\u0430/', null=True, editable=False)),
                ('dt_size_violated', models.DateTimeField(verbose_name='\u041d\u0430\u0440\u0443\u0448\u0435\u043d\u0438\u0435 \u0440\u0430\u0437\u043c\u0435\u0440\u043e\u0432 /\u0434\u0430\u0442\u0430 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0438 \u043f\u0440\u0438\u0437\u043d\u0430\u043a\u0430/', null=True, editable=False)),
                ('dt_unowned', models.DateTimeField(verbose_name='\u0417\u0430\u0431\u0440\u043e\u0448\u0435\u043d\u043d\u043e\u0435 /\u0434\u0430\u0442\u0430 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0438 \u043f\u0440\u0438\u0437\u043d\u0430\u043a\u0430/', null=True, editable=False)),
                ('dt_free', models.DateTimeField(verbose_name='\u0421\u0432\u043e\u0431\u043e\u0434\u043d\u043e\u0435 /\u0434\u0430\u0442\u0430 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0438 \u043f\u0440\u0438\u0437\u043d\u0430\u043a\u0430/', null=True, editable=False)),
                ('dt_unindentified', models.DateTimeField(verbose_name='\u041d\u0435\u043e\u043f\u043e\u0437\u043d\u0430\u043d\u043d\u043e\u0435 /\u0434\u0430\u0442\u0430 \u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0438 \u043f\u0440\u0438\u0437\u043d\u0430\u043a\u0430/', null=True, editable=False)),
                ('is_invent', models.BooleanField(default=False, verbose_name='\u0414\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043e \u043f\u0440\u0438 \u0438\u043d\u0432\u0435\u043d\u0442\u0430\u0440\u0438\u0437\u0430\u0446\u0438\u0438 \u043c\u043e\u0431\u0438\u043b\u044c\u043d\u044b\u043c \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u043c', editable=False)),
                ('dt_processed', models.DateTimeField(verbose_name='\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u0430\u043d\u043e: \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u044b \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f \u043f\u043e \u0444\u043e\u0442\u043e', null=True, editable=False)),
                ('is_inprocess', models.BooleanField(default=False, verbose_name='\u0412\u0437\u044f\u0442\u043e \u0432 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0443 \u043f\u0440\u0438 \u0432\u0432\u043e\u0434\u0435 \u043f\u043e \u0444\u043e\u0442\u043e\u0433\u0440\u0430\u0444\u0438\u044f\u043c', editable=False)),
                ('geohash', models.CharField(verbose_name='Geohash', max_length=12, null=True, editable=False, db_index=True)),
            ],
            options={
                'ordering': ['row', 'place'],
                'verbose_name': '\u041c\u0435\u0441\u0442\u043e',
                'verbose_name_plural': '\u041c\u0435\u0441\u0442\u0430',
            },
            bases=(pd.models.SafeDeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='PlacePhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('lat', models.FloatField(null=True, verbose_name='\u0428\u0438\u0440\u043e\u0442\u0430', blank=True)),
                ('lng', models.FloatField(null=True, verbose_name='\u0414\u043e\u043b\u0433\u043e\u0442\u0430', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='PlaceSize',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('graves_count', models.PositiveSmallIntegerField(verbose_name='\u0427\u0438\u0441\u043b\u043e \u043c\u043e\u0433\u0438\u043b')),
                ('place_length', models.DecimalField(verbose_name='\u0414\u043b\u0438\u043d\u0430, \u043c.', max_digits=5, decimal_places=2, validators=[pd.models.validate_gt0])),
                ('place_width', models.DecimalField(verbose_name='\u0428\u0438\u0440\u0438\u043d\u0430, \u043c.', max_digits=5, decimal_places=2, validators=[pd.models.validate_gt0])),
            ],
            options={
                'ordering': ('graves_count',),
                'verbose_name': '\u0420\u0430\u0437\u043c\u0435\u0440 \u043c\u0435\u0441\u0442\u0430',
                'verbose_name_plural': '\u0420\u0430\u0437\u043c\u0435\u0440\u044b \u043c\u0435\u0441\u0442',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlaceStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('status', models.CharField(default=b'actual', max_length=40, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', choices=[(b'actual', '\u0414\u0435\u0439\u0441\u0442\u0432\u0443\u044e\u0449\u0435\u0435 \u043c\u0435\u0441\u0442\u043e'), (b'found-unowned', '\u041e\u0431\u043d\u0430\u0440\u0443\u0436\u0435\u043d\u043e \u0431\u0435\u0441\u0445\u043e\u0437\u044f\u0439\u043d\u044b\u043c'), (b'signed', '\u0423\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0430 \u0442\u0430\u0431\u043b\u0438\u0447\u043a\u0430'), (b'responsible-rejected', '\u041e\u0442\u043a\u0430\u0437 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e \u043e\u0442 \u043c\u0435\u0441\u0442\u0430'), (b'accepted-unowned', '\u041f\u0440\u0438\u0437\u043d\u0430\u043d\u043e \u0431\u0435\u0441\u0445\u043e\u0437\u044f\u0439\u043d\u044b\u043c'), (b'recovering', '\u0413\u043e\u0442\u043e\u0432\u0438\u0442\u0441\u044f \u043a \u043f\u043e\u0432\u0442\u043e\u0440\u043d\u043e\u043c\u0443 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u044e'), (b'recovered', '\u0413\u043e\u0442\u043e\u0432\u043e \u043a \u043f\u043e\u0432\u0442\u043e\u0440\u043d\u043e\u043c\u0443 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u044e'), (b'other', '\u0414\u0440\u0443\u0433\u043e\u0439 \u0441\u0442\u0430\u0442\u0443\u0441 \u043c\u0435\u0441\u0442\u0430')])),
                ('comment', models.TextField(null=True, verbose_name='\u041f\u0440\u0438\u043c\u0435\u0447\u0430\u043d\u0438\u0435', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlaceStatusFiles',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Reason',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reason_type', models.CharField(max_length=255, verbose_name='\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435', choices=[(b'back', '\u041b\u041e\u0420\u0423 \u043e\u0442\u0437\u044b\u0432\u0430\u0435\u0442 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0435'), (b'decline', '\u041e\u041c\u0421 \u043e\u0442\u043a\u0430\u0437\u044b\u0432\u0430\u0435\u0442 \u0432 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0438'), (b'annulate', '\u0410\u043d\u043d\u0443\u043b\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f'), (b'disapprove', '\u041e\u041c\u0421 \u043e\u0442\u0437\u044b\u0432\u0430\u0435\u0442 \u0441\u043e\u0433\u043b\u0430\u0441\u043e\u0432\u0430\u043d\u0438\u0435 \u0440\u0443\u0447\u043d\u043e\u0433\u043e \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f')])),
                ('name', models.CharField(max_length=255, verbose_name='\u041f\u0440\u0438\u0447\u0438\u043d\u0430')),
                ('text', models.TextField(default=b'', verbose_name='\u0422\u0435\u043a\u0441\u0442 \u043f\u0440\u0438\u0447\u0438\u043d\u044b', editable=False)),
            ],
            options={
                'ordering': ('reason_type', 'name'),
                'verbose_name': '\u041f\u0440\u0438\u0447\u0438\u043d\u0430',
                'verbose_name_plural': '\u041f\u0440\u0438\u0447\u0438\u043d\u044b',
            },
            bases=(models.Model,),
        ),
    ]
