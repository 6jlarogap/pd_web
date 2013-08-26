# coding=utf-8
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

class Log(models.Model):
    """
    Журнал различных событий
    """
    user = models.ForeignKey('auth.User', null=True, editable=False, verbose_name=_(u"Пользователь"))
    ct = models.ForeignKey('contenttypes.ContentType', null=True, editable=False, verbose_name=_(u"Тип"))
    obj_id = models.PositiveIntegerField(null=True, editable=False, verbose_name=_(u"ID объекта"), db_index=True)
    obj = generic.GenericForeignKey(ct_field='ct', fk_field='obj_id')
    dt = models.DateTimeField(auto_now_add=True, verbose_name=_(u"Время"))
    msg = models.TextField(editable=False, verbose_name=_(u"Описание"))
    code = models.CharField(max_length=255, default='', editable=False, verbose_name=_(u"Спец. код"))
    
    def ct_display(self):
        """
        Показываем в таблице действий пользователей: что за объект + ссылка
        """
        model = self.ct.model_class()._meta.object_name
        obj_id = self.obj_id if self.obj_id else ''
        if model == 'Burial':
            ref = reverse('view_burial', args=[obj_id]) if obj_id else ''
            result = _(u"Захоронение <a href='%s'>%s</a>") % (ref, obj_id, )
        else:
            obj = model
            ref = obj_id if obj_id else ''
            result = u"%s %s" % (obj, ref,)
        return result

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