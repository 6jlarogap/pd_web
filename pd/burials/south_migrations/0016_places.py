# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Place'
        db.create_table('burials_place', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cemetery', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Cemetery'])),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Area'], null=True, blank=True)),
            ('row', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('place', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('responsible', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['persons.AlivePerson'], null=True, blank=True)),
        ))
        db.send_create_signal('burials', ['Place'])

        # Adding model 'Area'
        db.create_table('burials_area', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cemetery', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Cemetery'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('burials', ['Area'])

        # Adding field 'Burial.area'
        db.add_column('burials_burialrequest', 'area',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Area'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'Burial.row'
        db.add_column('burials_burialrequest', 'row',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Burial.responsible'
        db.add_column('burials_burialrequest', 'responsible',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['persons.AlivePerson'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'Place'
        db.delete_table('burials_place')

        # Deleting model 'Area'
        db.delete_table('burials_area')

        # Deleting field 'Burial.area'
        db.delete_column('burials_burialrequest', 'area_id')

        # Deleting field 'Burial.row'
        db.delete_column('burials_burialrequest', 'row')

        # Deleting field 'Burial.responsible'
        db.delete_column('burials_burialrequest', 'responsible_id')


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
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'burials.burialrequest': {
            'Meta': {'object_name': 'Burial'},
            'approved_ugh': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Area']", 'null': 'True', 'blank': 'True'}),
            'backed_loru': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'burial_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']", 'null': 'True'}),
            'completed_ugh': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'deadman': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.DeadPerson']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loru': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True'}),
            'place_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'plan_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'plan_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'processed_loru': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'ready_loru': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'responsible': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.AlivePerson']", 'null': 'True', 'blank': 'True'}),
            'row': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'burials.cemetery': {
            'Meta': {'object_name': 'Cemetery'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'time_begin': ('django.db.models.fields.TimeField', [], {}),
            'time_end': ('django.db.models.fields.TimeField', [], {}),
            'time_slots': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'ugh': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True'})
        },
        'burials.place': {
            'Meta': {'object_name': 'Place'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Area']", 'null': 'True', 'blank': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'responsible': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.AlivePerson']", 'null': 'True', 'blank': 'True'}),
            'row': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
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
        'persons.aliveperson': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'AlivePerson', '_ormbases': ['persons.BasePerson']},
            'baseperson_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.BasePerson']", 'unique': 'True', 'primary_key': 'True'}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'persons.baseperson': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'BasePerson'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'birth_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'birth_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'persons.deadperson': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'DeadPerson', '_ormbases': ['persons.BasePerson']},
            'baseperson_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.BasePerson']", 'unique': 'True', 'primary_key': 'True'}),
            'death_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'death_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'death_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'users.org': {
            'Meta': {'object_name': 'Org'},
            'director': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'full_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inn': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['burials']