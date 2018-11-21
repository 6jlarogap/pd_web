# -*- coding: utf-8 -*-

import os, shutil
import pytils
import datetime
from dateutil.relativedelta import relativedelta
import re

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.db.models.loading import get_model
from django.db.models.deletion import ProtectedError
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from logs.models import Log
from pd.views import ServiceException

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

    SAFE_STR_REGEX = r'^(\d{4})(?:\-(\d{2}))?(?:\-(\d{2}))?$'

    VALUE_ERROR_CREATE = 'Invalid data to make an UnclearDate object'

    def __init__(self, year, month=None, day=None):
        self.d = datetime.date(year, month or 1, day or 1)
        self.no_day = not day
        self.no_month = not month

    def strftime(self, format):
        if self.no_day:
            # Убираем день с возможными разделителями (.-/) слева или справа
            format = re.sub(r'\.\%d|\%d\.|\-\%d|\%d\-|\/\%d|\%d\/', '', format)
            # Убираем день, если формат был без разделителей
            format = re.sub(r'\%d', '', format)
        if self.no_month:
            # Убираем месяц с возможными разделителями (.-/) слева или справа
            format = re.sub(r'\.\%m|\%m\.|\-\%m|\%m\-|\/\%m|\%m\/', '', format)
            # Убираем месяц, если формат был без разделителей
            format = re.sub(r'\%m', '', format)

        if self.d.year < 1900:
            # Есть проблема в datetime.strftime() с годами раньше 1900 (ValueError exception)
            # кроме того:
            #   1600, 1200, ...: в феврале 29 дней (как в 2000)
            #   1800, 1700, 1500, ...: в феврале 28 дней (как в 1900)
            d_base = 1900 if self.d.year % 400 else 2000
            d1 = datetime.date(d_base + self.d.year % 100, self.d.month, self.d.day)
            return d1.strftime(format).replace(str(d1.year), str(self.d.year).rjust(4, '0'))
        return self.d.strftime(format)

    def get_datetime(self):
        return self.d

    def __repr__(self):
        return u'<UnclearDate: %s>' % self.strftime('%d.%m.%Y')

    def __unicode__(self):
        return self.strftime('%d.%m.%Y')

    def str_safe(self, format=''):
        """
        YYYY or YYYY-MM or YYYY-MM-DD

        Возможен возврат ММ.ДД.ГГГГ, ММ.ГГГГ, ГГГГ при формате 'd.m'y'
        """
        result = "%04d" % self.d.year
        if format == 'd.m.y':
            if not self.no_month:
                result = '%02d.%s' % (self.d.month, result)
            if not self.no_day:
                result = '%02d.%s' % (self.d.day, result)
        else:
            if not self.no_month:
                result += '-%02d' % self.d.month
            if not self.no_day:
                result += '-%02d' % self.d.day
        return result

    @classmethod
    def from_str_safe(cls, s, format=''):
        """
        Сделать UnclearDate из yyyy-mm-dd, yyyy-mm, yyyy, или из None ('null')

        При параметре format='d.m.y.' делаем из нее UnclearDate
        """
        if s:
            s = s.strip()
        if not s or s.lower() == 'null':
            return None
        if format == 'd.m.y':
            year, month, day = cls.from_str_dmy(s)
        else:
            m = re.search(cls.SAFE_STR_REGEX, s)
            if not m:
                raise ValueError(cls.VALUE_ERROR_CREATE)
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

        fmt = "%04d-%02d-%02d"
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

    @classmethod
    def from_str_dmy(cls, s):
        m = re.search(r'^(\d{2})[\.\/\-]?(\d{2})[\.\/\-]?(\d{4})$', s)
        if m:
            year = int(m.group(3))
            month = int(m.group(2))
            day = int(m.group(1))
        else:
            m = re.search(r'^(\d{2})[\.\/\-]?(\d{4})$', s)
            if m:
                year = int(m.group(2))
                month = int(m.group(1))
                day = None
            else:
                m = re.search(r'^(\d{4})$', s)
                if m:
                    year = int(m.group(1))
                    month = None
                    day = None
                else:
                    raise ValueError(cls.VALUE_ERROR_CREATE)
        return year, month, day

    @classmethod
    def check_safe_str(cls, s, check_today=False, format=''):
        """
        Проверка правильности строки "гггг-мм-дд", "гггг-мм", "гггг", или None ("null"), если дата не задана

        check_today - надо ли еще проверять, чтобы не было больше текущей даты
        Может возвратить непустое сообщение об ошибке
        """
        message = ''
        if isinstance(s, basestring):
            s = s.strip()
            if s.lower() == 'null':
                s = None
        if s:
            try:

                if format == 'd.m.y':
                    try:
                        year, month, day = cls.from_str_dmy(s)
                    except ValueError:
                        raise ServiceException(_(
                            u"Неверный формат даты. "
                            u"Допускается ММ.ДД.ГГГГ, ММ.ГГГГ, ГГГГ. Точки можно опустить или вместо них - или /"))

                else:
                    m = re.search(cls.SAFE_STR_REGEX, s)
                    if not m:
                        raise ServiceException(_(u"Неверный формат даты. Допускается ГГГГ-ММ-ДД, ГГГГ-ММ, ГГГГ"))
                    year = m.group(1)
                    month = m.group(2)
                    day = m.group(3)

                    year = int(year)
                    if month:
                        month = int(month)
                    else:
                        month = None
                    if day:
                        day = int(day)
                    else:
                        day = None

                if not year:
                    raise ServiceException(_(u"Неверный год"))
                if month is not None and not (1 <= month <= 12):
                    raise ServiceException(_(u"Неверный месяц"))
                if day is not None and not (1 <= day <= 31):
                    raise ServiceException(_(u"Неверный день"))

                if month and day:
                    try:
                        datetime.datetime.strptime("%04d-%02d-%02d" % (year, month, day), "%Y-%m-%d")
                    except ValueError:
                        raise ServiceException(_(u"Неверная дата"))

                if check_today:
                    t_month = month if month else 1
                    t_day = day if day else 1
                    if datetime.date.today() < datetime.date(year, t_month, t_day):
                        raise ServiceException(_(u"Дата больше текущей"))
            except ServiceException as excpt:
                message = excpt.message
        return message

    def diff(self, d):
        """
        Сравнить эту UnclearDate c d (UnlearDate or date or datetime)

        Результат: relativedelta: словарь, включающий years, months, days
        """
        if not self or not d:
            raise ValueError(_(u'Одна или обе даты для сравнения не заданы'))
        last = self.d
        if self.no_month:
            try:
                last = datetime.date(self.d.year, month=12, day=31)
            # Мало ли что там было при переходе из одного календаря в другой?
            except ValueError:
                pass
        elif self.no_day:
            for last_day_of_month in range(31, 0, -1):
                try:
                    last = datetime.date(self.d.year, month=self.d.month, day=last_day_of_month)
                except ValueError:
                    pass
                else:
                    break
        if isinstance(d, UnclearDate):
            first = d.d
            try:
                if d.no_month:
                    first = datetime.date(d.d.year, month=1, day=1)
                elif d.no_day:
                    first = datetime.date(d.d.year, month=d.d.month, day=1)
            except ValueError:
                pass
        elif isinstance(d, datetime.datetime) or isinstance(d, datetime.date):
            first = d
        else:
            raise ValueError(_(u'Неверный тип данного для даты для сравнения'))
        return relativedelta(last, first)

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
    Базовый класс для многих моделей. Даты создания/модификации автоматически
    """
    class Meta:
        abstract = True
        
    dt_created = models.DateTimeField(_(u"Дата/время создания"), auto_now_add=True)
    dt_modified = models.DateTimeField(_(u"Дата/время модификации"), auto_now=True)

class BaseModelManualDtCreated(models.Model):
    """
    Базовый класс для многих моделей. Дата создания заносится в коде

    В производных классах должны быть переопределены методы save(),
    чтобы дата создания устанавливались, если не была
    установлена автоматически
    """
    class Meta:
        abstract = True

    dt_created = models.DateTimeField(_(u"Дата/время создания"))
    dt_modified = models.DateTimeField(_(u"Дата/время модификации"), auto_now=True)

    def fill_dt_created(self):
        if not self.dt_created:
            self.dt_created = datetime.datetime.now()

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
    if hasattr(instance, 'original_name'):
        instance.original_name = filename
    elif hasattr(instance, 'original_filename'):
        instance.original_filename = filename
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
    elif isinstance(instance, get_model('users', 'OrgCertificate')):
        return os.path.join('org-certificates',
                today_pk_dir % instance.org.pk, fname)
    elif isinstance(instance, get_model('users', 'OrgContract')):
        return os.path.join('org-contracts',
                today_pk_dir % instance.org.pk, fname)
    elif isinstance(instance, get_model('persons', 'MemoryGallery')):
        return os.path.join('memory-gallery',
                today_pk_dir % instance.pk, fname)
    elif isinstance(instance, get_model('orders', 'ResultFile')):
        return os.path.join('order-results',
                today_pk_dir % instance.order.pk, fname)
    elif isinstance(instance, get_model('users', 'UserPhoto')):
        return os.path.join('user-photos',
                today_pk_dir % instance.user.pk, fname)
    elif isinstance(instance, get_model('persons', 'CustomPerson')):
        return os.path.join('customperson-photos',
                today_pk_dir % instance.pk, fname)
    elif isinstance(instance, get_model('users', 'OrgGallery')):
        return os.path.join('org-gallery',
                today_pk_dir % instance.org.pk, fname)
    elif isinstance(instance, get_model('users', 'StorePhoto')):
        return os.path.join('store-photos',
                today_pk_dir % instance.store.pk, fname)
    elif isinstance(instance, get_model('burials', 'CemeteryPhoto')):
        return os.path.join('cemetery-photos',
                today_pk_dir % instance.cemetery.pk, fname)
    elif isinstance(instance, get_model('burials', 'CemeterySchema')):
        return os.path.join('cemetery-schemas',
                today_pk_dir % instance.cemetery.pk, fname)
    else:
        return os.path.join('files', fname)

class FilesMixin(object):

    def file_field(self):
        if hasattr(self, 'bfile'):
            file_ = self.bfile
        elif hasattr(self, 'photo'):
            file_ = self.photo
        else:
            file_ = None
        return file_

    def delete_from_media(self):
        file_ = self.file_field()
        if file_ and file_.path and os.path.exists(file_.path):
            try:
                dir_ = os.path.dirname(file_.path)
                os.remove(file_.path)
                os.removedirs(dir_)
            except OSError:
                pass
            thmb = os.path.join(settings.THUMBNAILS_STORAGE_ROOT, file_.name)
            if os.path.exists(thmb):
                try:
                    dir_ = os.path.dirname(thmb)
                    shutil.rmtree(thmb)
                    os.removedirs(dir_)
                except OSError:
                    pass

    def delete(self):
        self.delete_from_media()
        super(FilesMixin, self).delete()

    def delete_only_rec(self):
        """
        Удалить только запись в б.д. Файл в media оставить!
        """
        super(FilesMixin, self).delete()

    def ext(self):
        """
        Получить расширение файла

        Для тэга video в шаблоне
        """
        result = None
        file_ = self.file_field()
        if file_ and file_.path:
            m = re.search(r'^.+\.([^\.\/]+)$', file_.path)
            if m:
                return m.group(1)
        return result

class Files(FilesMixin, models.Model):
    """
    Базовый класс для файлов
    """

    # Ограничение по размеру, Мегабайт, если загружаемый файл является фото:
    MAX_IMAGE_SIZE = 10

    class Meta:
        abstract = True
        
    bfile = models.FileField(u"Файл", max_length=255, upload_to=files_upload_to, blank=True)
    comment = models.CharField(u"Описание", max_length=255, blank=True)
    original_name = models.CharField(max_length=255, editable=False)
    creator = models.ForeignKey('auth.User', verbose_name=_(u"Создатель"), editable=False, null=True,
                                on_delete=models.PROTECT)
    date_of_creation = models.DateTimeField(auto_now_add=True)

class PhotoModel(FilesMixin, models.Model):
    """
    Базовый (дополнительный) класс для моделей, у которых есть фото объекта
    """
    # Мегабайт:
    MAX_PHOTO_SIZE = 10

    class Meta:
        abstract = True

    photo = models.ImageField(u"Фото", max_length=255, upload_to=files_upload_to, blank=True, null=True)
    original_filename = models.CharField(max_length=255, editable=False, null=True)

class PhotoFiles(PhotoModel, BaseModel):
    creator = models.ForeignKey('auth.User', verbose_name=_(u"Создатель"), editable=False, null=True,
                                on_delete=models.PROTECT)
    class Meta:
        abstract = True

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
    if not re.search(r'^\+?[1-79]\d{%d,%d}$' % (min_digits-1, max_digits-1, ), unicode(value)):
        raise ValidationError(
            _(u'Неверный номер телефона в международном формате, надо от %(min_digits)d до %(max_digits)d цифр') % dict(
                min_digits=min_digits, max_digits=max_digits, 
        ))

class  GetLogsMixin(object):
    """
    Для функция get_logs(), применяемой во многих моделях
    """

    def get_logs(self):
        ct = ContentType.objects.get_for_model(self)
        return Log.objects.filter(ct=ct, obj_id=self.pk).order_by('-dt')

class CheckLifeDatesMixin(object):

    def get_parm_(self, person, *args):
        """
        Значение из person и есть ли в person
        """
        value = None
        in_request = False
        for parm in args:
            in_request = parm in person
            if in_request:
                value = person[parm]
                if value and value.lower() == 'null':
                    value = None
                break
        return value, in_request

    def check_life_dates(self, instance=None, person=None, format=''):
        """
        Проверка дат рождения/смерти у person

        - параметры person могут быть в self.request.DATA или в словаре person
        в person могут быть даты в форматах: 'гггг', 'гггг-мм', 'гггг-мм-дд',
        None или 'null'
        при format=='d.m.y' сначала преобразуем к y-m-d
        """
        if not person:
            person = self.request.DATA
        birth_date, req_birth_date = self.get_parm_(person, 'birthDate', 'dob', 'birth_date')
        death_date, req_death_date = self.get_parm_(person, 'deathDate', 'dod', 'death_date')
        fact_date,  req_fact_date  = self.get_parm_(person, 'factDate', 'fact_date')
        message = UnclearDate.check_safe_str(birth_date, check_today=True, format=format)
        if message:
            return _(u"Дата рождения: %s") % message
        message = UnclearDate.check_safe_str(death_date, check_today=True, format=format)
        if message:
            return _(u"Дата смерти: %s") % message
        message = UnclearDate.check_safe_str(fact_date, check_today=True, format=format)
        if message:
            return _(u"Дата захоронения: %s") % message
        msg_dates = _(u"Дата смерти раньше даты рождения")
        birth_date = UnclearDate.from_str_safe(birth_date, format=format)
        death_date = UnclearDate.from_str_safe(death_date, format=format)
        fact_date  = UnclearDate.from_str_safe(fact_date, format=format)
        if birth_date and death_date and birth_date > death_date:
            return msg_dates
        msg_fact_lt_birth = _(u"Дата захоронения меньше даты рождения")
        if fact_date and birth_date and birth_date > fact_date:
            return msg_fact_lt_birth
        msg_fact_lt_death = _(u"Дата захоронения меньше даты смерти")
        if fact_date and death_date and death_date > fact_date:
            return msg_fact_lt_death
        if instance:
            if not req_death_date and birth_date and instance.death_date and birth_date > instance.death_date:
                return msg_dates
            if not req_birth_date and death_date and instance.birth_date and instance.birth_date > death_date:
                return msg_dates
            if hasattr(instance, 'fact_date') and not req_fact_date and \
               birth_date and instance.fact_date  and instance.fact_date < birth_date:
                return msg_fact_lt_birth
            if hasattr(instance, 'fact_date') and not req_fact_date and \
               death_date and instance.fact_date  and instance.fact_date < death_date:
                return msg_fact_lt_death
        return ""
