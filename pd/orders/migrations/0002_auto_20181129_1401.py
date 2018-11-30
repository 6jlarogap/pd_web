# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0001_initial'),
        ('users', '0001_initial'),
        ('orders', '0001_initial'),
        ('persons', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('burials', '0002_auto_20181129_1401'),
    ]

    operations = [
        migrations.AddField(
            model_name='productgroup',
            name='loru',
            field=models.ForeignKey(verbose_name='\u041b\u041e\u0420\u0423', to='users.Org'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='productgroup',
            name='productcategory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f', to='orders.ProductCategory'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='productgroup',
            unique_together=set([('loru', 'productcategory', 'name')]),
        ),
        migrations.AddField(
            model_name='product',
            name='loru',
            field=models.ForeignKey(verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a', to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='productcategory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f', to='orders.ProductCategory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='productgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='orders.ProductGroup', null=True, verbose_name='\u041f\u043e\u0434\u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orgserviceprice',
            name='measure',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0415\u0434\u0438\u043d\u0438\u0446\u0430 \u0438\u0437\u043c\u0435\u0440\u0435\u043d\u0438\u044f', to='orders.Measure'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orgserviceprice',
            name='orgservice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0421\u043b\u0443\u0436\u0431\u0430', to='orders.OrgService'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='orgserviceprice',
            unique_together=set([('orgservice', 'measure')]),
        ),
        migrations.AddField(
            model_name='orgservice',
            name='org',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a', to='users.Org'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orgservice',
            name='service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0422\u0438\u043f \u0441\u0435\u0440\u0432\u0438\u0441\u0430', to='orders.Service'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='orgservice',
            unique_together=set([('org', 'service')]),
        ),
        migrations.AddField(
            model_name='orderwebpay',
            name='order',
            field=models.ForeignKey(verbose_name='\u0417\u0430\u043a\u0430\u0437', to='orders.Order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderitem',
            name='order',
            field=models.ForeignKey(editable=False, to='orders.Order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderitem',
            name='product',
            field=models.ForeignKey(verbose_name='\u0422\u043e\u0432\u0430\u0440', to='orders.Product'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderitem',
            name='productcategory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='orders.ProductCategory', verbose_name='\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderitem',
            name='productgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='orders.ProductGroup', null=True, verbose_name='\u041f\u043e\u0434\u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ordercomment',
            name='order',
            field=models.ForeignKey(verbose_name='\u0417\u0430\u043a\u0430\u0437', to='orders.Order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ordercomment',
            name='user',
            field=models.ForeignKey(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='address',
            field=models.ForeignKey(editable=False, to='geo.Location', null=True, verbose_name='\u0410\u0434\u0440\u0435\u0441'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='agent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0410\u0433\u0435\u043d\u0442', blank=True, to='users.Profile', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='applicant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0417\u0430\u043a\u0430\u0437\u0447\u0438\u043a-\u0424\u041b', blank=True, to='persons.AlivePerson', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='applicant_organization',
            field=models.ForeignKey(related_name='org_orders', verbose_name='\u0417\u0430\u043a\u0430\u0437\u0447\u0438\u043a-\u042e\u041b', blank=True, to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='burial',
            field=models.ForeignKey(related_name='burial_orders', editable=False, to='burials.Burial', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='customplace',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='persons.CustomPlace', null=True, verbose_name='\u041c\u0435\u0441\u0442\u043e \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dover',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0414\u043e\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u044c', blank=True, to='users.Dover', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='loru',
            field=models.ForeignKey(verbose_name='\u041b\u041e\u0420\u0423', to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='measure',
            name='service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0421\u0435\u0440\u0432\u0438\u0441', to='orders.Service'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='measure',
            unique_together=set([('service', 'name')]),
        ),
        migrations.AddField(
            model_name='coffindata',
            name='order',
            field=models.OneToOneField(editable=False, to='orders.Order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='catafalquedata',
            name='order',
            field=models.OneToOneField(editable=False, to='orders.Order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='addinfodata',
            name='order',
            field=models.OneToOneField(editable=False, to='orders.Order'),
            preserve_default=True,
        ),
    ]
