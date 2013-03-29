# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Burial.burial_container'
        db.add_column('burials_burial', 'burial_container',
                      self.gf('django.db.models.fields.CharField')(default='container_coffin', max_length=255, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Burial.burial_container'
        db.delete_column('burials_burial', 'burial_container')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'burials.area': {
            'Meta': {'object_name': 'Area'},
            'availability': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']", 'on_delete': 'models.PROTECT'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'places_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'purpose': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.AreaPurpose']", 'null': 'True', 'on_delete': 'models.PROTECT'})
        },
        'burials.areapurpose': {
            'Meta': {'object_name': 'AreaPurpose'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'burials.burial': {
            'Meta': {'object_name': 'Burial'},
            'account_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'agent_director': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'applied_burials'", 'null': 'True', 'to': "orm['persons.AlivePerson']"}),
            'applicant_organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'loru_created'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['users.Org']"}),
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Area']", 'null': 'True', 'blank': 'True'}),
            'burial_container': ('django.db.models.fields.CharField', [], {'default': "'container_coffin'", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'burial_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'changed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'changed_requests'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['auth.User']"}),
            'deadman': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.DeadPerson']", 'null': 'True'}),
            'dover': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Dover']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'fact_date': ('pd.models.UnclearDateModelField', [], {'null': 'True', 'blank': 'True'}),
            u'fact_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'fact_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'grave_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['orders.Order']", 'unique': 'True', 'null': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Place']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'place_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'plan_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'plan_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'responsible': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'responsible_burials'", 'null': 'True', 'to': "orm['persons.AlivePerson']"}),
            'row': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'source_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'draft'", 'max_length': '255'}),
            'ugh': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ugh_created'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['users.Org']"})
        },
        'burials.cemetery': {
            'Meta': {'object_name': 'Cemetery'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'places_algo': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '255'}),
            'time_begin': ('django.db.models.fields.TimeField', [], {}),
            'time_end': ('django.db.models.fields.TimeField', [], {}),
            'time_slots': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'ugh': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True', 'on_delete': 'models.PROTECT'})
        },
        'burials.exhumationrequest': {
            'Meta': {'object_name': 'ExhumationRequest'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'agent_director': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.AlivePerson']", 'null': 'True', 'blank': 'True'}),
            'applicant_organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True', 'blank': 'True'}),
            'burial': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['burials.Burial']", 'unique': 'True'}),
            'dover': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Dover']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'fact_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Place']", 'null': 'True'}),
            'plan_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'plan_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'burials.place': {
            'Meta': {'object_name': 'Place'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Area']", 'null': 'True', 'blank': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']", 'on_delete': 'models.PROTECT'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'places_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'responsible': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.AlivePerson']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'row': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'burials.reason': {
            'Meta': {'object_name': 'Reason'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'reason_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'text': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'geo.city': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('region', 'name'),)", 'object_name': 'City', 'db_table': "'common_geocity'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Region']"})
        },
        'geo.country': {
            'Meta': {'ordering': "['name']", 'object_name': 'Country', 'db_table': "'common_geocountry'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'})
        },
        'geo.location': {
            'Meta': {'object_name': 'Location'},
            'block': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'building': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.City']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Country']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'flat': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'gps_x': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'gps_y': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'house': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'post_index': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Region']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'street': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Street']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'geo.region': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('country', 'name'),)", 'object_name': 'Region', 'db_table': "'common_georegion'"},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'geo.street': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('city', 'name'),)", 'object_name': 'Street'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.City']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'orders.order': {
            'Meta': {'object_name': 'Order'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'agent_director': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'annulated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.AlivePerson']", 'null': 'True', 'blank': 'True'}),
            'applicant_organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'org_orders'", 'null': 'True', 'to': "orm['users.Org']"}),
            'cost': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'dover': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Dover']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loru': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True'}),
            'loru_number': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'payment': ('django.db.models.fields.CharField', [], {'default': "'cash'", 'max_length': '255'})
        },
        'persons.aliveperson': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'AlivePerson', '_ormbases': ['persons.BasePerson']},
            'baseperson_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.BasePerson']", 'unique': 'True', 'primary_key': 'True'}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'persons.baseperson': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'BasePerson'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'persons.deadperson': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'DeadPerson', '_ormbases': ['persons.BasePerson']},
            'baseperson_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.BasePerson']", 'unique': 'True', 'primary_key': 'True'}),
            'birth_date': ('pd.models.UnclearDateModelField', [], {'null': 'True', 'blank': 'True'}),
            u'birth_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'birth_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'death_date': ('pd.models.UnclearDateModelField', [], {'null': 'True', 'blank': 'True'}),
            u'death_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'death_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'users.dover': {
            'Meta': {'object_name': 'Dover'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']"}),
            'begin': ('django.db.models.fields.DateField', [], {}),
            'document': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'target_org': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True'})
        },
        'users.org': {
            'Meta': {'object_name': 'Org'},
            'director': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inn': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'kpp': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'off_address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True', 'blank': 'True'}),
            'ogrn': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'users.profile': {
            'Meta': {'object_name': 'Profile'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Area']", 'null': 'True', 'blank': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']", 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Country']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_agent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lat': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '30', 'decimal_places': '27', 'blank': 'True'}),
            'lng': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '30', 'decimal_places': '27', 'blank': 'True'}),
            'numbers_algo': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'org': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True'}),
            'region_fias': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True'}),
            'user_first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user_last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user_middle_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['burials']