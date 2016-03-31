# coding=utf-8
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model

class LogOperation(object):

    GRAVE_FREE_SET =                1
    GRAVE_FREE_RESET =              2
    PLACE_PHOTO_PROCESSED =         3
    BURIAL_PHOTO_PROCESSED =        4
    PLACE_PHOTO_REJECT =            5
    PLACE_CREATED_MOBILE =          6
    INVITE_CUSTOMER_TO_TEMPLE =     7
    LORU_MAKES_PLACE_PHOTO =        8
    BURIAL_TO_GRAVE_MOBILE =        9
    CLOSED_BURIAL_TRANSFERRED =    10
    CLOSED_BURIAL_ARCHIVE =        11
    CLOSED_BURIAL_FULL =           12
    CLOSED_BURIAL_UGH =            13
    PHOTO_TO_PLACE_MOBILE =        14

    Operation = [
        _(u'Установка признака "Занято" для могилы'),                                       #  1
        _(u'Снятие признака "Занято" для могилы'),                                          #  2
        _(u'Фотографии места обработаны'),                                                  #  3
        _(u'Захоронение добавлено по фото'),                                                #  4
        _(u'Брак фото места'),                                                              #  5
        _(u'Место создано через мобильное приложение'),                                     #  6
        _(u'Приглашение в ХРАМ, от ЛОРУ'),                                                  #  7
        _(u'Фотографирование пользовательского места, ЛОРУ'),                               #  8
        _(u'Захоронение закрыто и прикреплено к могиле в мобильном приложении'),            #  9
        _(u'Импорт захоронения'),                                                           # 10
        _(u'Архивное захоронение закрыто'),                                                 # 11
        _(u'Электронное захоронение закрыто'),                                              # 12
        _(u'Ручное захоронение закрыто'),                                                   # 13
        _(u'Прикреплено фото к месту из мобильного приложения'),                            # 14
    ]

class Log(models.Model):
    """
    Журнал различных событий
    """
    user = models.ForeignKey('auth.User', null=True, editable=False, verbose_name=_(u"Пользователь"))
    ct = models.ForeignKey('contenttypes.ContentType', null=True, editable=False, verbose_name=_(u"Тип"))
    obj_id = models.PositiveIntegerField(null=True, editable=False, verbose_name=_(u"ID объекта"), db_index=True)
    obj = generic.GenericForeignKey(ct_field='ct', fk_field='obj_id')
    dt = models.DateTimeField(auto_now_add=True, verbose_name=_(u"Время"), db_index=True)
    msg = models.TextField(editable=False, verbose_name=_(u"Описание"))
    code = models.CharField(max_length=255, default='', editable=False, verbose_name=_(u"Спец. код"))
    operation = models.PositiveIntegerField(null=True, editable=False, verbose_name=_(u"Код операции"), db_index=True)
    
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
            result = _(u"Захоронение <a href='%(ref)s'>%(obj_id)s</a>") % dict(
                ref=ref, obj_id=obj_id,
            )
        elif model_name in ('Place', 'Cemetery'):
            try:
                obj = Model.objects.get(pk=obj_id)
                href = "<a href='%(url)s'>%(name)s</a>" % dict(
                    url=obj.url(),
                    name=obj.place if model_name == 'Place' else obj.name
                )
            except Model.DoesNotExist:
                href = _(u"не найдено")
            result = _(u"%s %s") % (
                Model._meta.verbose_name.title(),
                href,
            )
        elif model_name == 'Grave':
            try:
                grave = Model.objects.get(pk=obj_id)
                place = grave.place
                href = "<a href='%(url)s'>%(name)s</a>" % dict(
                    url=place.url(),
                    name=place.place,
                )
            except Model.DoesNotExist:
                href = _(u"не найдена")
            result = _(u"Могила  № %(grave_number)s, место %(place_url)s") % dict(
                grave_number=grave.grave_number,
                place_url=href,
            )
        elif model_name == 'Order':
            ref = reverse('order_edit', args=[obj_id])
            try:
                loru_number = Model.objects.get(pk=obj_id).loru_number
            except Model.DoesNotExist:
                loru_number = ''
            result = _(u"Заказ <a href='%(ref)s'>%(loru_number)s</a>") % dict(
                ref=ref, loru_number=loru_number,
            )
        elif model_name == 'Org':
            try:
               obj = Model.objects.get(pk=obj_id)
               result = "<a href='%s'>Организация</a>" % reverse('edit_org', args=[obj_id])
            except Model.DoesNotExist:
               result = _(u"Организация")
        elif model_name == 'User':
            try:
                result = _(u"Пользователь")
                user = Model.objects.get(pk=obj_id)
                try:
                    profile = user.profile
                    href = "<a href='%(url)s'>%(name)s</a>" % dict(
                                url=reverse('edit_profile', args=[profile.pk]),
                                name=user.username,
                    )
                    result = _(u"Пользователь %s") % href
                except (AttributeError, get_model('users', 'Profile').DoesNotExist):
                    pass
            except Model.DoesNotExist:
                pass
        elif model_name == 'Profile':
            try:
               obj = Model.objects.get(pk=obj_id)
               href = "<a href='%(url)s'>%(name)s</a>" % dict(
                    url=reverse('edit_profile', args=[obj_id]),
                    name=obj.user.username,
                )
            except Model.DoesNotExist:
                href = _(u"не найден")
            result = _(u"Пользователь %s") % href
        elif model_name == 'Product':
            product = ref = ""
            try:
                product = Model.objects.get(pk=obj_id).name
            except Model.DoesNotExist:
                pass
            if product:
                ref = ": <a href='%s'>%s</a>" % (
                    reverse('manage_products_edit', args=[obj_id]),
                    product,
                )
            result = _(u"Товар/услуга%s") % ref
        else:
            result = u"%s %s" % (model_name, obj_id,)
        return result

    def log_msg_display(self):
        if self.operation is not None:
            operation_title = LogOperation.Operation[self.operation-1]
            if self.msg:
                result = u"%s.\n%s" % (operation_title, self.msg,)
            else:
                result = operation_title
        else:
            result = self.msg
        return result

