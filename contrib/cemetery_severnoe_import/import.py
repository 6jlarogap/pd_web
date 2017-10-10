# -*- coding: utf-8 -*-

# Импорт кладбища "Северное" г.Минска из xls файла
# Исходный xls файл отсортировани по дате захоронения
#
# Поля:
#
#    0 (a)  регистрационный номер
#    1 (b)  ФИО
#    2 (с)  кладбище, может быть
#               Северное-1
#               Северное-2
#               Северное-3
#    3-5 (d-f)
#           Участок, ряд, место
#           Участок и/или место может отсутствовать, тогда заменяем на -
#    6 (g)  номер свидетельства о смерти, вставляем в комментарий захоронения
#    7 (h)  дата рождения
#    8 (i)  дата смерти
#    9 (j)  адрес, тоже в комментарий
#   10 (k)  примечания. Тоже в комментарии. Здесь ищем подзах или зах в сущ,
#           и на основании этого вносим или подзахоронение (при этом увеличиваем
#           номер могилы в месте на 1) или в существующую (в последнюю могилу места)
#   11 (l)  номер заказа, в комментарии
#   12 (l)  дата захоронения
#
#   Запускается как execfile() из ./manage.py shell
#   Путь к файлу импорта в INP_XLS

# --- " GLOBAL" vars ----------------------------------------------------

# Ид пользователя, который делает импорт.
# Делаем отрицательным, чтоб сдуру не запустить
#
PROFILE_ID = 43

INP_XLS = '/home/suprune20/musor/cemetery_severnoe_import/my_severnoe.xls'
# -----------------------------------------------------------------------

import sys, re, datetime
import xlrd

from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from users.models import Profile
from burials.models import Cemetery, Burial, BurialComment, Area, AreaPurpose, Place, Grave
from persons.models import DeadPerson
from logs.models import Log

from pd.utils import rus_to_lat
from pd.models import UnclearDate

C_IDENT_NUMBER = 0
C_FIO = 1
C_CEMETERY = 2
# Только такие кладбища там должны быть
cemeteries = {
    u"Северное-1": None,
    u"Северное-2": None,
    u"Северное-3": None
}
C_AREA = 3
C_ROW = 4
C_PLACE = 5
C_N_SVID = 6
C_DOB = 7
C_DOD = 8
C_ADDRESS = 9
C_PRIM = 10
C_N_ZAKAZA = 11
C_FACT_DATE = 12

