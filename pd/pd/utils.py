# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.validators import RegexValidator, MinLengthValidator
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _

import datetime
from pytz import timezone, utc
import re
import string
from collections import Sequence

from PIL import Image
import magic

class DigitsValidator(RegexValidator):
    regex = '^\d+$'
    message = _(u'Допускаются только цифры')
    code = 'digits'

    def __init__(self):
        super(DigitsValidator, self).__init__(regex=self.regex)

class LengthValidator(MinLengthValidator):
    compare = lambda self, v, l: v != l
    message = _(u'Длина %(limit_value)s')
    code = 'length_custom'

class VarLengthValidator(MinLengthValidator):
    compare = lambda self, v, l:  not l[0] <= v <= l[1]
    message = _(u'Длина %(limit_value)s')
    code = 'length_custom1'

class NotEmptyValidator(MinLengthValidator):
    compare = lambda self, v, l:  not v
    clean = lambda self, x: unicode(x).strip()
    message = _(u'Не пусто')
    code = 'not_empty'

def utcisoformat(dt, remove_mcsec=True):
    """
    Return a datetime object in ISO 8601 format in UTC, without microseconds
    or time zone offset other than 'Z', e.g. '2011-06-28T00:00:00Z'.
    """
    # Convert datetime to UTC, remove microseconds, remove timezone, convert to string
    TZ = timezone(settings.TIME_ZONE)
    if remove_mcsec:
        dt = dt.replace(microsecond=0)
    return TZ.localize(dt).astimezone(utc).replace(tzinfo=None).isoformat() + 'Z'

def utc2local(dt):
    """
    Из даты/времени по Гринвичу сделать локальную дату
    """
    local_tz = timezone(settings.TIME_ZONE)
    utc_tz = timezone('UTC')
    return utc_tz.localize(dt).astimezone(local_tz).replace(tzinfo=None)

def local2utc(dt):
    """
    Из локальной даты/времени сделать дату по Гринвичу
    """
    local_tz = timezone(settings.TIME_ZONE)
    utc_tz = timezone('UTC')
    return local_tz.localize(dt).astimezone(utc_tz).replace(tzinfo=None)

def host_country_code(request):
    """
    Получить строку 'ru' запроса типа http://org.pohoronnodelo.ru

    Если к системе обращаются по ip-адресу или localhost или host,
    возвращается пустая строка
    """
    m = re.search(r'\.([a-zA-Z]{2,})(?:\:\d+)?$', request.get_host())
    if m:
        return m.group(1).lower()
    else:
        return ''

def phones_from_text(phones_text):
    phones = []
    phones_text = phones_text and phones_text.strip()
    if phones_text:
        for phone in re.split(r'[\r\n,;]+', phones_text):
            phone = phone.strip()
            if phone:
                phones.append(phone)
    return phones

class PhonesFromTextMixin(object):

    def phones_func(self, obj):
        return phones_from_text(obj.phones)

def str_to_bool_or_None(s):
    """
    Строку 'true' или 'false' преобразовать в boolean True/False или None, если строка не 'true'/'false'

    Применяется при разборе multipart/form-data параметров, чтоб были аналогичны разбору json параметров,
    но с сохранением совместимости, если передаются булевы параметры
    """
    result = None
    if isinstance(s, basestring):
        s = s.lower()
        if s == 'true':
            result = True
        elif s == 'false':
            result = False
    elif isinstance(s, bool):
        result = s
    return result

class EmailMessage(EmailMessage):
    """
    Формирование, отправка почты
    
    В добавок к EmailMessage от django:
        - если почта от какого-то другого сервера, нежели производственного,
        тему письма предваряем "[dev] "
    """

    def send(self, **kwargs):
        if not settings.PRODUCTION_SITE:
            self.subject = u"[dev] %s" % self.subject
        if settings.BCC_OUR_MAIL:
            self.bcc.append(settings.BCC_OUR_MAIL)
        super(EmailMessage, self).send(**kwargs)

class CreatedAtMixin(object):
    def createdAt_func(self, instance):
        if hasattr(instance, 'dt_created'):
            dt_created = instance.dt_created
        elif hasattr(instance, 'date_of_creation'):
            dt_created = instance.date_of_creation
        else:
            return ""
        return utcisoformat(dt_created)

    def modifiedAt_func(self, instance):
        return utcisoformat(instance.dt_modified)

