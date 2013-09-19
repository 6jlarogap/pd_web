# -*- coding: utf-8 -*-

import os
import pytils
import datetime

from django.db import models
from django.db.models.loading import get_model
from django.utils.translation import ugettext as _
from south.modelsinspector import add_introspection_rules


class UnclearDate:
    def __init__(self, year, month=None, day=None):
        self.d = datetime.date(year, month or 1, day or 1)
        self.no_day = not day
        self.no_month = not month

    def strftime(self, format):
        if self.no_day:
            format = format.replace('%d.', '')
        if self.no_month:
            format = format.replace('%m.', '')

        if self.d.year < 1900:
            d1 = datetime.date(1900 + self.d.year % 100, self.d.month, self.d.day)
            return d1.strftime(format).replace(str(d1.year), str(self.d.year))
        return self.d.strftime(format)

    def get_datetime(self):
        return self.d

    def __repr__(self):
        return u'<UnclearDate: %s>' % self.strftime('%d.%m.%Y')

    def __unicode__(self):
        return self.strftime('%d.%m.%Y')

    @property
    def month(self):
        return self.d.month

    @property
    def year(self):
        return self.d.year

    @property
    def day(self):
        return self.d.day

class UnclearDateCreator(object):
    # http://blog.elsdoerfer.name/2008/01/08/fuzzydates-or-one-django-model-field-multiple-database-columns/

    def __init__(self, field):
        self.field = field
        self.no_day_name = u'%s_no_day' % self.field.name
        self.no_month_name = u'%s_no_month' % self.field.name

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')

        date = obj.__dict__[self.field.name]
        if date is None:
            return None
        else:
            y = date.year
            if getattr(obj, self.no_month_name):
                m = None
            else:
                m = date.month
            if getattr(obj, self.no_day_name):
                d = None
            else:
                d = date.day
            return UnclearDate(y, m, d)

    def __set__(self, obj, value):
        if isinstance(value, UnclearDate):
            obj.__dict__[self.field.name] = value.d
            setattr(obj, self.no_month_name, value.no_month)
            setattr(obj, self.no_day_name, value.no_day)
        else:
            obj.__dict__[self.field.name] = self.field.to_python(value)

class UnclearDateModelField(models.DateField):
    # http://blog.elsdoerfer.name/2008/01/08/fuzzydates-or-one-django-model-field-multiple-database-columns/

    def contribute_to_class(self, cls, name):
        no_month_field = models.BooleanField(editable=False, default=False)
        no_day_field = models.BooleanField(editable=False, default=False)
        no_month_field.creation_counter = self.creation_counter
        no_day_field.creation_counter = self.creation_counter
        cls.add_to_class(u'%s_no_month' % name, no_month_field)
        cls.add_to_class(u'%s_no_day' % name, no_day_field)

        super(UnclearDateModelField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, UnclearDateCreator(self))

    def get_db_prep_save(self, value, **kwargs):
        if isinstance(value, UnclearDate):
            value = value.d
        return super(UnclearDateModelField, self).get_db_prep_save(value, **kwargs)

    def get_db_prep_lookup(self, lookup_type, value, **kwargs):
        if lookup_type == 'exact':
            return [self.get_db_prep_save(value, **kwargs)]
        elif lookup_type == 'in':
            return [self.get_db_prep_save(v, **kwargs) for v in value]
        else:
            return super(UnclearDateModelField, self).get_db_prep_lookup(lookup_type, value, **kwargs)

    def to_python(self, value):
        if isinstance(value, UnclearDate):
            return value

        return super(UnclearDateModelField, self).to_python(value)

    def formfield(self, **kwargs):
        from pd.forms import UnclearDateField, UnclearSelectDateWidget
        defaults = {
            'form_class': UnclearDateField,
            'widget': UnclearSelectDateWidget,
            }
        kwargs.update(defaults)
        return super(UnclearDateModelField, self).formfield(**kwargs)
    
    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)        
        return value.strftime('%Y-%m-%d')     

class BaseModel(models.Model):
    """
    Базовый класс для многих моделей
    """
    class Meta:
        abstract = True
        
    dt_created = models.DateTimeField(_(u"Дата/время создания"), auto_now_add=True)
    dt_modified = models.DateTimeField(_(u"Дата/время модификации"), auto_now=True)

def files_upload_to(instance, filename):
    instance.original_name = filename
    fname = u'.'.join(map(pytils.translit.slugify, filename.rsplit('.', 1)))
    today = datetime.date.today()
    today_dir = "{0:d}/{1:02d}/{2:02d}".format(today.year, today.month, today.day)
    if isinstance(instance, get_model('burials', 'BurialFiles')):
        return os.path.join('bfiles', str(instance.burial.pk), fname)
    elif isinstance(instance, get_model('burials', 'PlaceStatusFiles')):
        return os.path.join('place-status-files', today_dir, fname)
    elif isinstance(instance, get_model('persons', 'DeathCertificateScan')):
        return os.path.join('death-certificates', today_dir, fname)
    elif isinstance(instance, get_model('burials', 'GravePhoto')):
        return os.path.join('grave-photos', today_dir, fname)
    else:
        return os.path.join('files', fname)

class Files(models.Model):
    """
    Базовый класс для файлов
    """
    class Meta:
        abstract = True
        
    bfile = models.FileField(u"Файл", upload_to=files_upload_to, blank=True)
    comment = models.CharField(u"Описание", max_length=96, blank=True)
    original_name = models.CharField(max_length=255, editable=False)
    creator = models.ForeignKey('auth.User', verbose_name=_(u"Создатель"), editable=False, null=True,
                                on_delete=models.PROTECT)
    date_of_creation = models.DateTimeField(auto_now_add=True)

    def delete_from_media(self):
        if self.bfile != "":
            if os.path.exists(self.bfile.path):
                os.remove(self.bfile.path)

    def delete(self):
        self.delete_from_media()
        self.bfile = ""
        super(Files, self).delete()

class Photo(Files):
    """
    Базовый класс для фото
    """
    class Meta:
        abstract = True

    lat = models.FloatField(_(u"Широта"), blank=True, null=True)
    lng = models.FloatField(_(u"Долгота"), blank=True, null=True)
    
add_introspection_rules([], ['^pd\.models\.UnclearDateModelField'])
