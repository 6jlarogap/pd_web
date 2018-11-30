# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Country'
        db.create_table('common_geocountry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
        ))
        db.send_create_signal('geo', ['Country'])

        # Adding model 'Region'
        db.create_table('common_georegion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.Country'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('geo', ['Region'])

        # Adding unique constraint on 'Region', fields ['country', 'name']
        db.create_unique('common_georegion', ['country_id', 'name'])

        # Adding model 'City'
        db.create_table('common_geocity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.Region'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('geo', ['City'])

        # Adding unique constraint on 'City', fields ['region', 'name']
        db.create_unique('common_geocity', ['region_id', 'name'])

        # Adding model 'Street'
        db.create_table('geo_street', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.City'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('geo', ['Street'])

        # Adding unique constraint on 'Street', fields ['city', 'name']
        db.create_unique('geo_street', ['city_id', 'name'])

        # Adding model 'Location'
        db.create_table('geo_location', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.Country'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.Region'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.City'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('street', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.Street'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('post_index', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('house', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('block', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('building', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('flat', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('gps_x', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('gps_y', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('info', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('geo', ['Location'])


    def backwards(self, orm):
        # Removing unique constraint on 'Street', fields ['city', 'name']
        db.delete_unique('geo_street', ['city_id', 'name'])

        # Removing unique constraint on 'City', fields ['region', 'name']
        db.delete_unique('common_geocity', ['region_id', 'name'])

        # Removing unique constraint on 'Region', fields ['country', 'name']
        db.delete_unique('common_georegion', ['country_id', 'name'])

        # Deleting model 'Country'
        db.delete_table('common_geocountry')

        # Deleting model 'Region'
        db.delete_table('common_georegion')

        # Deleting model 'City'
        db.delete_table('common_geocity')

        # Deleting model 'Street'
        db.delete_table('geo_street')

        # Deleting model 'Location'
        db.delete_table('geo_location')


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
        }
    }

    complete_apps = ['geo']