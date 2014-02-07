# coding=utf-8

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field



from logs.models import Log
from django.contrib.auth.models import User

class ObjField(serializers.Field):
    def to_native(self, obj):
        return obj.__unicode__()

class UserField(serializers.Field):
    def to_native(self, obj):
        if obj and obj.profile:
            s = u"%s / %s" % (
                 obj.profile.last_name_initials(),
                 obj.profile.org.name
                )
        else:
            s = '-'
        return s


class LogSerializer(serializers.ModelSerializer):
    obj = ObjField()
    user = UserField()   
    dt = serializers.DateTimeField(format="%d.%m.%Y %H:%M")
    class Meta:
        model = Log
        fields = ('msg', 'dt', 'user', 'obj')