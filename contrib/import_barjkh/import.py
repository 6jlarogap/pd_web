# coding=utf-8

# contrib/import_barjkh/import.py,

UGH_NAME = u'БарЖКХ'
CEMETERY_NAME = u'Русино'
IMPORT_ODS = '../contrib/import_barjkh/import.ods'

# Создать в организации UGH_NAME кладбище CEMETERY_NAME, импортировать
# данные по кладбищу из IMPORT_ODS
#
# Сама таблица IMPORT_ODS получена из двух MS Acess баз. В данные mydb.mdb
# добавлены три усопших ихз mydb2, отсутствовавшие в mydb. Поле ID_record
# для этих добавленных фамилий заполнено следующими по порядку номерами,
# ибо 3 добавленных захоронения были наиболее свежими.
#
# При импорте считалось:
#
# - учетный номер захоронения это поле ID_record
# - если дата рождения/смерти 31.12.1899, то это неизвестная дата
# - "наш" участок формируется как "их" сектор-участок (24-1). Если участок у них
#   е указан,то просто сектор (например, 52)

# Запуск из ./manage.py shell :
# execfile('../contrib/import_barjkh/import.py')

# Требования:
# -----------
# * python-odfpy

import sys,os

from odf.opendocument import load
from odf.opendocument import Spreadsheet
from odf.text import P
from odf.table import TableRow, TableCell

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

def ods_cell(cell):
    return "".join([unicode(data) for data in cell.getElementsByType(P)]).strip()

main()