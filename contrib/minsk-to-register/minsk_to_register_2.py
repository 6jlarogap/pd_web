# -*- coding: utf-8 -*-

# minsk_to_register_2.py
#
# Записать в домашний каталог пользователя 8 файлов xls
#
#   - захоронения берем с 2013г.
#   - склепов у нас нет, пропускаем, точнее формируем пустые файлы
#
# Запуск из ./manage.py shell :
# execfile('/path/to/minsk_to_register_2.py')

import os, datetime, xlwt

from django.db.models.query_utils import Q

from burials.models import Area, Burial
from users.models import Org

dir_out = os.getenv("HOME")
date_from = datetime.date(2013, 1, 1)
date_to = datetime.date(2013, 4, 30)
org = Org.objects.get(pk=2)

SEPARATOR = ';'
EMPTY_FIELD = u'-'
DATE_FORMAT='%d.%m.%Y'

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
        fact_date__isnull=False,
        fact_date_no_day=False,
        fact_date_no_month=False,
        deadman__last_name__gt=u'',
        deadman__first_name__gt=u'',
        fact_date__gte=date_from,
        fact_date__lte=date_to,
    )

    # Горизонтальные колумбарии
    #
    areas_hc = list()
    for horz_columbarium in horz_columbariums:
        areas_hc.append(Area.objects.get(cemetery__ugh=org, **horz_columbarium))
    q = q_dates & Q(area__in=areas_hc)
    mode_cemetery = 3
    print_xls(
        q,
        dir_out,
        mode_cemetery=mode_cemetery,
        file_id=fname_(mode_cemetery, with_id=True),
        file_noid=fname_(mode_cemetery, with_id=False),
        put_grave=False
    )

    # Вертикальные колумбарии
    #
    q = q_dates & \
        Q(cemetery__name__icontains=u'колумбарий')
    mode_cemetery = 2
    print_xls(
        q,
        dir_out,
        mode_cemetery=mode_cemetery,
        file_id=fname_(mode_cemetery, with_id=True),
        file_noid=fname_(mode_cemetery, with_id=False),
        put_grave=False
    )

    # Кладбища
    #
    q = q_dates & \
        ~Q(cemetery__name__icontains=u'колумбарий') & \
        ~Q(area__in=areas_hc)
    mode_cemetery = 1
    print_xls(
        q,
        dir_out,
        mode_cemetery=mode_cemetery,
        file_id=fname_(mode_cemetery, with_id=True),
        file_noid=fname_(mode_cemetery, with_id=False),
        put_grave=True
    )

def fname_(mode_cemetery, with_id):

    with_id_str = 'with_id' if with_id else 'without_id'
    date_from_str = datetime.datetime.strftime(date_from, '%Y%m%d')
    date_to_str = datetime.datetime.strftime(date_to, '%Y%m%d')
    dt_now_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')

    fname = u'registry-%s-%s-from-%s-to-%s-at-%s.xls' % (
        mode_cemetery,
        with_id_str,
        date_from_str,
        date_to_str,
        dt_now_str, 
    )
    return fname

def print_xls(q, dir_out, mode_cemetery, file_id, file_noid, put_grave=False):

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('output')
    set_xls_col_width(ws)
    n = 0
    for b in Burial.objects.filter(q & Q(deadman__ident_number__gt='')).order_by('fact_date'):
        line = get_line(b, mode_cemetery, put_grave)
        if line:
            for i in range(len(line)):
                ws.write(n, i, line[i])
            n += 1
    wb.save(os.path.join(dir_out, file_id))
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('output')
    set_xls_col_width(ws)
    n = 0
    for b in Burial.objects.filter(q & Q(deadman__ident_number__lte='')).order_by('fact_date'):
        line = get_line(b, mode_cemetery, put_grave)
        if line:
            for i in range(len(line)):
                ws.write(n, i, line[i])
            n += 1
    wb.save(os.path.join(dir_out, file_noid))
    
def get_line(b, mode_cemetery, put_grave):

    id_= b.deadman.ident_number or ''
    full_name = check_names(b.deadman)

    if full_name:
        result = (
            str(mode_cemetery),
            id_,
            full_name[0],
            full_name[1],
            full_name[2],
            datetime.datetime.strftime(b.fact_date.d, DATE_FORMAT),
            b.cemetery and b.cemetery.code or '-',
            b.area and b.area.name or '-',
            b.row or '-',
            b.place_number and b.place_number or '-',
            put_grave and str(b.grave_number) or '',
        )
    else:
        result = None
    return result

def set_xls_col_width(ws):
    ws.col(2).width = 4000
    ws.col(3).width = 4000
    ws.col(4).width = 4000

    ws.col(6).width = 4000

def correct_name(name):
    return name.replace(SEPARATOR, u'').strip()

def check_names(deadman):
    """
    Убрать из фио ';'. Пустое отчество -> '-'
    """
    result = None
    last_name = first_name = middle_name = u''
    if deadman:
        last_name = correct_name(deadman.last_name)
        if last_name == EMPTY_FIELD:
            last_name = u''
        first_name = correct_name(deadman.first_name)
        if first_name == EMPTY_FIELD:
            first_name = u''
        middle_name = correct_name(deadman.middle_name)
        if not middle_name:
            middle_name = EMPTY_FIELD
    if last_name and first_name:
        result = (last_name, first_name, middle_name)
    return result

make_xlss(org, date_from, date_to, dir_out)
