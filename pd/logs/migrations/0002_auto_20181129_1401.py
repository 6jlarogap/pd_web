# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
        ('logs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='loginlog',
            name='org',
            field=models.ForeignKey(verbose_name='\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f', to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='loginlog',
            name='user',
            field=models.ForeignKey(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='log',
            name='ct',
            field=models.ForeignKey(editable=False, to='contenttypes.ContentType', null=True, verbose_name='\u0422\u0438\u043f'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='log',
            name='user',
            field=models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='deletelog',
            name='ct',
            field=models.ForeignKey(editable=False, to='contenttypes.ContentType', verbose_name='\u0422\u0438\u043f'),
            preserve_default=True,
        ),
    ]
