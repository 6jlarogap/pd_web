from rest_framework import serializers
from django.conf import settings


class UnclearDateFieldSerializer(serializers.Field):
    """
    Field to frontend conversion
    --
    next step: serializers.WritebleField
    """
    def to_native(self, obj):
        try:
            return obj.strftime('%Y.%m.%d')
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
