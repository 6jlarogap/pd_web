#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Импорт в колумбарий из xls файла

# Запуск из ./manage.py shell :
# execfile('/path/to/script_name.py')


COLUMBARIUM_NAME = u'Колумбарий, Крематорий'

# Ид пользователя, который делает импорт.
# Делаем отрицательным, чтоб сдуру не запустить
#
PROFILE_ID = -41

INPUT_XLS = '/home/suprune20/d/columbarium.xls'

# Поля входного excel-2003 файла
START_COL = 7
#
#   START_COL +     (0) Регистрационный номер
#                   (1) Дата ритуала, будет фактической датой
#                   (2) Фамилия усопшего
#                   (3) Имя
#                   (4) Отчество
#                   (5) Участок
#                   (6) Ряд
#                   (7) Место
#
#   Если дата ритуала не пуста, в комментарий заносим: "Дата ритуала"

import datetime, xlrd, gc

from django.db import transaction, connection, reset_queries

from logs.models import write_log, LogOperation
from burials.models import Burial, Place, Cemetery, Area, AreaPurpose, Grave, BurialComment
from persons.models import DeadPerson
from users.models import Profile

def main():
    profile = Profile.objects.get(pk=PROFILE_ID)
    ugh = profile.org
    user = profile.user
    cemetery = Cemetery.objects.get(ugh=ugh, name=COLUMBARIUM_NAME)
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

        last_name = to_str(sheet.cell(row, START_COL + 2))
        first_name = to_str(sheet.cell(row, START_COL + 3))
        middle_name = to_str(sheet.cell(row, START_COL + 4))

        area_n = to_str(sheet.cell(row, START_COL + 5))
        if not area_n:
            raise Exception("No area, row %s" % (row +1))

        row_n = to_str(sheet.cell(row, START_COL + 6))
        place_n = to_str(sheet.cell(row, START_COL + 7)) or u"-"

        area, _created = Area.objects.get_or_create(
            cemetery=cemetery,
            name=area_n,
            defaults = {
                'availability': area_availability,
                'purpose': area_purpose,
                'places_count': 1,
            }
        )

        place, _created = Place.objects.get_or_create(
            cemetery=cemetery,
            area=area,
            row=row_n,
            place=place_n,
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
            row=row_n,
            place_number=place_n,
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

transaction.set_autocommit(False)
try:
    main()
finally:
    transaction.commit()
    transaction.set_autocommit(True)
