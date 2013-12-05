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
    
    class Meta:
        verbose_name = _(u"Событие")
        verbose_name_plural = _(u"Журнал событий")
        ordering = ['-dt']

    
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
    user = request and request.user.is_authenticated() and request.user or None
    Log.objects.create(
        user=user,
        ct=obj and ContentType.objects.get_for_model(obj) or None,
        obj_id=obj and obj.pk or None,
        msg=msg,
        code=code or '',
    )


LOG_STOP_FIELDS = ['pk', 'dt_created', 'dt_updated']

def log_object(request, obj=None, old=None, new=None, reason=None, code=None):
    msg = []
    if old.__class__ != new.__class__:
        return False
    
    if reason:
        msg.append(reason)
    
    if old is None:
        msg.append(_(u'Создан "%s"' % new))
    elif new is None:
        msg.append(_(u'Удален "%s"' % old))
    else:
        for field in new._meta.fields:
            if field.name not in LOG_STOP_FIELDS and getattr(old,field.name) != getattr(new,field.name):
                old_val = getattr(old,field.name)
                new_val = getattr(new,field.name)
                if isinstance(old_val, bool):
                     old_val = old_val and u'Да' or u'Нет'
                     new_val = old_val and u'Да' or u'Нет'
                old_val = old_val is None and u'<пусто>' or unicode(old_val) #.__unicode__()
                new_val = new_val is None and u'<пусто>' or unicode(new_val)
                if old_val=="None":
                    msg.append(_(u"'%s': добавлено '%s'") % (field.verbose_name, new_val))
                elif new_val=="None":
                    msg.append(_(u"'%s': удалено '%s'") % (field.verbose_name, old_val))
                else:
                    msg.append(_(u"'%s': '%s' -> '%s'") % (field.verbose_name, old_val, new_val))

    user = request and request.user.is_authenticated() and request.user or None
    Log.objects.create(
        user=user,
        ct=obj and ContentType.objects.get_for_model(obj) or None,
        obj_id=obj and obj.pk or None,
        msg = "<br/>".join(msg),
        code=code or '',
    )


class LoginLog(models.Model):
    """
    Журнал входа пользователей в систему
    """
    dt = models.DateTimeField(auto_now_add=True, verbose_name=_(u"Время"))
    user = models.ForeignKey('auth.User', verbose_name=_(u"Пользователь"))
    org = models.ForeignKey('users.Org', verbose_name=_(u"Организация"), null=True)
    ip = models.GenericIPAddressField(unpack_ipv4=True, null=True)

    @classmethod
    def write(cls, request):
        user = request.user
        if user:
            # Пользователь может не иметь еще профиля при первом входе в систему
            org = user.profile and user.profile.org or None
            rec = cls(user=user, org = org, ip=request.META.get('REMOTE_ADDR'))
            rec.save()