def get_image(image):
    """
    Является ли загруженный файл фото? Если да, то возвращает Image(фото)
    """
    try:
        return Image.open(image)
    except IOError:
        return None

def is_video(video):
    """
    Является ли загруженный файл video
    """
    valid = False
    for chunk in video.chunks(chunk_size=min(video.size, 128*1024)):
        chunk0 = chunk
        break
    mimetype = magic.from_buffer(chunk0, mime=True)
    if mimetype:
        if re.search(r'video|ogg|mpeg|webm|avi', mimetype.lower()):
            valid = True 
        else:
            mimetype0 = magic.from_buffer(chunk0)
            if re.search(r'iso', mimetype0.lower()):
                # flv: ISO media
                valid = True
    return valid

def capitalize(s):
    """
    Капитализация строки имени, фамилии, отчества

    Учесть двойные фамилии (Петров-Водкин) и много слов, например, Эрих Мария
    """
    if s is None:
        return ''
    dash_char = lambda m: u"-%s" % m.group(1).upper()
    return s and re.sub(r'\-(\S)', dash_char, string.capwords(s)) or ''

def re_search(s):
    """
    Преобразовать строку в таковую для поиска __iregex = regex

    Применяется в поиске по фио или по названию организации,
    например поиск:
        ?лейник     вернет  Олейник, Алейник, Алейников
        *лейник             Олейник, Алейник, Калейник,
                            НО! не Алейников
                                (особое сочетание: * в начале)
        д?р?шев             Дарашевич, Дорошевич

    Полагаем, что на вход всегда идет строка, не содержащая пробелов
    """
    regex = s.strip()
    if re.search(r'[\?\*]', regex):
        regex = re.sub(r'\.', r'\.', regex)
        regex = re.sub(r'\?', r'.',  regex)
        regex = re.sub(r'\*', r'.*', regex)
        if regex.startswith(".*"):
            regex = u"%s$" % regex
        else:
            regex = u"^%s" % regex
    else:
        regex = u"^%s" % regex
    return regex

class SeriesTable(Sequence):
    """
    Отдать статистические серии в шаблон

    Проблема: Считаем статистику, получаем несколько результатов,
    списков типа
        показатель1 = [(дата1, значение1), (дата2, значение1)...],
        показатель2 = [(дата1, значение3), (дата2, значение4)...],
        ...
    А в шаблон надо отдать таблицу (*):

                          показатель1  показатель2
    --------------------------------------------------
    {date:дата1, values: [значение1,   значение3 ...]}
    {date:дата2, values: [значение2,   значение4 ...]}

    Всё было бы хорошо, если б существовала шаблонная конструкция
    типа for i in показатель1.length:
             показатель1[i][1], показатель2[i][1]
    Но даже если и была такая удобная шаблонная конструкция,
    при пажинации надо отдать именно таблицу (*),
    т.е. ее надо сделать в коде. Можно из массивов показателей
    собрать таблицу из списков показателей, но это расход
    памяти. Посему таблицу (*) делаем здесь, в этом классе,
    логической. Инициализируется этот класс списками показателей,
    точнее ссылками на них, а отдает на выходе двухмерный
    массив типа таблицы (*).
    Кроме того, не надо показывать в таблице (*) даты с пустыми
    показателями.
    """

    def __init__(self, *series):
        super(SeriesTable, self).__init__()
        self._collection = list()
        # индексы списков-показателей с непустыми показателями
        self._indexes = list()
        for ser in series:
            self._collection.append(ser)
        for i in xrange(len(self._collection[0])):
            do_append = False
            for k in range(len(self._collection)):
                if self._collection[k][i][1]:
                    do_append = True
                    break
            if do_append:
                self._indexes.append(i)
        self._total = len(self._indexes)

    def __len__(self):
        return self._total

    def __getitem__(self, key):
        if isinstance(key, slice) :
            result = []
            stop = key.stop
            if stop is None:
                stop = self._total
            for i in xrange(key.start or 0, stop, key.step or 1):
                try:
                    result.append(self.__getitem__(i))
                except IndexError:
                    pass
        elif isinstance(key, int):
            key = self._indexes[key]
            result = dict(
                date=self._collection[0][key][0],
                values=[]
            )
            for ser in self._collection:
                result['values'].append(ser[key][1])
        return result
