# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'DeadPerson.death_date_no_month'
        db.add_column('persons_deadperson', 'death_date_no_month',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'DeadPerson.death_date_no_day'
        db.add_column('persons_deadperson', 'death_date_no_day',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'AlivePerson.death_date'
        db.delete_column('persons_aliveperson', 'death_date')


    def backwards(self, orm):
        # Deleting field 'DeadPerson.death_date_no_month'
        db.delete_column('persons_deadperson', 'death_date_no_month')

        # Deleting field 'DeadPerson.death_date_no_day'
        db.delete_column('persons_deadperson', 'death_date_no_day')

        # Adding field 'AlivePerson.death_date'
        db.add_column('persons_aliveperson', 'death_date',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)


    models = {
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
        'persons.deathcertificate': {
            'Meta': {'object_name': 'DeathCertificate'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.DeadPerson']", 'unique': 'True'}),
            'release_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            's_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'series': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zags': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.ZAGS']", 'null': 'True'})
        },
        'persons.documentsource': {
            'Meta': {'object_name': 'DocumentSource'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'persons.iddocumenttype': {
            'Meta': {'object_name': 'IDDocumentType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'persons.personid': {
            'Meta': {'object_name': 'PersonID'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.IDDocumentType']"}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'person': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.BasePerson']", 'unique': 'True'}),
            'series': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.DocumentSource']", 'null': 'True', 'blank': 'True'})
        },
        'persons.zags': {
            'Meta': {'ordering': "['name']", 'object_name': 'ZAGS'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['persons']