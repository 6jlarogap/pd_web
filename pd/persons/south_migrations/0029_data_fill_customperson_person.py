# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.db.models.query_utils import Q

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."

        # В тех СustomPlace, которые привязаны к Place, созданному в ОМС, создать
        # CustomPersons, соответсвующих усопшим в этом месте (не аннулированным,
        # не эксгумированным)
        #

        print "*** Poulating CustomPersons with DeadPersons in Burials of Places linked to CustomPlace"
        for customplace in orm['persons.CustomPlace'].objects.filter(place__isnull=False):
            q = Q(
                place=customplace.place,
                status='closed',
                annulated=False,
                deadman__isnull=False,
            )
            q &= ~Q(burial_container='container_bio')
            for burial in orm['burials.Burial'].objects.filter(q):
                deadman = burial.deadman
                customperson = orm['persons.CustomPerson'].objects.create(
                    person=deadman.baseperson_ptr,
                    last_name=deadman.last_name,
                    first_name=deadman.first_name,
                    middle_name=deadman.middle_name,
                    is_dead=True,
                    customplace=customplace,
                    birth_date=deadman.birth_date,
                    birth_date_no_day=deadman.birth_date_no_day,
                    birth_date_no_month=deadman.birth_date_no_month,
                    death_date=deadman.death_date,
                    death_date_no_day=deadman.death_date_no_day,
                    death_date_no_month=deadman.death_date_no_month,
                )
                
    def backwards(self, orm):
        "Write your backwards methods here."

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
        'billing.currency': {
            'Meta': {'unique_together': "(('code',),)", 'object_name': 'Currency'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'icon': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'rounding': ('django.db.models.fields.SmallIntegerField', [], {'default': '2'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'burials.area': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('cemetery', 'name'),)", 'object_name': 'Area'},
            'availability': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']", 'on_delete': 'models.PROTECT'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'places_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'purpose': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.AreaPurpose']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'square': ('django.db.models.fields.FloatField', [], {'null': 'True'})
        },
        'burials.areapurpose': {
            'Meta': {'object_name': 'AreaPurpose'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'burials.cemetery': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('ugh', 'name'),)", 'object_name': 'Cemetery'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True'}),
            'archive_burial_account_number_required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'archive_burial_fact_date_required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'on_delete': 'models.PROTECT'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'places_algo': ('django.db.models.fields.CharField', [], {'default': "'area'", 'max_length': '255'}),
            'places_algo_archive': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '255'}),
            'square': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'time_begin': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'time_end': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'time_slots': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ugh': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True', 'on_delete': 'models.PROTECT'})
        },
        'burials.place': {
            'Meta': {'ordering': "['row', 'place']", 'unique_together': "(('cemetery', 'area', 'row', 'place'),)", 'object_name': 'Place'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Area']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'available_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']", 'on_delete': 'models.PROTECT'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_military': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'dt_size_violated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'dt_unindentified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'dt_unowned': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'dt_wrong_fio': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'lng': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'oldplace': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'place': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'place_length': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'place_width': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'responsible': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.AlivePerson']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'row': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'burials.burial': {
            'Meta': {'object_name': 'Burial'},
            'account_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'agent_director': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'annulated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'applied_burials'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['persons.AlivePerson']"}),
            'applicant_organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'loru_created'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['users.Org']"}),
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Area']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'burial_container': ('django.db.models.fields.CharField', [], {'default': "'container_coffin'", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'burial_type': ('django.db.models.fields.CharField', [], {'default': "'common'", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'changed_requests'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['auth.User']"}),
            'deadman': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.DeadPerson']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'desired_graves_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'dover': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Dover']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'fact_date': ('pd.models.UnclearDateModelField', [], {'null': 'True', 'blank': 'True'}),
            u'fact_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'fact_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flag_no_applicant_doc_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'grave': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Grave']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'grave_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loru': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'loru_agent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'agent_burials'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['users.Profile']"}),
            'loru_agent_director': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'loru_dover': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'dover_burials'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['users.Dover']"}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Place']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'place_length': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'place_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'place_width': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'plan_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'plan_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'responsible': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'responsible_burials'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['persons.AlivePerson']"}),
            'row': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'source_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'draft'", 'max_length': '255'}),
            'ugh': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ugh_created'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': "orm['users.Org']"})
        },
        'burials.grave': {
            'Meta': {'ordering': "['grave_number']", 'unique_together': "(('place', 'grave_number'),)", 'object_name': 'Grave'},
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'grave_number': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_military': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wrong_fio': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'lng': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Place']"})
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
            'addr_str': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
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
            'login_phone': ('django.db.models.fields.DecimalField', [], {'db_index': 'True', 'null': 'True', 'max_digits': '15', 'decimal_places': '0', 'blank': 'True'}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'persons.baseperson': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'BasePerson'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'birth_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'birth_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'persons.customperson': {
            'Meta': {'ordering': "('last_name', 'first_name', 'middle_name')", 'object_name': 'CustomPerson'},
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'birth_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'birth_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'customplace': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.CustomPlace']", 'null': 'True', 'blank': 'True'}),
            'death_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'death_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'death_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_dead': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'memory_text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.BasePerson']", 'unique': 'True', 'null': 'True'})
        },
        'persons.customplace': {
            'Meta': {'unique_together': "(('user', 'place'),)", 'object_name': 'CustomPlace'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Place']", 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'persons.deadperson': {
            'Meta': {'ordering': "['last_name', 'first_name', 'middle_name']", 'object_name': 'DeadPerson', '_ormbases': ['persons.BasePerson']},
            'baseperson_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.BasePerson']", 'unique': 'True', 'primary_key': 'True'}),
            'death_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'death_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'death_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'persons.deathcertificate': {
            'Meta': {'object_name': 'DeathCertificate'},
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.DeadPerson']", 'unique': 'True'}),
            'release_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            's_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'series': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zags': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True', 'blank': 'True'})
        },
        'persons.deathcertificatescan': {
            'Meta': {'object_name': 'DeathCertificateScan'},
            'bfile': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '96', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deathcertificate': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.DeathCertificate']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'persons.documentsource': {
            'Meta': {'object_name': 'DocumentSource'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'persons.iddocumenttype': {
            'Meta': {'ordering': "('name',)", 'object_name': 'IDDocumentType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'persons.memorygallery': {
            'Meta': {'object_name': 'MemoryGallery'},
            'bfile': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '96', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'customperson': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.CustomPerson']"}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event_date': ('pd.models.UnclearDateModelField', [], {'null': 'True'}),
            u'event_date_no_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'event_date_no_month': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'persons.personid': {
            'Meta': {'object_name': 'PersonID'},
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.IDDocumentType']", 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['persons.BasePerson']", 'unique': 'True'}),
            'series': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.DocumentSource']", 'null': 'True', 'blank': 'True'})
        },
        'persons.phone': {
            'Meta': {'object_name': 'Phone'},
            'ct': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'obj_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'phonetype': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'})
        },
        'users.org': {
            'Meta': {'object_name': 'Org'},
            'ability': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['users.OrgAbility']", 'symmetrical': 'False'}),
            'basis': ('django.db.models.fields.CharField', [], {'default': "'charter'", 'max_length': '255'}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.Currency']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'director': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inn': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'is_wholesale_with_vat': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'kpp': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'max_graves_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'numbers_algo': ('django.db.models.fields.CharField', [], {'default': "'empty'", 'max_length': '255'}),
            'off_address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True', 'blank': 'True'}),
            'ogrn': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'opf_order': ('django.db.models.fields.CharField', [], {'default': "'org'", 'max_length': '255'}),
            'opf_order_customer_mandatory': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'phones': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'plan_date_days_before': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'site': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'populate_from': "'name'", 'unique_with': '()'}),
            'sms_phone': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '15', 'decimal_places': '0', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'worktime': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        'users.orgability': {
            'Meta': {'object_name': 'OrgAbility'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
        'users.profile': {
            'Meta': {'ordering': "('user_last_name', 'user_first_name', 'user_middle_name')", 'object_name': 'Profile'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Area']", 'null': 'True', 'blank': 'True'}),
            'cemetery': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['burials.Cemetery']", 'null': 'True', 'blank': 'True'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_agent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lat': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '30', 'decimal_places': '27', 'blank': 'True'}),
            'lng': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '30', 'decimal_places': '27', 'blank': 'True'}),
            'org': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True'}),
            'user_first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user_last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user_middle_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
    }

    complete_apps = ['persons']
    symmetrical = True
