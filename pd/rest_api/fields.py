from rest_framework import serializers
from django.conf import settings

from pd.models import UnclearDate

class HyperlinkedFileField(serializers.FileField):
    """
    Show full URL of o file field
    """
    def to_native(self, value):
        request = self.context.get('request', None)
        return request.build_absolute_uri(value.url) if request and value else ''

class UnclearDateFieldSerializer(serializers.Field):
    """
    Field to frontend conversion
    --
    next step: serializers.WritebleField
    """
    def to_native(self, obj):
        try:
            return obj.strftime('%d.%m.%Y')
        except:
            return obj


class ThumbnailFieldSerializer(serializers.Field):
    """
    Field to frontend conversion
    """
    def to_native(self, obj, width=None, height=None, method=None):
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

    def set_unclear_date(self, s):
        if s:
            return UnclearDate.from_str_safe(s)
        else:
            return None