@transaction.commit_on_success
def main():
    
    profile = Profile.objects.get(pk=PROFILE_ID)
    ugh = profile.org
    user = profile.user
    for c in cemeteries:
        cemeteries[c] = Cemetery.objects.get(ugh=ugh, name=c)
    area_purpose = AreaPurpose.objects.get(name='общественный')
    
    ct = ContentType.objects.get_for_model(Burial)

    rb = xlrd.open_workbook(INP_XLS)
    sheet = rb.sheet_by_index(0)
    for row in range(1, sheet.nrows):

        ident_number = rus_to_lat(cell_value(sheet.cell(row, C_IDENT_NUMBER))).strip()
        if not re.search(r'^[A-Za-z0-9]{10,}$', ident_number):
            ident_number = ''

        fio = cell_value(sheet.cell(row, C_FIO))
        fio = re.sub(r'[\s\.]+', ' ', fio).strip()
        fio = fio.split(' ')
        last_name = first_name = middle_name = ''
        if len(fio) > 2:
            middle_name = " ".join(fio[2:])
        if len(fio) > 1:
            first_name = fio[1]
        if len(fio) > 0:
            last_name = fio[0]
        deadman = DeadPerson.objects.create(
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            birth_date=make_unc_date(cell_value(sheet.cell(row, C_DOB)) or None),
            death_date=make_unc_date(cell_value(sheet.cell(row, C_DOD)) or None),
            ident_number=ident_number,
        )
        fact_date=make_unc_date(cell_value(sheet.cell(row, C_FACT_DATE)) or None)
        
        cemetery = cemeteries[cell_value(sheet.cell(row, C_CEMETERY)).strip()]

        c_prim = cell_value(sheet.cell(row, C_PRIM)).strip()
        c_n_svid = cell_value(sheet.cell(row, C_N_SVID)).strip()

        places_count = 2
        if re.search(ur'3\s*мест', c_prim, flags = re.IGNORECASE):
            places_count = 3
        if re.search(ur'4\s*мест', c_prim, flags = re.IGNORECASE):
            places_count = 4
        area, _created = Area.objects.get_or_create(
            cemetery=cemetery,
            name=cell_value(sheet.cell(row, C_AREA)).strip() or u'-',
            defaults = dict(
                availability=Area.AVAILABILITY_OPEN,
                purpose=area_purpose,
                places_count=places_count,
        ))
        place, _created = Place.objects.get_or_create(
            cemetery=cemetery,
            area=area,
            row = cell_value(sheet.cell(row, C_ROW)) or u'',
            place = cell_value(sheet.cell(row, C_PLACE)) or u'-',
        )

        burial_type = Burial.BURIAL_NEW
        if re.search(ur'подзах', c_prim, flags = re.IGNORECASE):
            burial_type = Burial.BURIAL_ADD
        elif re.search(ur'(подз|зах).+в.*сущ', c_prim, flags = re.IGNORECASE):
            burial_type = Burial.BURIAL_OVER

        burial_container = Burial.CONTAINER_COFFIN
        if re.search(ur'урн(а|ы)', c_prim, flags = re.IGNORECASE):
            burial_container = Burial.CONTAINER_URN
        if re.search(ur'урн(а|ы)', c_n_svid, flags = re.IGNORECASE):
            burial_container = Burial.CONTAINER_URN
        if burial_container == Burial.CONTAINER_URN:
            burial_type = Burial.BURIAL_OVER

        grave_number = 1
        if burial_type == Burial.BURIAL_ADD:
            for g in Grave.objects.filter(place=place).order_by('grave_number'):
                if Burial.objects.filter(grave=g).exists():
                    grave_number = grave_number + 1
                else:
                    break
        num_graves_to_create = grave_number
        if places_count > 2:
            num_graves_to_create = max(grave_number, places_count)
        place.get_or_create_graves(num_graves_to_create)
        grave = Grave.objects.get(place=place, grave_number=grave_number)

        burial = Burial.objects.create(
            burial_type=burial_type,
            burial_container=burial_container,
            source_type=Burial.SOURCE_TRANSFERRED,
            ugh=ugh,
            cemetery=cemetery,
            area=area,
            place=place,
            row=place.row,
            place_number=place.place,
            grave=grave,
            grave_number=grave_number,
            deadman=deadman,
            status=Burial.STATUS_CLOSED,
            changed_by=user,
            fact_date=fact_date,
            flag_no_applicant_doc_required = True,
        )

        c_address = cell_value(sheet.cell(row, C_ADDRESS)).strip()
        c_n_zakaza = cell_value(sheet.cell(row, C_N_ZAKAZA)).strip()
        comment = u""
        if c_prim:
            comment += u"Примечание: %s\n" % c_prim
        if c_address:
            comment += u"Адрес: %s\n" % c_address
        if c_n_svid:
            comment += u"Свидетельство: %s\n" % c_n_svid
        if c_n_zakaza:
            comment += u"Заказ: %s" % c_n_zakaza
        if comment:
            BurialComment.objects.create(
                burial=burial,
                creator=user,
                comment=u"Импорт\n%s" % comment,
            )
            Log.objects.create(
                user=user,
                ct=ct,
                obj_id=burial.pk,
                msg=u"Комментарий: (импорт)\n%s" % comment,
            )

        if row % 500 == 0:
            print ' %s records processed' % row
            transaction.commit()

    if row % 500 != 0:
        print ' %s records processed' % row
        transaction.commit()

def cell_value(cell):
    """
    Вернуть значение ячейки.
    
    Если дата/время, то datetime, иначе unicode- представление
    """
    cell_type = cell.ctype
    cell_value = cell.value

    if cell_type == xlrd.XL_CELL_DATE:
        try:
            dt_tuple = xlrd.xldate_as_tuple(cell_value, 0)
        except xlrd.xldate.XLDateError:
            # Эта ошибка будет и при дате <= 01.01.1900.
            # OK, это неизвестная дата
            return None
        return datetime.datetime(
            dt_tuple[0], dt_tuple[1], dt_tuple[2], 
            dt_tuple[3], dt_tuple[4], dt_tuple[5]
        )
    elif cell_type == xlrd.XL_CELL_NUMBER:
        # 52.0 -> 52
        return re.sub(r'\.0+$','', str(float(cell_value)))
    else:
        return unicode(cell_value).strip()

def make_unc_date(d):
    if isinstance(d, basestring):
        pd_bits = d.split('.')
        pd_bits.reverse()
        pd_bits = [b.isdigit() and int(b) or None for b in pd_bits]
        return UnclearDate(*pd_bits)
    return d


main()
