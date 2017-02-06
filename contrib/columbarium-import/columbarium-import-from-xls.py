#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Импорт в колумбарий из xls файла

# Запуск из ./manage.py shell :
# execfile('/path/to/script_name.py')


COLUMBARIUM_NAME = u'Колумбарий, Крематорий'

# Ид пользователя, который делает импорт.
# Делаем отрицательным, чтоб сдуру не запустить
#
PROFILE_ID = 41

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

import datetime, xlrd

from burials.models import Burial, Place, Cemetery
from persons.models import DeadPerson
from users.models import Profile

def main():
    profile = Profile.objects.get(pk=PROFILE_ID)
    cemetery = Cemetery.objects.get(ugh=profile.org, name=COLUMBARIUM_NAME)

    rb = xlrd.open_workbook(INPUT_XLS)
    sheet = rb.sheet_by_index(0)

    burial_comment = u"Дата ритуала"
    for row in range(1, sheet.nrows):

        account_number = to_str(sheet.cell(row, START_COL + 0))

        fact_date = sheet.cell(row, START_COL + 1).value
        try:
            fact_date = datetime.datetime.strptime(fact_date, '%d.%m.%Y')
        except ValueError:
            fact_date = None

        last_name = to_str(sheet.cell(row, START_COL + 2))
        first_name = to_str(sheet.cell(row, START_COL + 3))
        middle_name = to_str(sheet.cell(row, START_COL + 4))

        area_n = to_str(sheet.cell(row, START_COL + 5))
        if not area_n:
            raise Exception("No area, row %s" % (row +1))

        row_n = to_str(sheet.cell(row, START_COL + 6))
        place_n = to_str(sheet.cell(row, START_COL + 7)) or u"-"

        print account_number, datetime.datetime.strftime(fact_date, '%d.%m.%Y'), \
            last_name, first_name, middle_name, area_n, row_n, place_n


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


main()
