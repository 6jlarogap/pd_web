# coding=utf-8

from django.contrib.auth.models import Group, Permission
from django.utils.translation import ugettext_lazy as _
from django.db.models.loading import get_model

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
    msg = serializers.SerializerMethodField('msg_func')

    class Meta:
        model = Log
        fields = ('msg', 'dt', 'user', 'obj')

    def msg_func(self, obj):
        result = obj.log_msg_display()
        if obj.obj_id:
            model_name = obj.ct.model_class()._meta.object_name
            app_name = obj.ct.model_class()._meta.app_label
            Model = get_model(app_name, model_name)
            if model_name == "Grave":
                try:
                    grave = Model.objects.get(pk=obj.obj_id)
                    result = _(u"%(msg)s (могила № %(grave_number)s)") % dict(
                        msg=result,
                        grave_number=grave.grave_number,
                    )
                except Model.DoesNotExist:
                    pass
        return result
