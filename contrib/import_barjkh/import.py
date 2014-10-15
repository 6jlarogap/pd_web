# coding=utf-8

# contrib/import_barjkh/import.py,

UGH_NAME = u'БарЖКХ'
CEMETERY_NAME = u'Русино'
IMPORT_XLS = '../contrib/import_barjkh/import.xls'

# Создать в организации UGH_NAME кладбище CEMETERY_NAME, импортировать
# данные по кладбищу из IMPORT_XLS
#
# Сама таблица IMPORT_XLS получена из двух MS Acess баз. В данные mydb.mdb
# добавлены три усопших ихз mydb2, отсутствовавшие в mydb. Поле ID_record
# для этих добавленных фамилий заполнено следующими по порядку номерами
#
# При импорте считалось:
#
# - учетный номер захоронения это поле ID_record
# - импортируемый xls отсортирован по дате смерти, затем по ID_record,
#   чтоб определить, кто в могилу с каким номером захоронен
# - если дата рождения/смерти 01.01.1900, то это неизвестная дата
# - "наш" участок формируется как "их" сектор-участок (24-1). Если участок у них
#   не указан,то просто сектор (например, 52)
# - места на кладбище состоят из одной (колонка I в xls == "Одинарный"),
#   двух ("Двойной") или трёх ("Семейный") могил
# - * 1-го покойника в месте "кладем" в 1-ю могилу,
#     2-го -- во 2-ю, если место двойное или семейное, иначе в 1-ю
#     3-го -- в  3-ю, если место семейное, иначе во 2-ю в двойном месте
#             или в 1-ю в одинарном
#     4-го и т.д. -- в последнюю из имеющихся могил в месте
# - фактическая дата захоронения не проставляется. Не будем гадать

# Запуск из ./manage.py shell :
# execfile('../contrib/import_barjkh/import.py')

# Требования:
# -----------
# * python-xlrd

import datetime, re
import xlrd

from django.db import transaction

from users.models import Org, Profile
from burials.models import Cemetery, Burial, Area, AreaPurpose, Place, Grave

# Колонки импортируемого xls, начиная с 0:
#
(C_ACCOUNT_NUMBER, 
 C_FIO,
 C_DOB,
 C_DOD,
 C_SECTOR,
 C_AREA,
 C_ROW,
 C_PLACE,
 C_PLACE_TYPE
) = range(9)

@transaction.commit_on_success
def main():
    # Получим пользователя из этой организации, первого по списку
    ugh = Org.objects.get(name=UGH_NAME)
    user = Profile.objects.filter(org=ugh).order_by('pk')[0].user
    print 'Creating cemetery'
    cemetery, _created = Cemetery.objects.get_or_create(
        ugh=ugh,
        name=CEMETERY_NAME,
        defaults=dict(
            creator=user,
            time_begin=datetime.time(9, 0),
            time_end=datetime.time(17, 0),
    ))
    if not _created and Place.objects.filter(cemetery=cemetery).exists():
        raise Exception("Cemetery exists and has already burial places!")

    if not _created:
        print 'Cemetery exists but has no burial places'
    book = xlrd.open_workbook(IMPORT_XLS)
    sheet = book.sheet_by_index(0)
    # 1-й проход:
    # Формируем места и могилы. Сразу на этом проходе привязывать могилы
    # к захоронениям нельзя, ибо в импортируемом xls бывае, что одно и то же
    # место помечено и как двойное, и как одинарное.
    #
    print '1-st pass: creating areas, places, graves'
    area_purpose, _created = AreaPurpose.objects.get_or_create(name='общественный')
    place_length_1 = 1.50
    place_length_2 = 2.60
    place_length_3 = 4.50
    place_width = 2.30

    for row in range(sheet.nrows)[1:]:
        s_area = cell_value(sheet.cell(row, C_SECTOR))
        s_their_area = cell_value(sheet.cell(row, C_AREA))
        if s_their_area:
            s_area = u"%s-%s" % (s_area, s_their_area, )
        area, _created = Area.objects.get_or_create(
            cemetery=cemetery,
            name=s_area,
            defaults = dict(
                availability=Area.AVAILABILITY_OPEN,
                purpose=area_purpose,
                places_count=1,
        ))
        place, _created = Place.objects.get_or_create(
            cemetery=cemetery,
            area=area,
            row = cell_value(sheet.cell(row, C_ROW)),
            place = cell_value(sheet.cell(row, C_PLACE)),
            defaults = dict(
                place_length=place_length_1,
                place_width=place_width,
        ))
        s_type = cell_value(sheet.cell(row, C_PLACE_TYPE)).lower()
        if s_type.startswith(u'двойн'):
            s_type_n = 2
        elif s_type.startswith(u'семейн'):
            s_type_n = 3
        else:
            s_type_n = 1
        place.get_or_create_graves(s_type_n)
        grave_count = place.get_graves_count()
        if grave_count == 3 and place.place_length < place_length_3:
            place.place_length = place_length_3
            place.save()
        if grave_count == 2 and place.place_length < place_length_2:
            place.place_length = place_length_2
            place.save()
        if row % 500 == 0:
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

main()