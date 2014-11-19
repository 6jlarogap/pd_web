# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Currency.rounding'
        db.add_column('billing_currency', 'rounding',
                      self.gf('django.db.models.fields.SmallIntegerField')(default=2),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Currency.rounding'
        db.delete_column('billing_currency', 'rounding')


    models = {
        'billing.ad': {
            'Meta': {'object_name': 'Ad'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['billing.Payment']", 'unique': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.Product']"}),
            'rate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.Rate']", 'null': 'True'}),
            'ugh': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']"})
        },
        'billing.commission': {
            'Meta': {'object_name': 'Commission'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['billing.Payment']", 'unique': 'True'}),
            'share': ('django.db.models.fields.FloatField', [], {}),
            'source_ct': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'source_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
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
        'billing.io': {
            'Meta': {'object_name': 'Io'},
            'bank': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['billing.Payment']", 'unique': 'True'}),
            'transaction': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'billing.payment': {
            'Meta': {'object_name': 'Payment'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'comment': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'ct': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'wallet_from': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'payment_from'", 'null': 'True', 'to': "orm['billing.Wallet']"}),
            'wallet_to': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'payment_to'", 'null': 'True', 'to': "orm['billing.Wallet']"})
        },
        'billing.rate': {
            'Meta': {'unique_together': "(('wallet', 'action', 'date_from'),)", 'object_name': 'Rate'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'date_from': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'wallet': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.Wallet']"})
        },
        'billing.wallet': {
            'Meta': {'unique_together': "(('org', 'currency'),)", 'object_name': 'Wallet'},
            'amount': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '20', 'decimal_places': '2'}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.Currency']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'org': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']"})
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
        'orders.product': {
            'Meta': {'ordering': "['name']", 'object_name': 'Product'},
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public_catalog': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_wholesale': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'loru': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']", 'null': 'True'}),
            'measure': ('django.db.models.fields.CharField', [], {'default': "u'\\u0448\\u0442'", 'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'price_wholesale': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'productcategory': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.ProductCategory']", 'on_delete': 'models.PROTECT'}),
            'productgroup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.ProductGroup']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'ptype': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'sku': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'max_length': '255', 'unique': 'True', 'null': 'True', 'populate_from': "'name'", 'unique_with': '()'})
        },
        'orders.productcategory': {
            'Meta': {'ordering': "('name',)", 'object_name': 'ProductCategory'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'orders.productgroup': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('loru', 'productcategory', 'name'),)", 'object_name': 'ProductGroup'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'icon': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loru': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Org']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'productcategory': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.ProductCategory']", 'on_delete': 'models.PROTECT'})
        },
        'users.org': {
            'Meta': {'object_name': 'Org'},
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
        }
    }

    complete_apps = ['billing']