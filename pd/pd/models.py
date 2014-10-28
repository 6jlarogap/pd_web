# -*- coding: utf-8 -*-

import os, shutil
import pytils
import datetime
import re

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.db.models.loading import get_model
from django.db.models.deletion import ProtectedError
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from south.modelsinspector import add_introspection_rules
from logs.models import Log

class SafeDeleteMixin(object):
    
    def safe_delete(self, field_name, instance):
        """
        Безопасно удалить что-то из записи таблицы
        
        field       - строка (!) имени поля
        instance    - запись в таблице
        Поле устанавливается в null, запись сохраняется, потом
        удаляется то, на что указывало поле.
        Типичный пример - удаление заявителя, заказчика, покойника.
        """
        field_to_delete = getattr(instance, field_name)
        if field_to_delete:
            setattr(instance, field_name, None)
            instance.save()
            try:
                field_to_delete.delete()
            except ProtectedError:
                pass

class UnclearDate:
    def __init__(self, year, month=None, day=None):
        self.d = datetime.date(year, month or 1, day or 1)
        self.no_day = not day
        self.no_month = not month

    def strftime(self, format):
        if self.no_day:
            format = format.replace('%d.', '')
        if self.no_month:
            format = format.replace('%m.', '')

        if self.d.year < 1900:
            d1 = datetime.date(1900 + self.d.year % 100, self.d.month, self.d.day)
            return d1.strftime(format).replace(str(d1.year), str(self.d.year))
        return self.d.strftime(format)

    def get_datetime(self):
        return self.d

    def __repr__(self):
        return u'<UnclearDate: %s>' % self.strftime('%d.%m.%Y')

    def __unicode__(self):
        return self.strftime('%d.%m.%Y')

    def str_safe(self):
        """
        YYYY or YYYY-MM or YYYY-MM-DD
        """
        result = str(self.d.year)
        if not self.no_month:
            result += '-%02d' % self.d.month
        if not self.no_day:
            result += '-%02d' % self.d.day
        return result

    @classmethod
    def from_str_safe(cls, s):
        """
        Сделать UnclearDate из yyyy-mm-dd, yyyy-mm, yyyy
        """
        m = re.search(r'^(\d{4})(?:\-(\d{2}))?(?:\-(\d{2}))?$', s)
        if not m:
            raise ValueError('Invalid data to make an UnclearDate object')
        day = m.group(3)
        month = m.group(2)
        year = m.group(1)
        return cls(
            int(year),
            month and int(month) or None,
            day and int(day) or None,
        )

    @property
    def month(self):
        return self.d.month

    @property
    def year(self):
        return self.d.year

    @property
    def day(self):
        return self.d.day

    def prepare_compare(self, other):
        """
        Подготовить даты к сравнению
        
        Возвращает строки обеих дат
        1999 и 7.7.1999 дожны стать обе '1999-07-07'
        """
        if isinstance(other, datetime.date):
            other = UnclearDate(other.year, other.month, other.day)

        if not self.no_month and not other.no_month:
            self_month = self.month
            other_month = other.month
        elif not self.no_month and other.no_month:
            other_month = self_month = self.month
        elif self.no_month and not other.no_month:
            self_month = other_month = other.month
        elif self.no_month and other.no_month:
            self_month = other_month = 0

        if not self.no_day and not other.no_day:
            self_day = self.day
            other_day = other.day
        elif not self.no_day and other.no_day:
            other_day = self_day = self.day
        elif self.no_day and not other.no_day:
            self_day = other_day = other.day
        elif self.no_day and other.no_day:
            self_day = other_day = 0

        fmt = "%d-%02d-%02d"
        self_date = fmt % (self.year, self_month, self_day)
        other_date = fmt % (other.year, other_month, other_day)
        return (self_date , other_date, )
    
    # Было бы удобнее воспользоваться __cmp__(), но 
    # нам эти даты надо сравнивать на больше или меньше,
    # а сравнивать на равенство 07.07.1999 и 1999?
    # Пока такой потребности не было.
    # Кроме того, cmp() is deprecated в python 3

    def __lt__(self, other):
        self_date, other_date = self.prepare_compare(other)
        return self_date < other_date

    def __gt__(self, other):
        self_date, other_date = self.prepare_compare(other)
        return self_date > other_date


