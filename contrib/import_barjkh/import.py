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
# - если дата рождения/смерти 31.12.1899 (или 01.01.1900), то это неизвестная дата
# - "наш" участок формируется как "их" сектор-участок (24-1). Если участок у них
#   е указан,то просто сектор (например, 52)

# Запуск из ./manage.py shell :
# execfile('../contrib/import_barjkh/import.py')

# Требования:
# -----------
# * python-xlrd

import datetime
import xlrd

from django.db import transaction

from users.models import Org, Profile
from burials.models import Cemetery, Burial

@transaction.commit_on_success
def main():
    # Получим пользователя из этой организации, первого по списку
    ugh = Org.objects.get(name=UGH_NAME)
    user = Profile.objects.filter(org=ugh).order_by('pk')[0].user
    cemetery, created = Cemetery.objects.get_or_create(
        ugh=ugh,
        name=UGH_NAME,
        defaults=dict(
            creator=user
    ))
    if not created and Burial.objects.filter(cemetery=cemetery).exists():
        raise Exception(u"Кладбище '%s' (pk=%s) у ОМС '%s' уже имеется и там есть захоронения!" % \
                (CEMETERY_NAME, cemetery.pk, UGH_NAME, ) )

    book = xlrd.open_workbook(IMPORT_XLS)
    sheet = book.sheet_by_index(0)
    for row in range(sheet.nrows)[1:]:
        for i in range(9):
            cell = sheet.cell(row, i)
            print row + 1, i, cell_value(cell), cell.ctype

def cell_value(cell):
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
        return  float(cell_value)
    else:
        return unicode(cell_value).strip()

main()