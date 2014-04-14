#! /usr/bin/env python
# coding=utf-8
#
# send_video.py
# ---------------
#
# Назначение:
# -----------
# Отправить видеоролики и их описание (csv- файл на сервер)
#
# Получаем от составителя видеокурса его папку, например support/. Имя папки - 
# параметр этой процедуры; если не задано, то полагаем текущую папку,
# т.е. что процедуру положили в support/.
# В корне папки support/ лежит tablica.ods с описанием того, что в видеокурсе.
# Каждая строка таблицы содержит колонки:
#
#   A (0):  тип пользователя, для которого этот пункт или заголовок раздела, loru или oms
#   B (1):  номер по порядку, может быть типа 1 или 2.1, но этот номер пока не используем
#   C (2):  заголовок или краткое описание пункта
#   D (3):  текст диктора, если это пункт
#   E (4):  имя_файла.mp4 с видеороликом,
#           он будет support/video/loru/имя_файла.mp4 или support/video/oms/имя_файла.mp4
#           в зависимости от содержимого колонки A
#
#   NB: если в строке колонка имя_файла.mp4 пустая, то это будет заголовком раздела,
#       после которого следуют пункты с mp4 файлами вплоть до следующего раздела
#       (строки с пустой колонкой для имени_файла.mp4) или до конца таблицы
#
# Анализируем таблицу, получаем csv- файл с полями, аналогичными тем, что в таблице:
#
#   *  тип пользователя, для которого курс, loru или oms
#   *: заголовок или краткое описание пункта
#   *: текст диктора, если это пункт
#   *: имя_файла.mp4 с видеороликом
#
# Требования:
# -----------
# * python-odfpy
# * ffmpeg, для конвертации mp4 в webm, ogg

DESCRIPTION_ODS='tablica.ods'
DESCRIPTION_CSV='description.csv'

import sys, os, subprocess, re

from odf.opendocument import load
from odf.opendocument import Spreadsheet
from odf.text import P
from odf.table import TableRow, TableCell

import csv

def main():
    
    folder = len(sys.argv) > 1 and sys.argv[1] or '.'
    try:
        doc = load(os.path.join(folder, DESCRIPTION_ODS,)).spreadsheet
    except IOError:
        scram('%s not found in %s' % os.path.join(folder, DESCRIPTION_ODS,))
    ofile  = open(os.path.join(folder, DESCRIPTION_CSV,), "wb")
    csv_writer = csv.writer(ofile)
    rows = doc.getElementsByType(TableRow)
    for row in rows:
        cells = row.getElementsByType(TableCell)
        type_ = ods_cell(cells[0]).strip().lower()
        if type_ not in ('loru', 'oms', ):
            continue
        title = ods_cell(cells[2])
        try:
            text = ods_cell(cells[3])
        except IndexError:
            text = ''
        try:
            fname = ods_cell(cells[4])
        except IndexError:
            fname = ''
        csv_writer.writerow(map(lambda u: u.encode("utf8").strip(),[
            type_,
            title,
            text,
            fname,
        ]))
        if fname:
            if not re.search(r'\.mp4$', fname, flags=re.IGNORECASE):
                fname += '.mp4'
            fname = os.path.join(folder, 'video', type_, fname)
            fname_webm = re.sub(r'\.mp4$', r'.webm', fname, flags=re.IGNORECASE)
            fname_ogg = re.sub(r'\.mp4$', r'.ogg', fname, flags=re.IGNORECASE)
            # TODO Сравнить даты
            do_cmd(
                'ffmpeg -y -i %s -c:v libvpx -crf 10 -b:v 1M -c:a libvorbis %s' % \
                (fname, fname_webm,)
            )
            do_cmd(
                'ffmpeg -y -i %s -acodec libvorbis -vcodec libtheora -f ogg %s' % \
                (fname, fname_ogg,)
            )

def ods_cell(cell):
    return "".join([unicode(data) for data in cell.getElementsByType(P)])

def do_cmd(cmd):
    outp = subprocess.check_output(cmd,
                                   stderr=subprocess.STDOUT,
                                   shell=True)
    print '> %s\n%s' % (cmd, outp,)
    return outp

def scram(message, rc=1):
    print message
    exit(rc)

main()
