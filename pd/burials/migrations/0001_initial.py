# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Cemetery'
        db.create_table(u'burials_cemetery', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cemetery', to=orm['orgs.Organization'])),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.Location'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('date_of_creation', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('ordering', self.gf('django.db.models.fields.PositiveIntegerField')(default=1, blank=True)),
            ('phones', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'burials', ['Cemetery'])

        # Adding model 'Place'
        db.create_table(u'burials_place', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cemetery', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Cemetery'])),
            ('area', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('row', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('seat', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('gps_x', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('gps_y', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('responsible', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['persons.Person'], null=True, blank=True)),
            ('rooms', self.gf('django.db.models.fields.PositiveIntegerField')(default=1, blank=True)),
            ('unowned', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('date_of_creation', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'burials', ['Place'])

        # Adding model 'Operation'
        db.create_table(u'burials_operation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('op_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ordering', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal(u'burials', ['Operation'])

        # Adding model 'Burial'
        db.create_table(u'burials_burial', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('operation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Operation'])),
            ('date_plan', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('date_fact', self.gf('django.db.models.fields.DateField')(null=True)),
            ('time_fact', self.gf('django.db.models.fields.TimeField')(null=True, blank=True)),
            ('exhumated_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('place', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Place'])),
            ('grave_id', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='buried', to=orm['persons.Person'])),
            ('client_person', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='ordr_customer', null=True, to=orm['persons.Person'])),
            ('client_organization', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='ordr_customer', null=True, to=orm['orgs.Organization'])),
            ('doverennost', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['orgs.Doverennost'], null=True, blank=True)),
            ('agent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='orders', null=True, to=orm['orgs.Agent'])),
            ('acct_num_str1', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('acct_num_num', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('acct_num_str2', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('print_info', self.gf('django.db.models.fields.TextField')(null=True)),
            ('payment_type', self.gf('django.db.models.fields.CharField')(default='nal', max_length=255)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='edited_burials', null=True, to=orm['auth.User'])),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'burials', ['Burial'])

        # Adding model 'UserProfile'
        db.create_table(u'burials_userprofile', (
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, primary_key=True)),
            ('default_cemetery', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Cemetery'], null=True, blank=True)),
            ('default_operation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Operation'], null=True, blank=True)),
            ('default_country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.Country'], null=True, blank=True)),
            ('default_region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.Region'], null=True, blank=True)),
            ('default_city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.City'], null=True, blank=True)),
            ('records_per_page', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('records_order_by', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('org_user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='org_users', null=True, to=orm['orgs.Organization'])),
            ('org_registrator', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='org_registrators', null=True, to=orm['orgs.Organization'])),
            ('catafalque_text', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('naryad_text', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['persons.Person'], null=True)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['orgs.Organization'], null=True)),
        ))
        db.send_create_signal(u'burials', ['UserProfile'])

        # Adding model 'Service'
        db.create_table(u'burials_service', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('measure', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('ordering', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal(u'burials', ['Service'])

        # Adding model 'ServicePosition'
        db.create_table(u'burials_serviceposition', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('burial', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Burial'])),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Service'])),
            ('count', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal(u'burials', ['ServicePosition'])

        # Adding model 'Comment'
        db.create_table(u'burials_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('burial', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['burials.Burial'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'burials', ['Comment'])


    def backwards(self, orm):
        # Deleting model 'Cemetery'
        db.delete_table(u'burials_cemetery')

        # Deleting model 'Place'
        db.delete_table(u'burials_place')

        # Deleting model 'Operation'
        db.delete_table(u'burials_operation')

        # Deleting model 'Burial'
        db.delete_table(u'burials_burial')

        # Deleting model 'UserProfile'
        db.delete_table(u'burials_userprofile')

        # Deleting model 'Service'
        db.delete_table(u'burials_service')

        # Deleting model 'ServicePosition'
        db.delete_table(u'burials_serviceposition')

        # Deleting model 'Comment'
        db.delete_table(u'burials_comment')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'burials.burial': {
            'Meta': {'object_name': 'Burial'},
            'account_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'acct_num_num': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'acct_num_str1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'acct_num_str2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'orders'", 'null': 'True', 'to': u"orm['orgs.Agent']"}),
            'client_organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ordr_customer'", 'null': 'True', 'to': u"orm['orgs.Organization']"}),
            'client_person': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ordr_customer'", 'null': 'True', 'to': u"orm['persons.Person']"}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'date_fact': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'date_plan': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doverennost': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['orgs.Doverennost']", 'null': 'True', 'blank': 'True'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edited_burials'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'exhumated_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'grave_id': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'operation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['burials.Operation']"}),
            'payment_type': ('django.db.models.fields.CharField', [], {'default': "'nal'", 'max_length': '255'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'buried'", 'to': u"orm['persons.Person']"}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['burials.Place']"}),
            'print_info': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'time_fact': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'burials.cemetery': {
            'Meta': {'ordering': "['ordering', 'name']", 'object_name': 'Cemetery'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Location']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'ordering': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cemetery'", 'to': u"orm['orgs.Organization']"}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'burials.comment': {
            'Meta': {'object_name': 'Comment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'burial': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['burials.Burial']"}),
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'burials.operation': {
            'Meta': {'ordering': "['ordering', 'op_type']", 'object_name': 'Operation'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'op_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ordering': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        u'burials.place': {
            'Meta': {'object_name': 'Place'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['burials.Cemetery']"}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'gps_x': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'gps_y': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'responsible': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['persons.Person']", 'null': 'True', 'blank': 'True'}),
            'rooms': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'blank': 'True'}),
            'row': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'seat': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'unowned': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'burials.service': {
            'Meta': {'object_name': 'Service'},
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'measure': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ordering': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'})
        },
        u'burials.serviceposition': {
            'Meta': {'object_name': 'ServicePosition'},
            'burial': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['burials.Burial']"}),
            'count': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['burials.Service']"})
        },
        u'burials.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'catafalque_text': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'default_cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['burials.Cemetery']", 'null': 'True', 'blank': 'True'}),
            'default_city': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.City']", 'null': 'True', 'blank': 'True'}),
            'default_country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Country']", 'null': 'True', 'blank': 'True'}),
            'default_operation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['burials.Operation']", 'null': 'True', 'blank': 'True'}),
            'default_region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Region']", 'null': 'True', 'blank': 'True'}),
            'naryad_text': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'org_registrator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'org_registrators'", 'null': 'True', 'to': u"orm['orgs.Organization']"}),
            'org_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'org_users'", 'null': 'True', 'to': u"orm['orgs.Organization']"}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['orgs.Organization']", 'null': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['persons.Person']", 'null': 'True'}),
            'records_order_by': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'records_per_page': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'geo.city': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('region', 'name'),)", 'object_name': 'City', 'db_table': "'common_geocity'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Region']"})
        },
        u'geo.country': {
            'Meta': {'ordering': "['name']", 'object_name': 'Country', 'db_table': "'common_geocountry'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'})
        },
        u'geo.location': {
            'Meta': {'object_name': 'Location'},
            'block': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'building': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.City']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Country']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'flat': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'gps_x': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'gps_y': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'house': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'post_index': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Region']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'street': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Street']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        u'geo.region': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('country', 'name'),)", 'object_name': 'Region', 'db_table': "'common_georegion'"},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Country']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'geo.street': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('city', 'name'),)", 'object_name': 'Street'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.City']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'orgs.agent': {
            'Meta': {'object_name': 'Agent'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'agents'", 'to': u"orm['orgs.Organization']"}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['persons.Person']"})
        },
        u'orgs.doverennost': {
            'Meta': {'ordering': "['-issue_date']", 'object_name': 'Doverennost'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'doverennosti'", 'to': u"orm['orgs.Agent']"}),
            'expire_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        },
        u'orgs.organization': {
            'Meta': {'ordering': "['name']", 'object_name': 'Organization'},
            'ceo': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['persons.Person']", 'null': 'True', 'blank': 'True'}),
            'ceo_document': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ceo_name_who': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inn': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'}),
            'kpp': ('django.db.models.fields.CharField', [], {'max_length': '9', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Location']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '99'}),
            'ogrn': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'persons.person': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'Person'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geo.Location']", 'null': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'birth_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'birth_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'death_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'})
        }
    }

    complete_apps = ['burials']