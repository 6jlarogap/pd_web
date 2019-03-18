# coding=utf-8

import datetime

from rest_framework import serializers
from rest_framework.fields import DateTimeField
from django.conf import settings

from pd.models import UnclearDate
from pd.utils import local2utc, utc2local

class HyperlinkedFileField(serializers.FileField):
    """
    Show full URL of of a file field
    """
    def to_representation(self, value):
        request = self.context.get('request', None)
        return request.build_absolute_uri(value.url) if request and value else ''

class UnclearDateFieldSerializer(serializers.Field):
    date_format = 'd.m.y'

    def to_representation(self, obj):
        try:
            return obj.str_safe(format=self.date_format)
        except:
            return obj

    def to_internal_value(self, value):
        if UnclearDate.check_safe_str(value, check_today=False, format=self.date_format):
            # Неверная дата
            return None
        return UnclearDate.from_str_safe(value, self.date_format)


class UnclearDateFieldSafeSerializer(UnclearDateFieldSerializer):
    date_format = ''

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

    def __init__(self, *args, **kwargs):
        f1 = self.UTC_FORMAT
        f2 = self.UTC_FORMAT[:-1]
        f3 = self.UTC_FORMAT[:-4]
        f4 = self.UTC_FORMAT[:-3]
        super(DateTimeUtcField, self).__init__(
            input_formats = [f1, f2, f3, f4], format=self.UTC_FORMAT, *args, **kwargs
        )

    def to_internal_value(self, value):
        # value: DateTime или строка в UTC
        # результат: dt in localtime, например, для записи в базу
        if value is None:
            return value
        dt = super(DateTimeUtcField, self).to_internal_value(value)
        dt = utc2local(dt)
        return dt

    def to_representation(self, value):
        # value: DateTime
        # результат: Строка
        if isinstance(value, datetime.datetime):
            value = local2utc(value)
        elif isinstance(value, str):
            return value
        return super(DateTimeUtcField, self).to_representation(value)
