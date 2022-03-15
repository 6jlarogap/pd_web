from django.conf import settings
from django.core.validators import RegexValidator, MinLengthValidator
from django.core.mail import EmailMessage
from django.utils.translation import gettext_lazy as _

import datetime
import dateutil.parser
from pytz import timezone, utc
import re
import string
import math
from collections import Sequence, OrderedDict

import ipaddress
import geoip2.database

from PIL import Image
import magic

class DigitsValidator(RegexValidator):
    regex = '^\d+$'
    message = _('Допускаются только цифры')
    code = 'digits'

    def __init__(self):
        super(DigitsValidator, self).__init__(regex=self.regex)

class LengthValidator(MinLengthValidator):
    compare = lambda self, v, l: v != l
    message = _('Длина %(limit_value)s')
    code = 'length_custom'

class VarLengthValidator(MinLengthValidator):
    compare = lambda self, v, l:  not l[0] <= v <= l[1]
    message = _('Длина %(limit_value)s')
    code = 'length_custom1'

class NotEmptyValidator(MinLengthValidator):
    compare = lambda self, v, l:  not v
    clean = lambda self, x: str(x).strip()
    message = _('Не пусто')
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

def utcstr2local(str_dt):
    try:
        return utc2local(dateutil.parser.parse(str_dt, ignoretz=True))
    except (ValueError, AttributeError,):
        return None

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
    if isinstance(s, str):
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
            self.subject = "[dev] %s" % self.subject
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
    dash_char = lambda m: "-%s" % m.group(1).upper()
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
    regex = s.strip(). \
            replace('\\', '\\\\'). \
            replace('|', '\\|'). \
            replace('(', '\\('). \
            replace(')', '\\)'). \
            replace('{', '\\{'). \
            replace('}', '\\}'). \
            replace('^', '\\^'). \
            replace('$', '\\$'). \
            replace('.', '\\.'). \
            replace('+', '\\+')
    # Всего в регулярных выражениях 12 метасимволов. Кроме перечисленных выше 10,
    # еще те 2, по которым анализируем:
    if re.search(r'[\?\*]', regex):
        regex = re.sub(r'\?', r'.',  regex)
        regex = re.sub(r'\*', r'.*', regex)
        if regex.startswith(".*"):
            regex = "%s$" % regex
        else:
            regex = "^%s" % regex
    else:
        regex = "^%s" % regex
    return regex


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(list(zip(columns, row)))
        for row in cursor.fetchall()
    ]

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
        for i in range(len(self._collection[0])):
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
            for i in range(key.start or 0, stop, key.step or 1):
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

#def zoom_to_geohash_length(zoom):

    ## https://dou.ua/lenta/articles/geohash/

    ##public int getGeohashLength(Coordinates southWest, Coordinates northEast, int zoom) {
        ##double a = minGeohashLength / Math.exp(minZoom / (maxZoom - minZoom) * Math.log(maxGeohashLength / minGeohashLength));
        ##double b = Math.log(maxGeohashLength / minGeohashLength) / (maxZoom - minZoom);
        ##return (int) Math.max(minGeohashLength, Math.min(a * Math.exp(b * zoom), maxGeohashLength));
    ##}


    #MIN_GEOHASH_LENGTH = 1
    #MAX_GEOHASH_LENGTH = 12
    #MIN_ZOOM = 0;
    #MAX_ZOOM = 17;

    #zoom = min(zoom, MAX_ZOOM)
    #zoom = max(zoom, MIN_ZOOM)

    #a = MIN_GEOHASH_LENGTH / \
        #math.exp(MIN_ZOOM / (MAX_ZOOM - MIN_ZOOM) * math.log(MAX_GEOHASH_LENGTH / MIN_GEOHASH_LENGTH))

    #b = math.log(MAX_GEOHASH_LENGTH / MIN_GEOHASH_LENGTH) / (MAX_ZOOM - MIN_ZOOM);

    #return int(max(MIN_GEOHASH_LENGTH, min(a * math.exp(b * zoom), MAX_GEOHASH_LENGTH)))

def rus_to_lat(s):
    """
    В строке преобразовать русские буквы в одинаковые по начертанию латинские
    """
    if isinstance(s, str):
        result = ''
        tr_from = 'авекмнорстухАВЕКМНОРСТУХ'
        tr_to   = 'abekmhopctyxABEKMHOPCTYX'
        for c in s:
            ind = tr_from.find(c)
            if ind < 0:
                result += c
            else:
                result += tr_to[ind]
    else:
        result = s
    return result

def reorder_form_fields(fields, old_pos, new_pos):
    """
    Поместить поле из form fields из позиции old_pos перед new_pos, вернуть fields
    """
    field_keys = list(fields.keys())
    if isinstance(new_pos, str):
        new_pos = field_keys.index(new_pos)
    field_keys.insert(new_pos, field_keys.pop(old_pos))
    fields = OrderedDict((k, fields[k]) for k in field_keys)
    return fields

class IpTools(object):

    LOCAL_NETs = (
        ipaddress.IPv4Network('192.168.0.0/16'),
        ipaddress.IPv4Network('172.16.0.0/12'),
        ipaddress.IPv4Network('10.0.0.0/8'),
        ipaddress.IPv4Network('127.0.0.0/8'),
    )

    @classmethod
    def get_client_ip(cls, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @classmethod
    def ipv4_valid_address(cls, ip):
        try:
            result = ipaddress.IPv4Address(ip)
        except ipaddress.AddressValueError:
            result = None
        return result

    @classmethod
    def ipv4_is_local(cls, ip_v4_address):
        """
        """
        for net in cls.LOCAL_NETs:
            if ip_v4_address in net:
                return True
        return False

    @classmethod
    def ipv4_country(cls, ip):
        try:
            reader = geoip2.database.Reader(settings.GEOIP2_DB)
            record = reader.country(ip)
            return record.country
        except:
            return None

class RestoreObjectMixin(object):
    """
    Приводим restore_object(), отработанную в DRF 2.x, к функциям из DRF 3.x
    """
    def create(self, validated_data):
        obj = self.restore_object_(instance=None, validated_data=validated_data)
        obj.save(force_insert=True)
        return obj

    def update(self, instance, validated_data):
        obj = self.restore_object_(instance=instance, validated_data=validated_data)
        obj.save()
        return obj