def write_log(request, obj=None, msg='', reason=None, code=None, operation=None):
    if reason:
        if msg:
            msg = u'%s: %s' % (msg, reason)
        else:
            msg = reason
    user = request and request.user.is_authenticated() and request.user or None
    return Log.objects.create(
        user=user,
        ct=obj and ContentType.objects.get_for_model(obj) or None,
        obj_id=obj and obj.pk or None,
        msg=msg,
        code=code or '',
        operation=operation,
    )


def compare_obj(verbose_name, old_val, new_val):
    if isinstance(old_val, bool) or isinstance(new_val, bool):
         if old_val:
             old_val=_(u'Да')
         else:
             old_val=_(u'Нет')
         if new_val:
             new_val=_(u'Да')
         else:
             new_val=_(u'Нет')
    old_val = old_val is None and u'<пусто>' or unicode(old_val) #.__unicode__()
    new_val = new_val is None and u'<пусто>' or unicode(new_val)
    if old_val=="None":
        res = _(u"'%(verbose_name)s': добавлено '%(new_val)s'") % dict(
            verbose_name=verbose_name, new_val=new_val
        )
    elif new_val=="None":
        res = _(u"'%(verbose_name)s': удалено '%(old_val)s'") % dict(
            verbose_name=verbose_name, old_val=old_val
        )
    elif old_val != new_val:
        res = _(u"'%(verbose_name)s': '%(old_val)s' -> '%(new_val)s'") % dict(
            verbose_name=verbose_name, old_val=old_val, new_val=new_val
        )
    else: 
        return
    return res


LOG_STOP_FIELDS = ['pk', 'obj', 'ct', 'obj_id', 'dt_created', 'dt_modified', 'dt_updated']

def log_object(request, obj=None, old=None, new=None, reason=None, footer=None, \
               code=None, create_text=None, delete_text=None, obj_stop_fields=None, new_msg = []):
    msg = []
    if old is not None and old.__class__ != new.__class__:
        return False
    if reason:
        msg.append(reason)
    
    if old is None:
        msg.append(create_text or _(u'Создан "%s"') % new.__unicode__())
    elif new is None:
        msg.append(delete_text or _(u'Удален "%s"') % old.__unicode__())
    else:
        for field in new._meta.fields:
            if field.name not in LOG_STOP_FIELDS and getattr(old,field.name) != getattr(new,field.name) \
                and (obj_stop_fields is None or (obj_stop_fields is not None and  field.name not in obj_stop_fields)):
                if hasattr(field, 'choices') and getattr(field, 'choices'):
                    old_val = old._get_FIELD_display(field)
                    new_val = new._get_FIELD_display(field)
                else:
                    old_val = getattr(old,field.name)
                    new_val = getattr(new,field.name)
                res = compare_obj(field.verbose_name, old_val, new_val)
                if res:
                    msg.append(res)

    user = request and request.user.is_authenticated() and request.user or None
    if footer:
        msg.append(footer)

    log = Log.objects.create(
        user=user,
        ct=obj and ContentType.objects.get_for_model(obj) or None,
        obj_id=obj and obj.pk or None,
        msg = "\n".join(msg + new_msg),
        code=code or '',
    )
    del msg


def prepare_m2m_log(verbose_name="", old_set = [], new_set=[]):
    """
    """
    old_arr = {}
    new_arr = {}
    msg = []
    
    for i in new_set:
        new_arr[i.id] = i
    new_arr_keys = new_arr.keys()
    
    for i in old_set:
        old_arr[i.id] = i
        if i.id not in new_arr_keys:
            res  = compare_obj(verbose_name, i, None)
            if res:
                msg.append(res)
        
    old_arr_keys = old_arr.keys()
    
    for i in new_set:
        if i.id not in old_arr_keys:
            res = compare_obj(verbose_name, None, i)
            if res:
                msg.append(res)
        else:
            res = compare_obj(verbose_name, old_arr[i.id], i)
            if res:
                msg.append(res)

    return msg


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
            Profile = get_model('users', 'Profile')
            try:
                org = user.profile.org
            except Profile.DoesNotExist:
                org = None
            rec = cls(user=user, org = org, ip=request.META.get('REMOTE_ADDR'))
            rec.save()
