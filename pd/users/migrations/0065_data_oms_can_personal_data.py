# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."
        
        # Всем существующим активным ОМС добавляем возможность ввода персональных данных
        # Фикстура в OrgAbility с именем personal-data может не существовать до этой миграции,
        # посему создаем:
        pd_ability, created_ = orm['users.OrgAbility'].objects.get_or_create(
            name='personal-data',
            defaults=dict(title=u"Перcональные данные в захоронениях"),
        )
        for ugh in orm['users.Org'].objects.filter(type='ugh'):
            if ugh.profile_set.filter(user__is_active=True).exists():
                ugh.ability.add(pd_ability)

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
        'users.bankaccount': {
            'Meta': {'object_name': 'BankAccount'},
            'bankname': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'bik': ('django.db.models.fields.CharField', [], {'max_length': '9'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ks': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'ls': ('django.db.models.fields.CharField', [], {'max_length': '11', 'null': 'True', 'blank': 'True'}),
            'off_address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']"}),
            'rs': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'users.bankaccountregister': {
            'Meta': {'object_name': 'BankAccountRegister'},
            'bankname': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'bik': ('django.db.models.fields.CharField', [], {'max_length': '9'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ks': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'ls': ('django.db.models.fields.CharField', [], {'max_length': '11', 'null': 'True', 'blank': 'True'}),
            'off_address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True'}),
            'registerprofile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.RegisterProfile']"}),
            'rs': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'users.customerprofile': {
            'Meta': {'unique_together': "(('login_phone',),)", 'object_name': 'CustomerProfile'},
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login_phone': ('django.db.models.fields.DecimalField', [], {'db_index': 'True', 'null': 'True', 'max_digits': '15', 'decimal_places': '0', 'blank': 'True'}),
            'tc_confirmed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True'}),
            'user_first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user_last_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user_middle_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
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
        'users.favoritesupplier': {
            'Meta': {'unique_together': "(('loru', 'supplier'),)", 'object_name': 'FavoriteSupplier'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loru': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'favorite_loru'", 'on_delete': 'models.PROTECT', 'to': "orm['users.Org']"}),
            'supplier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'favorite_supplier_list'", 'on_delete': 'models.PROTECT', 'to': "orm['users.Org']"})
        },
        'users.oauth': {
            'Meta': {'unique_together': "(('provider', 'uid'),)", 'object_name': 'Oauth'},
            'display_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'uid': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
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
        'users.orgcertificate': {
            'Meta': {'object_name': 'OrgCertificate'},
            'bfile': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '96', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'org': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['users.Org']", 'unique': 'True'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'users.orgcontract': {
            'Meta': {'object_name': 'OrgContract'},
            'bfile': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '96', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'org': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['users.Org']", 'unique': 'True'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'users.orgwebpay': {
            'Meta': {'object_name': 'OrgWebPay'},
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'org': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['users.Org']", 'unique': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'wsb_currency_id': ('django.db.models.fields.CharField', [], {'default': "'BYR'", 'max_length': '255'}),
            'wsb_store': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'wsb_storeid': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'wsb_test': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'wsb_version': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
        'users.profileloru': {
            'Meta': {'object_name': 'ProfileLORU'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loru': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ugh_list'", 'to': "orm['users.Org']"}),
            'ugh': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'loru_list'", 'to': "orm['users.Org']"})
        },
        'users.registerprofile': {
            'Meta': {'object_name': 'RegisterProfile'},
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'org_address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True'}),
            'org_basis': ('django.db.models.fields.CharField', [], {'default': "'charter'", 'max_length': '255'}),
            'org_currency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.Currency']"}),
            'org_director': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'org_fax': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'org_full_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'org_inn': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'org_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'org_ogrn': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'org_phones': ('django.db.models.fields.TextField', [], {}),
            'org_type': ('django.db.models.fields.CharField', [], {'default': "'ugh'", 'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user_activation_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'user_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'user_first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user_last_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user_middle_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'user_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'})
        },
        'users.registerprofilecontract': {
            'Meta': {'object_name': 'RegisterProfileContract'},
            'bfile': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '96', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'registerprofile': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['users.RegisterProfile']", 'unique': 'True'})
        },
        'users.registerprofilescan': {
            'Meta': {'object_name': 'RegisterProfileScan'},
            'bfile': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '96', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'registerprofile': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['users.RegisterProfile']", 'unique': 'True'})
        },
        'users.store': {
            'Meta': {'object_name': 'Store'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loru': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'on_delete': 'models.PROTECT'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'})
        },
        'users.userphoto': {
            'Meta': {'object_name': 'UserPhoto'},
            'bfile': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '96', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'date_of_creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'user_photo_list'", 'unique': 'True', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['users']
    symmetrical = True
