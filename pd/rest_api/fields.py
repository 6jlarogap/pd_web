# coding=utf-8

import datetime

from rest_framework import serializers
from rest_framework.fields import DateTimeField
from django.conf import settings

from pd.models import UnclearDate
from pd.utils import local2utc, utc2local

class HyperlinkedFileField(serializers.FileField):
    """
    Show full URL of o file field
    """
    def to_representation(self, value):
        request = self.context.get('request', None)
        return request.build_absolute_uri(value.url) if request and value else ''

class UnclearDateFieldSerializer(serializers.Field):
    """
    Field to frontend conversion
    --
    next step: serializers.WritebleField
    """
    def to_representation(self, obj):
        try:
            return obj.str_safe(format='d.m.y')
        except:
            return obj


class UnclearDateFieldSafeSerializer(serializers.Field):
    def to_representation(self, obj):
        if obj is not None:
            return obj.str_safe()
        else:
            return obj


class ThumbnailFieldSerializer(serializers.Field):
    """
    Field to frontend conversion
    """
    def to_representation(self, obj, width=None, height=None, method=None):
        if obj:
            try:
                return '%s%s/%dx%d~%s~12.jpg'.format(settings.THUMBNAILS_STORAGE_BASE_PATH, 
                                                     obj.url, width, height, method)
            except:
                return None

class UnclearDateFieldMixin(object):

    def birth_date(self, instance):
        return instance.birth_date and instance.birth_date.str_safe() or None

    def death_date(self, instance):
        return instance.death_date and instance.death_date.str_safe() or None

    def set_unclear_date(self, s, format=''):
        return UnclearDate.from_str_safe(s, format)

class DateTimeUtcField(DateTimeField):
    """
    DateTime в моделях в локальном времени, а выдается и преобразуется из Utc времени
    """

    UTC_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

    def __init__(self, input_formats=None, format=None, *args, **kwargs):
        if format is None:
            format = DateTimeUtcField.UTC_FORMAT
        if input_formats is None:
            input_formats = (DateTimeUtcField.UTC_FORMAT, )
        super(DateTimeUtcField, self).__init__(input_formats, format, *args, **kwargs)

    def to_internal_value(self, value):
        # value: DateTime или строка в UTC
        # результат: dt in localtime, например, для записи в базу
        dt = super(DateTimeUtcField, self).to_internal_value(value)
        if dt is not None:
            dt = utc2local(dt)
        return dt

    def to_representation(self, value):
        # value: DateTime
        # результат: Строка
        if isinstance(value, datetime.datetime):
            value = local2utc(value)
        elif isinstance(value, basestring):
            return value
        return super(DateTimeUtcField, self).to_representation(value)
