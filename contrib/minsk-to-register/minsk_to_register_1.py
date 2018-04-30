# -*- coding: utf-8 -*-

# minsk_to_register_1.py
#
# Записать в домашний каталог пользователя 8 файлов xls
# в соответствии с format.xls.
#
#   - захоронения берем с 2013г.
#   - склепов у нас нет, пропускаем, точнее формируем пустые файлы
#
# Запуск из ./manage.py shell :
# execfile('/path/to/minsk_to_register_1.py')

import os, datetime, xlwt

from django.db.models.query_utils import Q

from burials.models import Area, Burial
from users.models import Org

dir_out = os.getenv("HOME")
date_from = datetime.date(2013, 1, 1)
date_to = datetime.date(2018, 1, 31)
org = Org.objects.get(pk=2)

# Вертикальные колумбарии: в названии кладбища есть слово колумбарий

# Горизонтальные колумбарии
#
horz_columbariums = (
    dict(
        cemetery__name=u'Колодищи',
        name=u'132у'
    ),
)

def make_xlss(org, date_from, date_to, dir_out):
    
    q_dates = Q(
        annulated=False,
        status= Burial.STATUS_CLOSED,
        ugh=org,
    )
    if date_from:
        q_dates &= Q(fact_date__gte=date_from)
    if date_to:
        q_dates &= Q(fact_date__lte=date_to)

    # Горизонтальные колумбарии
    #
    areas_hc = list()
    for horz_columbarium in horz_columbariums:
        areas_hc.append(Area.objects.get(cemetery__ugh=org, **horz_columbarium))
    q = q_dates & Q(area__in=areas_hc)
    print_xls(
        q,
        dir_out,
        file_id='horizontal_columbariums_with_id.xls',
        file_noid='horizontal_columbariums_without_id.xls',
        put_grave=False
    )

    # Вертикальные колумбарии
    #
    q = q_dates & \
        Q(cemetery__name__icontains=u'колумбарий')
    print_xls(
        q,
        dir_out,
        file_id='vertical_columbariums_with_id.xls',
        file_noid='vertical_columbariums_without_id.xls',
        put_grave=False
    )

    # Кладбища
    #
    q = q_dates & \
        ~Q(cemetery__name__icontains=u'колумбарий') & \
        ~Q(area__in=areas_hc)
    print_xls(
        q,
        dir_out,
        file_id='cemeteries_with_id.xls',
        file_noid='cemeteries_without_id.xls',
        put_grave=True
    )

def print_xls(q, dir_out, file_id, file_noid, put_grave=False):

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('output')
    set_xls_col_width(ws)
    n = 0
    for b in Burial.objects.filter(q & Q(deadman__ident_number__gt='')).order_by('pk'):
        line =get_line(b, put_grave)
        for i in range(len(line)):
            ws.write(n, i, line[i])
        n += 1
    wb.save(os.path.join(dir_out, file_id))
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('output')
    set_xls_col_width(ws)
    n = 0
    for b in Burial.objects.filter(q & Q(deadman__ident_number__lte='')).order_by('pk'):
        line =get_line(b, put_grave)
        for i in range(len(line)):
            ws.write(n, i, line[i])
        n += 1
    wb.save(os.path.join(dir_out, file_noid))
    
def get_line(b, put_grave=False):

    if b.deadman:
        id_= b.deadman.ident_number or ''
        last_name = b.deadman.last_name or '',
        first_name = b.deadman.first_name or '',
        middle_name = b.deadman.middle_name or '',
        birth_date = b.deadman.birth_date and b.deadman.birth_date.str_safe(format='d.m.y') or ''
    else:
        id_ = last_name = first_name = middle_name = birth_date = ''

    return (
        str(b.pk),
        id_,
        last_name,
        first_name,
        middle_name,
        birth_date,
        b.cemetery and b.cemetery.name or '-',
        b.area and b.area.name or '-',
        b.row or '',
        b.place_number and b.place_number or '-',
        put_grave and str(b.grave_number) or '',
    )

def set_xls_col_width(ws):
    ws.col(1).width = 4000
    ws.col(2).width = 4000
    ws.col(3).width = 4000
    ws.col(4).width = 4000

    ws.col(6).width = 4000

make_xlss(org, date_from, date_to, dir_out)