class UnclearDateCreator(object):
    # http://blog.elsdoerfer.name/2008/01/08/fuzzydates-or-one-django-model-field-multiple-database-columns/

    def __init__(self, field):
        self.field = field
        self.no_day_name = u'%s_no_day' % self.field.name
        self.no_month_name = u'%s_no_month' % self.field.name

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')

        date = obj.__dict__[self.field.name]
        if date is None:
            return None
        else:
            y = date.year
            if getattr(obj, self.no_month_name):
                m = None
            else:
                m = date.month
            if getattr(obj, self.no_day_name):
                d = None
            else:
                d = date.day
            return UnclearDate(y, m, d)

    def __set__(self, obj, value):
        if isinstance(value, UnclearDate):
            obj.__dict__[self.field.name] = value.d
            setattr(obj, self.no_month_name, value.no_month)
            setattr(obj, self.no_day_name, value.no_day)
        else:
            obj.__dict__[self.field.name] = self.field.to_python(value)

class UnclearDateModelField(models.DateField):
    # http://blog.elsdoerfer.name/2008/01/08/fuzzydates-or-one-django-model-field-multiple-database-columns/

    def contribute_to_class(self, cls, name):
        no_month_field = models.BooleanField(editable=False, default=False)
        no_day_field = models.BooleanField(editable=False, default=False)
        no_month_field.creation_counter = self.creation_counter
        no_day_field.creation_counter = self.creation_counter
        cls.add_to_class(u'%s_no_month' % name, no_month_field)
        cls.add_to_class(u'%s_no_day' % name, no_day_field)

        super(UnclearDateModelField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, UnclearDateCreator(self))

    def get_db_prep_save(self, value, **kwargs):
        if isinstance(value, UnclearDate):
            value = value.d
        return super(UnclearDateModelField, self).get_db_prep_save(value, **kwargs)

    def get_db_prep_lookup(self, lookup_type, value, **kwargs):
        if lookup_type == 'exact':
            return [self.get_db_prep_save(value, **kwargs)]
        elif lookup_type == 'in':
            return [self.get_db_prep_save(v, **kwargs) for v in value]
        else:
            return super(UnclearDateModelField, self).get_db_prep_lookup(lookup_type, value, **kwargs)

    def to_python(self, value):
        if isinstance(value, UnclearDate):
            return value

        return super(UnclearDateModelField, self).to_python(value)

    def formfield(self, **kwargs):
        from pd.forms import UnclearDateField, UnclearSelectDateWidget
        defaults = {
            'form_class': UnclearDateField,
            'widget': UnclearSelectDateWidget,
            }
        kwargs.update(defaults)
        return super(UnclearDateModelField, self).formfield(**kwargs)
    
    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)        
        return value.strftime('%Y-%m-%d')     

class BaseModel(models.Model):
    """
    Базовый класс для многих моделей
    """
    class Meta:
        abstract = True
        
    dt_created = models.DateTimeField(_(u"Дата/время создания"), auto_now_add=True)
    dt_modified = models.DateTimeField(_(u"Дата/время модификации"), auto_now=True)

def upload_slugified(instance, filename):
    """
    Загрузка файлов из models.FileField
    
    Полагается, что файлы загружаются в одну кучу в каталоге в зависимости
    от класса модели с FileField.
    Нелатинские символы и знаки препинания преобразуются в такое,
    что не вызывает 'нареканий' у Django
    """
    fname = u'.'.join(map(pytils.translit.slugify, filename.rsplit('.', 1)))
    if isinstance(instance, get_model('orders', 'Product')):
        return os.path.join('product-photo', fname)
    if isinstance(instance, get_model('orders', 'ProductCategory')) or \
       isinstance(instance, get_model('billing', 'Currency')):
        return os.path.join('icons', fname)

