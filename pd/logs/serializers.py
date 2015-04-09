# coding=utf-8

from django.contrib.auth.models import Group, Permission
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.fields import Field

from logs.models import Log
from django.contrib.auth.models import User

from users.models import get_profile, is_cabinet_user

class ObjField(serializers.Field):
    def to_native(self, obj):
        return obj.__unicode__()

class UserField(serializers.Field):
    def to_native(self, user):
        profile = get_profile(user)
        if profile:
            s = u"%s / %s" % (
                 profile.last_name_initials(),
                 _(u"Ответственный за место") if is_cabinet_user(user) else profile.org.name,
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