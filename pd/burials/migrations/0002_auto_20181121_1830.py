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
        ('burials', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reason',
            name='org',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='users.Org', verbose_name='\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='reason',
            unique_together=set([('org', 'reason_type', 'name')]),
        ),
        migrations.AddField(
            model_name='placestatusfiles',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='placestatusfiles',
            name='placestatus',
            field=models.ForeignKey(to='burials.PlaceStatus'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='placestatus',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='placestatus',
            name='place',
            field=models.ForeignKey(verbose_name='\u041c\u0435\u0441\u0442\u043e', to='burials.Place'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='placesize',
            name='org',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='users.Org', verbose_name='\u041e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044f'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='placesize',
            unique_together=set([('org', 'graves_count')]),
        ),
        migrations.AddField(
            model_name='placephoto',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='placephoto',
            name='place',
            field=models.ForeignKey(to='burials.Place'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='area',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0423\u0447\u0430\u0441\u0442\u043e\u043a', blank=True, to='burials.Area', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='caretaker',
            field=models.ForeignKey(related_name=b'caretaker_places', on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0441\u043c\u043e\u0442\u0440\u0438\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='cemetery',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435', to='burials.Cemetery'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='responsible',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439', blank=True, to='persons.AlivePerson', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='user_processed',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c, \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u0430\u0432\u0448\u0438\u0439 \u0444\u043e\u0442\u043e \u043c\u0435\u0441\u0442\u0430'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='place',
            unique_together=set([('cemetery', 'area', 'row', 'place')]),
        ),
        migrations.AddField(
            model_name='orderplace',
            name='area',
            field=models.ForeignKey(verbose_name='\u0423\u0447\u0430\u0441\u0442\u043e\u043a', to='burials.Area', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderplace',
            name='cemetery',
            field=models.ForeignKey(verbose_name='\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435', to='burials.Cemetery', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderplace',
            name='order',
            field=models.OneToOneField(verbose_name='\u0417\u0430\u043a\u0430\u0437', to='orders.Order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='grave',
            name='place',
            field=models.ForeignKey(verbose_name='\u041c\u0435\u0441\u0442\u043e', to='burials.Place'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='grave',
            unique_together=set([('place', 'grave_number')]),
        ),
        migrations.AddField(
            model_name='exhumationrequest',
            name='agent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0410\u0433\u0435\u043d\u0442', blank=True, to='users.Profile', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='exhumationrequest',
            name='applicant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0417\u0430\u043a\u0430\u0437\u0447\u0438\u043a-\u0424\u041b', blank=True, to='persons.AlivePerson', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='exhumationrequest',
            name='applicant_organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0417\u0430\u043a\u0430\u0437\u0447\u0438\u043a-\u042e\u041b', blank=True, to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='exhumationrequest',
            name='burial',
            field=models.OneToOneField(editable=False, to='burials.Burial'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='exhumationrequest',
            name='dover',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0414\u043e\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u044c', blank=True, to='users.Dover', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='exhumationrequest',
            name='place',
            field=models.ForeignKey(editable=False, to='burials.Place', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cemeteryschema',
            name='cemetery',
            field=models.OneToOneField(to='burials.Cemetery'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cemeteryschema',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cemeteryphoto',
            name='cemetery',
            field=models.OneToOneField(to='burials.Cemetery'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cemeteryphoto',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cemeterycoordinates',
            name='cemetery',
            field=models.ForeignKey(related_name=b'coordinates', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435', to='burials.Cemetery'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='cemeterycoordinates',
            unique_together=set([('cemetery', 'angle_number')]),
        ),
        migrations.AddField(
            model_name='cemetery',
            name='address',
            field=models.ForeignKey(editable=False, to='geo.Location', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cemetery',
            name='caretaker',
            field=models.ForeignKey(related_name=b'caretaker_cemeteries', on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0441\u043c\u043e\u0442\u0440\u0438\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cemetery',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0412\u043b\u0430\u0434\u0435\u043b\u0435\u0446', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cemetery',
            name='ugh',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0423\u0413\u0425', to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='cemetery',
            unique_together=set([('ugh', 'name')]),
        ),
        migrations.AddField(
            model_name='burialfiles',
            name='burial',
            field=models.ForeignKey(to='burials.Burial'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burialfiles',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burialcomment',
            name='burial',
            field=models.ForeignKey(verbose_name='\u0417\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0435', to='burials.Burial'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burialcomment',
            name='creator',
            field=models.ForeignKey(verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burialcomment',
            name='modifier',
            field=models.ForeignKey(related_name=b'modified_by', verbose_name='\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0439 \u0438\u0437\u043c\u0435\u043d\u0438\u0432\u0448\u0438\u0439', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='agent',
            field=models.ForeignKey(related_name=b'agent_burials', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0410\u0433\u0435\u043d\u0442', blank=True, to='users.Profile', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='applicant',
            field=models.ForeignKey(related_name=b'applied_burials', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0417\u0430\u044f\u0432\u0438\u0442\u0435\u043b\u044c', blank=True, to='persons.AlivePerson', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='applicant_organization',
            field=models.ForeignKey(related_name=b'applicant_organization_burials', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0417\u0430\u044f\u0432\u0438\u0442\u0435\u043b\u044c-\u042e\u041b', blank=True, to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='area',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0423\u0447\u0430\u0441\u0442\u043e\u043a', blank=True, to='burials.Area', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='cemetery',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435', blank=True, to='burials.Cemetery', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='changed_by',
            field=models.ForeignKey(related_name=b'changed_by_burials', on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='deadman',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='persons.DeadPerson', null=True, verbose_name='\u0423\u0441\u043e\u043f\u0448\u0438\u0439'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='dover',
            field=models.ForeignKey(related_name=b'dover_burials', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0414\u043e\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u044c', blank=True, to='users.Dover', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='grave',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, editable=False, to='burials.Grave', null=True, verbose_name='\u041c\u043e\u0433\u0438\u043b\u0430'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='loru',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041f\u043e\u0441\u0440\u0435\u0434\u043d\u0438\u043a', to='users.Org', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='loru_agent',
            field=models.ForeignKey(related_name=b'loru_agent_burials', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0410\u0433\u0435\u043d\u0442', blank=True, to='users.Profile', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='loru_dover',
            field=models.ForeignKey(related_name=b'loru_dover_burials', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0414\u043e\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u044c', blank=True, to='users.Dover', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='place',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041c\u0435\u0441\u0442\u043e', blank=True, to='burials.Place', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='responsible',
            field=models.ForeignKey(related_name=b'responsible_burials', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439', blank=True, to='persons.AlivePerson', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='burial',
            name='ugh',
            field=models.ForeignKey(related_name=b'ugh_created', on_delete=django.db.models.deletion.PROTECT, editable=False, to='users.Org', null=True, verbose_name='\u0423\u0413\u0425'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='areaphoto',
            name='area',
            field=models.ForeignKey(to='burials.Area'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='areaphoto',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='areacoordinates',
            name='area',
            field=models.ForeignKey(related_name=b'coordinates', on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0423\u0447\u0430\u0441\u0442\u043e\u043a', to='burials.Area'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='areacoordinates',
            unique_together=set([('area', 'angle_number')]),
        ),
        migrations.AddField(
            model_name='area',
            name='caretaker',
            field=models.ForeignKey(related_name=b'caretaker_areas', on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0441\u043c\u043e\u0442\u0440\u0438\u0442\u0435\u043b\u044c'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='area',
            name='cemetery',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041a\u043b\u0430\u0434\u0431\u0438\u0449\u0435', to='burials.Cemetery'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='area',
            name='purpose',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435', to='burials.AreaPurpose', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='area',
            unique_together=set([('cemetery', 'name')]),
        ),
        migrations.CreateModel(
            name='Burial1',
            fields=[
            ],
            options={
                'verbose_name': '\u0417\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0435',
                'managed': False,
                'verbose_name_plural': '\u0417\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0435',
            },
            bases=(models.Model,),
        ),
    ]
