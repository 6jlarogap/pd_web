# coding=utf-8
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

class Log(models.Model):
    """
    Журнал различных событий
    """
    user = models.ForeignKey('auth.User', null=True, editable=False, verbose_name=_(u"Пользователь"))
    ct = models.ForeignKey('contenttypes.ContentType', null=True, editable=False, verbose_name=_(u"Тип"))
    obj_id = models.PositiveIntegerField(null=True, editable=False, verbose_name=_(u"ID объекта"))
    obj = generic.GenericForeignKey(ct_field='ct', fk_field='obj_id')
    dt = models.DateTimeField(auto_now_add=True, verbose_name=_(u"Время"))
    msg = models.CharField(max_length=255, editable=False, verbose_name=_(u"Описание"))
    code = models.CharField(max_length=255, default='', editable=False, verbose_name=_(u"Спец. код"))

def write_log(request, obj=None, msg='', reason=None, code=None):
    if reason:
        if msg:
            msg = u'%s: %s' % (msg, reason)
        else:
            msg = reason
    user = request.user.is_authenticated() and request.user or None
    Log.objects.create(
        user=user,
        ct=obj and ContentType.objects.get_for_model(obj) or None,
        obj_id=obj and obj.pk or None,
        msg=msg,
        code=code or '',
    )