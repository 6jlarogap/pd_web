# coding=utf-8
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model

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
    
    def log_object_display(self):
        """
        Показываем в таблице действий пользователей: что за объект + ссылка
        """

        model_name = self.ct.model_class()._meta.object_name
        app_name = self.ct.model_class()._meta.app_label
        # Во избежание перекрестных ссылок между модулями
        # различных приложений, применяющих здешние функции,
        # не импортируем модели, а получаем их так:
        Model = get_model(app_name, model_name)
        obj_id = self.obj_id if self.obj_id else ''
        if model_name == 'Burial':
            ref = reverse('view_burial', args=[obj_id])
            result = _(u"Захоронение <a href='%s'>%s</a>") % (ref, obj_id, )
        elif model_name == 'Order':
            ref = reverse('order_edit', args=[obj_id])
            try:
                loru_number = Model.objects.get(pk=obj_id).loru_number
            except Model.DoesNotExist:
                loru_number = ''
            result = _(u"Заказ <a href='%s'>%s</a>") % (ref, loru_number, )
        elif model_name == 'Cemetery':
            ref = reverse('manage_cemeteries_edit', args=[obj_id])
            try:
                cemetery = Model.objects.get(pk=obj_id).name
            except Model.DoesNotExist:
                cemetery = ''
            result = _(u"Кладбище <a href='%s'>%s</a>") % (ref, cemetery, )
        elif model_name == 'Org':
            result = _(u"Организация")
        elif model_name == 'Profile':
            result = ""
        elif model_name == 'User':
            result = ""
        else:
            result = u"%s %s" % (model_name, obj_id,)
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