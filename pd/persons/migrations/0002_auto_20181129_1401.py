# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0001_initial'),
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('burials', '0002_auto_20181129_1401'),
        ('persons', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='deathcertificate',
            name='zags',
            field=models.ForeignKey(verbose_name='\u0417\u0410\u0413\u0421', blank=True, to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customplace',
            name='address',
            field=models.ForeignKey(verbose_name='\u0410\u0434\u0440\u0435\u0441', to='geo.Location', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customplace',
            name='favorite_performer',
            field=models.ForeignKey(verbose_name='\u041f\u0440\u0435\u0434\u043f\u043e\u0447\u0442\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c', blank=True, to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customplace',
            name='place',
            field=models.ForeignKey(verbose_name='\u041c\u0435\u0441\u0442\u043e', to='burials.Place', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customplace',
            name='user',
            field=models.ForeignKey(verbose_name='\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0437\u0430 \u043c\u0435\u0441\u0442\u043e \u0438\u043b\u0438 \u0443\u043a\u0430\u0437\u0430\u0432\u0448\u0438\u0439 \u043c\u0435\u0441\u0442\u043e', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='customplace',
            unique_together=set([('user', 'place')]),
        ),
        migrations.AddField(
            model_name='custompersonpermission',
            name='customperson',
            field=models.ForeignKey(to='persons.CustomPerson'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customperson',
            name='customplace',
            field=models.ForeignKey(verbose_name='\u041c\u0435\u0441\u0442\u043e \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f', blank=True, to='persons.CustomPlace', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customperson',
            name='person',
            field=models.ForeignKey(verbose_name='\u041b\u0438\u0446\u043e', to='persons.BasePerson', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customperson',
            name='user',
            field=models.ForeignKey(verbose_name='\u0412\u043b\u0430\u0434\u0435\u043b\u0435\u0446 \u0438\u043b\u0438 \u0443\u043a\u0430\u0437\u0430\u0432\u0448\u0438\u0439 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u043d\u043e\u0433\u043e', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='baseperson',
            name='address',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='geo.Location', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='aliveperson',
            name='user',
            field=models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0437\u0430 \u043c\u0435\u0441\u0442\u043e \u0438\u043b\u0438 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c- \u0444\u0438\u0437. \u043b\u0438\u0446\u043e'),
            preserve_default=True,
        ),
    ]
