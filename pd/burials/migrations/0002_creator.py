# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Cemetery.creator'
        db.alter_column('burials_cemetery', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True))

        # Changing field 'Cemetery.date_of_creation'
        db.alter_column('burials_cemetery', 'date_of_creation', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True))
        # Adding field 'Service.creator'
        db.add_column('burials_service', 'creator',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True),
                      keep_default=False)

        # Adding field 'Service.date_of_creation'
        db.add_column('burials_service', 'date_of_creation',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Operation.creator'
        db.add_column('burials_operation', 'creator',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True),
                      keep_default=False)

        # Adding field 'Operation.date_of_creation'
        db.add_column('burials_operation', 'date_of_creation',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Cemetery.creator'
        raise RuntimeError("Cannot reverse this migration. 'Cemetery.creator' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Cemetery.date_of_creation'
        raise RuntimeError("Cannot reverse this migration. 'Cemetery.date_of_creation' and its values cannot be restored.")
        # Deleting field 'Service.creator'
        db.delete_column('burials_service', 'creator_id')

        # Deleting field 'Service.date_of_creation'
        db.delete_column('burials_service', 'date_of_creation')

        # Deleting field 'Operation.creator'
        db.delete_column('burials_operation', 'creator_id')

        # Deleting field 'Operation.date_of_creation'
        db.delete_column('burials_operation', 'date_of_creation')


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
        'burials.burial': {
            'Meta': {'object_name': 'Burial'},
            'account_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'acct_num_num': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'acct_num_str1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'acct_num_str2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'orders'", 'null': 'True', 'to': "orm['orgs.Agent']"}),
            'client_organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ordr_customer'", 'null': 'True', 'to': "orm['orgs.Organization']"}),
            'client_person': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ordr_customer'", 'null': 'True', 'to': "orm['persons.Person']"}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'date_fact': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'date_plan': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doverennost': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orgs.Doverennost']", 'null': 'True', 'blank': 'True'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edited_burials'", 'null': 'True', 'to': "orm['auth.User']"}),
            'exhumated_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'grave_id': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'operation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Operation']"}),
            'payment_type': ('django.db.models.fields.CharField', [], {'default': "'nal'", 'max_length': '255'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'buried'", 'to': "orm['persons.Person']"}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Place']"}),
            'print_info': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'time_fact': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'burials.cemetery': {
            'Meta': {'ordering': "['ordering', 'name']", 'object_name': 'Cemetery'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'ordering': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cemetery'", 'to': "orm['orgs.Organization']"}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'burials.comment': {
            'Meta': {'object_name': 'Comment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'burial': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Burial']"}),
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'burials.operation': {
            'Meta': {'ordering': "['ordering', 'op_type']", 'object_name': 'Operation'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'op_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ordering': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        'burials.place': {
            'Meta': {'object_name': 'Place'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']"}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'gps_x': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'gps_y': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'responsible': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Person']", 'null': 'True', 'blank': 'True'}),
            'rooms': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'blank': 'True'}),
            'row': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'seat': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'unowned': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'burials.service': {
            'Meta': {'object_name': 'Service'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'measure': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ordering': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'})
        },
        'burials.serviceposition': {
            'Meta': {'object_name': 'ServicePosition'},
            'burial': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Burial']"}),
            'count': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Service']"})
        },
        'burials.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'catafalque_text': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'default_cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']", 'null': 'True', 'blank': 'True'}),
            'default_city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.City']", 'null': 'True', 'blank': 'True'}),
            'default_country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Country']", 'null': 'True', 'blank': 'True'}),
            'default_operation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Operation']", 'null': 'True', 'blank': 'True'}),
            'default_region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Region']", 'null': 'True', 'blank': 'True'}),
            'naryad_text': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'org_registrator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'org_registrators'", 'null': 'True', 'to': "orm['orgs.Organization']"}),
            'org_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'org_users'", 'null': 'True', 'to': "orm['orgs.Organization']"}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orgs.Organization']", 'null': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Person']", 'null': 'True'}),
            'records_order_by': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'records_per_page': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
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
        'orgs.agent': {
            'Meta': {'object_name': 'Agent'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'agents'", 'to': "orm['orgs.Organization']"}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Person']"})
        },
        'orgs.doverennost': {
            'Meta': {'ordering': "['-issue_date']", 'object_name': 'Doverennost'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'doverennosti'", 'to': "orm['orgs.Agent']"}),
            'expire_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        },
        'orgs.organization': {
            'Meta': {'ordering': "['name']", 'object_name': 'Organization'},
            'ceo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Person']", 'null': 'True', 'blank': 'True'}),
            'ceo_document': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ceo_name_who': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inn': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'}),
            'kpp': ('django.db.models.fields.CharField', [], {'max_length': '9', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '99'}),
            'ogrn': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'})
        },
        'persons.person': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'Person'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'birth_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'birth_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'death_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        }
    }

    complete_apps = ['burials']