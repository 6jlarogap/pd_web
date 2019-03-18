# coding=utf-8

from django.contrib.auth.models import Group, Permission
from django.utils.translation import ugettext_lazy as _
from django.apps import apps
get_model = apps.get_model
from django.urls import reverse

from rest_framework import serializers

from logs.models import Log
from django.contrib.auth.models import User

from users.models import get_profile, is_cabinet_user

class ObjField(serializers.Field):
    def to_representation(self, obj):
        return str(obj)

class UserField(serializers.Field):
    def to_representation(self, user):
        profile = get_profile(user)
        if profile:
            s = "%s / %s" % (
                 profile.last_name_initials(),
                 _("Ответственный за место") if is_cabinet_user(user) else profile.org.name,
                )
        else:
            s = '-'
        return s


class PlaceLogSerializer(serializers.ModelSerializer):
    obj = ObjField()
    user = UserField()   
    dt = serializers.DateTimeField(format="%d.%m.%Y %H:%M")
    msg = serializers.ReadOnlyField(source='log_msg_display')
    obj_str = serializers.SerializerMethodField('obj_str_func')

    class Meta:
        model = Log
        fields = ('msg', 'dt', 'user', 'obj', 'obj_str',)

    def obj_str_func(self, obj):
        result = _("Место")
        if obj.obj_id:
            model_name = obj.ct.model_class()._meta.object_name
            app_name = obj.ct.model_class()._meta.app_label
            Model = get_model(app_name, model_name)
            if model_name == "Grave":
                try:
                    grave = Model.objects.get(pk=obj.obj_id)
                    result = _("Могила № %s") % grave.grave_number
                except Model.DoesNotExist:
                    result = _("Могила")
            elif model_name == "Burial":
                try:
                    burial = Model.objects.get(pk=obj.obj_id)
                    if burial.is_bio():
                        deadman_name=_("Биоотходы")
                    else:
                        deadman_name = burial.deadman and burial.deadman.full_name() or _("Неизвестный")
                    result = _('Захоронение</br /><a href="%(href)s" target="_blank">'
                               '%(deadman_name)s</a>') % dict(
                                    href=reverse('view_burial', args=[burial.pk]),
                                    deadman_name=deadman_name,
                    )
                    if not burial.is_closed():
                        result += "%s %s" % ("<br />", _("Не закрыто"),)
                except Model.DoesNotExist:
                    result = _("Захоронение")
            elif model_name == "AlivePerson":
                result = _("Ответственный")
        return result
