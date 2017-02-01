#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Готовим к импорту колумбарий. Импортируем из их access базы
# в excel-2003 файл: вручную, выбирая конкретный колумбарий.
# Этот excel-2003 файл будет параметром этой процедуры.
# На выходе получаем выходной excel-2003 файл, из которого
# уже будет производиться импорт, другой процедурой.
#
# Почему не сразу в базу? Надо будет дать посмотреть
# работнику колумбария, возможны какие-то правки.
#
# Выходной файл будет input-NEW.xls, если исходный
# excel файл был import.xls.


# Поля входного excel-2003 файла
#
#   (0) Регистрационный номер
#   (1) Дата заказа
#   (2) ФИО заказчика (на самом деле усопшего)
#   (3) Заказ-наряд
#   (4) Район
#   (5) Сектор, обычно строка С-4Р-5
#       /сектор 4, ряд 5/
#   (6) Место

# Поля выходного excel-2003 файла.
#
#   (0) Регистрационный номер
#   (1) Дата захоронения
#   (2) Фамилия усопшего
#   (3) Имя усопшего
#   (4) Отчество усопшего
#   (5) Сектор
#   (6) Ряд
#   (7) Место
#   (8) Комментарий к захоронению: если удалось расшифровать
#       сектор и ряд, то это будет "Дата ритуала"
#   (9) Примечание. Обычно пусто, но если не удалось расшифровать
#       сектор, то там будет, например, "Не понял: <сектор>"

import sys, re, datetime, string
import xlrd, xlwt

def main():
    try:
        inp_xls = sys.argv[1]
    except IndexError:
        print "No input xls file given"
        exit(1)

    m = re.search(r'^(\S+)\.xls$', inp_xls, flags=re.I)
    if not m:
        print u"%s is not xls file" % inp_xls
        exit(1)
    out_xls = u"%s-NEW.xls" % m.group(1)

    rb = xlrd.open_workbook(inp_xls)
    sheet = rb.sheet_by_index(0)

    wb = xlwt.Workbook()
    ws = wb.add_sheet('output')

    burial_comment = u"Дата ритуала"
    for row in range(1, sheet.nrows):

        comment = u''

        account_number = sheet.cell(row, 0)
        account_number_type = account_number.ctype
        if account_number_type == xlrd.XL_CELL_NUMBER:
            account_number = int(account_number.value)
        elif account_number_type == xlrd.XL_CELL_TEXT:
            account_number = account_number.value
        else:
            account_number = ""
        ws.write(row, 0, account_number)

        fact_date = sheet.cell(row, 1).value
        try:
            datetime.datetime.strptime(fact_date, '%d.%m.%Y')
        except ValueError:
            fact_date = ''
        ws.write(row, 1, fact_date)
        if fact_date:
            ws.write(row, 8, burial_comment)

        fio = unicode(sheet.cell(row, 2).value).strip()
        f_ = i_ = o_ = ''
        fio = re.sub(r'\s+\-\s+', u'-', fio)
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
                elif fio:
                    comment += u"ОШИБКА: не распознано ФИО; '%s' " % fio
        ws.write(row, 2, capitalize(f_))
        ws.write(row, 3, capitalize(i_))
        ws.write(row, 4, capitalize(o_))

        area_ = row_ = ''
        place = u'-'
        sector_ = unicode(sheet.cell(row, 5).value).strip()
        m = re.search(ur'^[сcСC]?[\-\=\s]*(\d+)[\-\=\s]*[рpРP][\-\=\s]*(\d+)', sector_, flags=re.I)
        if m:
            # сектор ряд
            area_ = int(m.group(1))
            row_ = int(m.group(2))
        else:
            # сектор ниша
            m = re.search(ur'^[сcСC]?[\-\=\s]*(\d+)[\-\=\s]*н[\-\=\s]*(\d+)', sector_, flags=re.I)
            if m:
                area_ = int(m.group(1))
                place = int(m.group(2))
            else:
                # сектор ряд ниша
                m = re.search(ur'^[сcСC]?[\-\=\s]*(\d+)[\-\=\s]*[рpРP][\-\=\s]*(\d+)[нН][\-\=\s]*(\d+)', sector_, flags=re.I)
                if m:
                    area_ = int(m.group(1))
                    row_ = int(m.group(2))
                    place = int(m.group(3))
                else:
                    # сектор
                    m = m = re.search(ur'^[сcСC]?[\-\=\s]*(\d+)[^\d]*$', sector_, flags=re.I)
                    if m:
                        area_ = int(m.group(1))
                    else:
                        comment += u"ОШИБКА: не распознаны сектор/ряд: '%s'; " % sector_
                        place = ''
        ws.write(row, 5, area_)
        ws.write(row, 6, row_)
        ws.write(row, 7, place)

        ws.write(row, 9, comment)
    wb.save(out_xls)

def capitalize(s):
    """
    Капитализация строки имени, фамилии, отчества

    Учесть двойные фамилии (Петров-Водкин) и много слов, например, Эрих Мария
    """
    if s is None:
        return ''
    dash_char = lambda m: u"-%s" % m.group(1).upper()
    return s and re.sub(r'\-(\S)', dash_char, string.capwords(s)) or ''

main()
