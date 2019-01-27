#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Импорт в кладбище из xls файла. Многие годы из крематория уходили
# урны для захоронения в землю, на северных кладбищах их не вводили.
# Сейчас на соответствуюшем кладбище создаем фиктивный сектор/ряд/место
# */*/*, туда ставим эти урны

# Запуск из ./manage.py shell :
# execfile('/path/to/script_name.py')

# Ид пользователя, который делает импорт.
# Делаем отрицательным, чтоб сдуру не запустить
#
PROFILE_ID = -23

INPUT_XLS = '/home/sev/d/Cna.xls'

# Поля входного excel-2003 файла
START_COL = 0
#
#   START_COL +     (0) Регистрационный номер
#                   (1) Дата ритуала, будет фактической датой
#                   (2) ФИО усопшего
#                   (3) Заказ-наряд, не используем
#                   (4) Кладбище

# 
AREA_NAME =  u'-'
ROW_NAME =  u'-'
PLACE_NAME = u'-'

import datetime, xlrd, gc, re, string

from django.db import transaction, connection, reset_queries

from logs.models import write_log, LogOperation
from burials.models import Burial, Place, Cemetery, Area, AreaPurpose, Grave, BurialComment
from persons.models import DeadPerson
from users.models import Profile

def main():
    profile = Profile.objects.get(pk=PROFILE_ID)
    ugh = profile.org
    user = profile.user
    area_availability = Area.AVAILABILITY_OPEN
    area_purpose, _created = AreaPurpose.objects.get_or_create(name=u'общественный')
    burial_container = Burial.CONTAINER_URN
    burial_type = Burial.BURIAL_NEW

    rb = xlrd.open_workbook(INPUT_XLS)
    sheet = rb.sheet_by_index(0)

    burial_comment = u"Дата ритуала: %s"
    n = 0
    for row in range(1, sheet.nrows):

        account_number = to_str(sheet.cell(row, START_COL + 0))

        fact_date = sheet.cell(row, START_COL + 1)
        fact_date = to_date(fact_date, rb)

        fio_initial = to_str(sheet.cell(row, START_COL + 2))
        f_ = i_ = o_ = ''
        fio = re.sub(r'\s+\-\s+', u'-', fio_initial)
        m = re.search(r'^(\S+)[\s\.]+(\S+?)[\s\.]+(\S+?)\.*$', fio)
        if m:
            f_ = m.group(1)
            i_ = m.group(2)
            o_ = m.group(3)
        else:
            m = re.search(r'^(\S+)[\s\.]+(\S+?)\.*$', fio)
            if m:
                f_ = m.group(1)
                i_ = m.group(2)
            else:
                m = re.search(r'^(\S+)$', fio)
                if m:
                    f_ = m.group(1)
                elif fio_initial:
                    raise Exception("Faled to get fio: '%s', line %s " % (fio_initial, n + 1))

        last_name = capitalize(f_)
        first_name = capitalize(i_)
        middle_name = capitalize(o_)

        cemetery_name = to_str(sheet.cell(row, START_COL + 4))
        cemetery = Cemetery.objects.get(ugh=ugh, name=cemetery_name)

        area, _created = Area.objects.get_or_create(
            cemetery=cemetery,
            name=AREA_NAME,
            defaults = {
                'availability': area_availability,
                'purpose': area_purpose,
                'places_count': 1,
            }
        )

        place, _created = Place.objects.get_or_create(
            cemetery=cemetery,
            area=area,
            row=ROW_NAME,
            place=PLACE_NAME,
        )

        grave, _created = Grave.objects.get_or_create(
            place=place,
            grave_number=1
        )

        deadman = DeadPerson.objects.create(
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
        )

        burial = Burial.objects.create(
            burial_type=burial_type,
            burial_container=burial_container,
            source_type=Burial.SOURCE_TRANSFERRED,
            account_number=account_number,
            place=place,
            cemetery=cemetery,
            area=area,
            row=ROW_NAME,
            place_number=PLACE_NAME,
            grave=grave,
            grave_number=1,
            fact_date=fact_date,
            deadman=deadman,
            applicant=None,
            ugh=ugh,
            status=Burial.STATUS_CLOSED,
            changed_by=user,
            flag_no_applicant_doc_required = True,
        )

        if fact_date:
            BurialComment.objects.create(
                burial=burial,
                creator=user,
                comment=burial_comment % datetime.datetime.strftime(fact_date, '%d.%m.%Y'),
            )
        write_log(
            request=None,
            user=user,
            obj=burial,
            operation=LogOperation.CLOSED_BURIAL_TRANSFERRED,
        )

        if n > 0 and n % 500 == 0:
            transaction.commit()
            gc.collect()
            reset_queries()
            print 'Processed', n, 'of', sheet.nrows - 1
        n += 1

    print 'Processed', n, 'of', sheet.nrows - 1

def to_str(cell):
    type_ = cell.ctype
    if type_ == xlrd.XL_CELL_NUMBER:
        if int(cell.value) == cell.value:
            result = str(int(cell.value))
        else:
            result = str(cell.value)
    elif type_ == xlrd.XL_CELL_TEXT:
        result = unicode(cell.value.strip())
    else:
        result = ""
    return result

def to_date(cell, book):
    type_ = cell.ctype
    if type_ == xlrd.XL_CELL_TEXT:
        result = datetime.datetime.strptime(cell.value, '%d.%m.%Y')
    else:
        result = datetime.datetime(*xlrd.xldate_as_tuple(cell.value, book.datemode))
    return result


def capitalize(s):
    """
    Капитализация строки имени, фамилии, отчества

    Учесть двойные фамилии (Петров-Водкин) и много слов, например, Эрих Мария
    """
    if s is None:
        return ''
    dash_char = lambda m: u"-%s" % m.group(1).upper()
    return s and re.sub(r'\-(\S)', dash_char, string.capwords(s)) or ''

transaction.set_autocommit(False)
try:
    main()
finally:
    transaction.commit()
    transaction.set_autocommit(True)
