#! /usr/bin/env python3
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
# Требования (применительно к openSuse Leap 15.0, где сценарий успешно работает):
# -----------
# * python3-odfpy
# * ffmpeg, для конвертации mp4 в webm, ogg
# * ssh connect to remote host via openssl keys

DESCRIPTION_ODS='tablica.ods'
DESCRIPTION_CSV='description.csv'

REMOTE_HOST = 'pohoronnoedelo.ru'
REMOTE_USER = 'suprune20'
REMOTE_DIR = '/home/suprune20/support'

import sys, os, subprocess, re, csv

from odf.opendocument import load
from odf.opendocument import Spreadsheet
from odf.text import P
from odf.table import TableRow, TableCell

def main():
    
    folder = len(sys.argv) > 1 and sys.argv[1] or '.'
    try:
        doc = load(os.path.join(folder, DESCRIPTION_ODS,)).spreadsheet
    except IOError:
        scram('%s not found in %s' % os.path.join(folder, DESCRIPTION_ODS,))
    ofile  = open(os.path.join(folder, DESCRIPTION_CSV,), "w", encoding='utf-8')
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
        csv_writer.writerow([u.strip() for u in [
            type_,
            title,
            text,
            fname,
        ]])
        if fname:
            if not re.search(r'\.mp4$', fname, flags=re.IGNORECASE):
                fname += '.mp4'
            print('Processing %s' % fname)
            fname = os.path.join(folder, 'video', type_, fname)
            if not os.path.exists(fname):
                scram('Failed to stat %s' % fname)
            fname_webm = re.sub(r'\.mp4$', r'.webm', fname, flags=re.IGNORECASE)
            fname_ogg = re.sub(r'\.mp4$', r'.ogg', fname, flags=re.IGNORECASE)
            stat_fname = os.stat(fname)
            try:
                stat_fname_webm = os.stat(fname_webm)
            except OSError:
                stat_fname_webm = None
            if not stat_fname_webm or stat_fname_webm.st_mtime < stat_fname.st_mtime:
                do_cmd(
                    'ffmpeg -y -i %s -c:v libvpx -crf 10 -b:v 1M -c:a libvorbis %s' % \
                    (fname, fname_webm,)
                )
            try:
                stat_fname_ogg = os.stat(fname_ogg)
            except OSError:
                stat_fname_ogg = None
            if not stat_fname_ogg or stat_fname_ogg.st_mtime < stat_fname.st_mtime:
                do_cmd(
                    'ffmpeg -y -i %s -acodec libvorbis -vcodec libtheora -f ogg %s' % \
                    (fname, fname_ogg,)
                )
    ofile.close()
    do_cmd(
        'rsync -avz  --delete -e ssh  %s %s@%s:%s' % \
        ( folder, REMOTE_USER, REMOTE_HOST, REMOTE_DIR,)
    )

def ods_cell(cell):
    return "".join([str(data) for data in cell.getElementsByType(P)])

def do_cmd(cmd):
    outp = subprocess.check_output(cmd,
                                   stderr=subprocess.STDOUT,
                                   shell=True).decode('utf-8')
    print('> %s\n%s' % (cmd, outp,))
    return outp

def scram(message, rc=1):
    print(message)
    exit(rc)

main()
