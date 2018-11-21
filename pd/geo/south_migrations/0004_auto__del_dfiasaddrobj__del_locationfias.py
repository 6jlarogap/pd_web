# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'DFiasAddrobj'
        db.delete_table(u'd_fias_addrobj')

        # Deleting model 'LocationFIAS'
        db.delete_table('geo_locationfias')


    def backwards(self, orm):
        # Adding model 'DFiasAddrobj'
        db.create_table(u'd_fias_addrobj', (
            ('areacode', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('streetcode', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('offname', self.gf('django.db.models.fields.CharField')(max_length=120)),
            ('extrcode', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('aolevel', self.gf('django.db.models.fields.IntegerField')()),
            ('shortname', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('ctarcode', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('citycode', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('enddate', self.gf('django.db.models.fields.DateField')()),
            ('placecode', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('aoguid', self.gf('django.db.models.fields.CharField')(max_length=36, primary_key=True)),
            ('formalname', self.gf('django.db.models.fields.CharField')(max_length=120)),
            ('sextcode', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('parentguid', self.gf('django.db.models.fields.CharField')(max_length=36)),
        ))
        db.send_create_signal('geo', ['DFiasAddrobj'])

        # Adding model 'LocationFIAS'
        db.create_table('geo_locationfias', (
            ('loc', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fias_parents', to=orm['geo.Location'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('level', self.gf('django.db.models.fields.PositiveSmallIntegerField')(db_index=True)),
            ('guid', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('geo', ['LocationFIAS'])


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