def files_upload_to(instance, filename):
    instance.original_name = filename
    fname = u'.'.join(map(pytils.translit.slugify, filename.rsplit('.', 1)))
    today = datetime.date.today()
    
    # Путь к сохраняемому файлу:
    #   - первая составляющая (каталог): - /то, к чему относятся файлы/
    #   - год/месяц/день, чтоб не допускать огромное множество файлов
    #     (каталогов) в одной папке. Заодно и дата создания наглядна
    #   - первичный ключ того объекта, проверку на доступ к которому
    #     будем осуществлять
    #   - имя файла, оттуда убраны нелатинские символы, знаки препинания
    #     и т.п.
    today_pk_dir = "{0:d}/{1:02d}/{2:02d}".format(today.year, today.month, today.day)
    today_pk_dir += "/%s" 
    
    if isinstance(instance, get_model('burials', 'BurialFiles')):
        return os.path.join('bfiles',
                today_pk_dir % instance.burial.pk, fname)
    elif isinstance(instance, get_model('burials', 'PlaceStatusFiles')):
        return os.path.join('place-status-files',
                today_pk_dir % instance.placestatus.pk, fname)
    elif isinstance(instance, get_model('persons', 'DeathCertificateScan')):
        return os.path.join('death-certificates',
                today_pk_dir % instance.deathcertificate.person.pk, fname)
    elif isinstance(instance, get_model('burials', 'PlacePhoto')):
        return os.path.join('place-photos',
                today_pk_dir % instance.pk, fname)
    elif isinstance(instance, get_model('burials', 'AreaPhoto')):
        return os.path.join('area-photos',
                today_pk_dir % instance.cemetery.pk, fname)
    elif isinstance(instance, get_model('users', 'RegisterProfileScan')):
        return os.path.join('register-profile-scans',
                today_pk_dir % instance.registerprofile.pk, fname)
    elif isinstance(instance, get_model('users', 'RegisterProfileContract')):
        return os.path.join('register-profile-contracts',
                today_pk_dir % instance.registerprofile.pk, fname)
    elif isinstance(instance, get_model('users', 'CustomerProfilePhoto')):
        return os.path.join('customer-profile',
                today_pk_dir % instance.customerprofile.user.pk, fname)
    elif isinstance(instance, get_model('users', 'OrgCertificate')):
        return os.path.join('org-certificates',
                today_pk_dir % instance.org.pk, fname)
    elif isinstance(instance, get_model('users', 'OrgContract')):
        return os.path.join('org-contracts',
                today_pk_dir % instance.org.pk, fname)
    elif isinstance(instance, get_model('persons', 'MemoryGallery')):
        return os.path.join('memory-gallery',
                today_pk_dir % instance.creator.pk, fname)
    elif isinstance(instance, get_model('orders', 'OrderPhoto')):
        return os.path.join('order-photo',
                today_pk_dir % instance.order.pk, fname)
    else:
        return os.path.join('files', fname)


class Files(models.Model):
    """
    Базовый класс для файлов
    """
    class Meta:
        abstract = True
        
    bfile = models.FileField(u"Файл", max_length=255, upload_to=files_upload_to, blank=True)
    comment = models.CharField(u"Описание", max_length=96, blank=True)
    original_name = models.CharField(max_length=255, editable=False)
    creator = models.ForeignKey('auth.User', verbose_name=_(u"Создатель"), editable=False, null=True,
                                on_delete=models.PROTECT)
    date_of_creation = models.DateTimeField(auto_now_add=True)

    def delete_from_media(self):
        if self.bfile and os.path.exists(self.bfile.path):
            os.remove(self.bfile.path)
            thmb = os.path.join(settings.THUMBNAILS_STORAGE_ROOT, self.bfile.name)
            if os.path.exists(thmb):
                shutil.rmtree(thmb)

    def delete(self):
        self.delete_from_media()
        super(Files, self).delete()

def validate_gt0(value):
    if value <= 0:
        raise ValidationError(_(u'Должно быть больше нуля'))

def validate_username(value):
    if not re.match(r'^[A-Za-z0-9@_-]{1,30}$', value):
        raise ValidationError(_(u"Может быть до 30 латинских букв, "
                                u"цифр, знаков подчеркивания, дефисов, @"
        ))

def validate_phone_as_number(value):
    """
    Проверка поля телефона
    """
    min_digits = 10
    max_digits = 12
    if not re.search(r'^\d{%d,%d}$' % (min_digits, max_digits, ), str(value)):
        raise ValidationError(_(u'Неверный номер телефона, надо от %d до %d цифр') % (min_digits, max_digits, ))
    # Могут приходить и из json rest запросов, просто строки, а не десятичные числа из формы
    if isinstance(value, basestring) and value.startswith('0'):
        raise ValidationError(_(u'Неверный первый знак в телефоне'))

class  GetLogsMixin(object):
    """
    Для функция get_logs(), применяемой во многих моделях
    """

    def get_logs(self):
        ct = ContentType.objects.get_for_model(self)
        return Log.objects.filter(ct=ct, obj_id=self.pk).order_by('-pk')

add_introspection_rules([], ['^pd\.models\.UnclearDateModelField'])
