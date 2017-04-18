# coding=utf-8

# На Кладбищах Кальварийствое, Дворище, ... (Минск)
# обнаружились множество перенесенных захоронений
# в которых ФИО, участок, ряд, место, одинаковые,
# но такие лежат на разных кладбищах

# Запуск: из ./manage.py shell :
#   execfile('/path/to/this/file.py')
#
# NB:   чтобы загнать длинный вывод этого в файл, т.е. что бы выполнить
#
#       echo "execfile('/path/to/this/file.py')" | ./manage.py shell > 1.txt
#
# предварительно сделать в консоли:
#
#       export PYTHONIOENCODING=utf-8

# Профиль пользователя, у которого эти кладища собственные
#
PROFILE_PK = 37

# В этом каталоге лежат шахматки кальварийских кладбищ, там будем искать
# эти дубли
#
DIR_SHAHMATKI = '/home/suprune20/d/musor/calvar-shah'

import os, xlrd

from django.db import transaction, connection

from burials.models import Burial, Cemetery, Area, Place
from users.models import Profile

from pd.utils import dictfetchall

#   shahms['Кальварийское']
#       {
#           "1": {
#                   "rows":     {"1": 3, "2": 4, ...}           # название, строка xls
#                   "places":   {"1": 3, "2": 4, ...}           # название, колонка xls
#               }
#       }
#   shahms['Дворище']
#   ...

#   counter['Кальварийское'] : число попаданий в соотв. кладбище
#


def xls_to_str(cell):
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


def find_name(last_name, cemeteries, area, row, place):
    
    result = []
    for cemetery in cemeteries:
        try:
            xls_row = shahms[cemetery][area]['rows'][row]
            xls_col = shahms[cemetery][area]['places'][place]
            xls_cemetery = os.path.join(DIR_SHAHMATKI,u"%s.xls" % cemetery)
            rb = xlrd.open_workbook(xls_cemetery)
            sheet = rb.sheet_by_name(area)
            xls_fio = xls_to_str(sheet.cell(xls_row, xls_col)).lower()
            last_name = last_name.lower()
            if last_name in xls_fio:
                result.append(cemetery)
        except KeyError:
            pass

    return result

shahms = dict()
counter = dict()
count_one = 0
count_several = 0
count_doubles = 0

for f in os.listdir(DIR_SHAHMATKI):
    xls = os.path.join(DIR_SHAHMATKI, f)
    if os.path.isfile(os.path.join(DIR_SHAHMATKI, f)) and f.endswith('.xls'):
        f = f.rstrip('.xls')
        cemetery = unicode(f, "utf-8")
        shahms[cemetery] = dict()
        counter[cemetery] = 0
        try:
            rb = xlrd.open_workbook(xls)
        except:
            print "Failed to open %s" % xls
        for area in rb.sheet_names():
            shahms[cemetery][area] = dict(rows=dict(), places=dict())
            sheet = rb.sheet_by_name(area)
            for col in range(1, 1000):
                try:
                    place = xls_to_str(sheet.cell(1, col))
                    if place:
                        shahms[cemetery][area]['places'][place] = col
                except IndexError:
                    break
            for xls_row in range(2, sheet.nrows):
                row = xls_to_str(sheet.cell(xls_row, 0))
                if row:
                    shahms[cemetery][area]['rows'][row] = xls_row

#for cemetery in shahms:
    #print "\n", cemetery
    #areas = shahms[cemetery].keys()
    #areas.sort()
    #for area in areas:
        #print area, ":"
        #print 'places'
        #places = shahms[cemetery][area]['places'].keys()
        #places.sort()
        #for place in places:
            #print place, " : ", shahms[cemetery][area]['places'][place]
        #print 'rows'
        #rows = shahms[cemetery][area]['rows'].keys()
        #rows.sort()
        #for row in rows:
            #print row, " : ", shahms[cemetery][area]['rows'][row]


#for c in find_name(
    #u'Кожура',
    #[u'Дворище', u'Кальварийское', u'Козыревское', u'Масюковщина', u'Петровщина', u'Сухаревское'],
    #"1", "25", "23"
#):
    #print c

#exit()

cemeteries = Cemetery.editable_ugh_cemeteries(Profile.objects.get(pk=PROFILE_PK).user)
cemetery_pk_in_str = ", ".join([str(c.pk) for c in cemeteries])
req_str = '''
    SELECT
        "persons_baseperson"."last_name" as last_name,
        "persons_baseperson"."first_name" as first_name,
        "persons_baseperson"."middle_name" as middle_name,

        "burials_area"."name" as area,
        "burials_burial"."row" as row,
        "burials_burial"."place_number" as place_number

        FROM "persons_deadperson"

        INNER JOIN "burials_burial" ON ("persons_deadperson"."baseperson_ptr_id" = "burials_burial"."deadman_id")
        INNER JOIN "burials_area" ON ("burials_burial"."area_id" = "burials_area"."id")
        INNER JOIN "burials_cemetery" ON ("burials_burial"."cemetery_id" = "burials_cemetery"."id")
        INNER JOIN "persons_baseperson" ON ("persons_deadperson"."baseperson_ptr_id" = "persons_baseperson"."id")

        WHERE
            last_name > '' AND
            first_name > '' AND
            middle_name > '' AND
            "burials_burial"."annulated" = False AND
            "burials_burial"."status" = 'closed' AND
            "burials_cemetery"."id" IN (%(cemetery_pk_in_str)s) AND
            "burials_burial"."source_type" = 'transferred'

        GROUP BY
            last_name,
            first_name,
            middle_name,
            area,
            row,
            place_number

        HAVING Count(*) > 1

        ORDER BY
            last_name,
            first_name,
            middle_name
        ;
''' % dict(cemetery_pk_in_str=cemetery_pk_in_str)

cursor = connection.cursor()
cursor.execute(req_str)
for d in  dictfetchall(cursor):
    burials = Burial.objects.filter(
        source_type='transferred',
        status='closed',
        cemetery__in=cemeteries,
        deadman__last_name=d['last_name'],
        deadman__first_name=d['first_name'],
        deadman__middle_name=d['middle_name'],
        area__name=d['area'],
        row=d['row'],
        place_number=d['place_number'],
    )
    cc = []
    cc_str = u''
    c_names = []
    for b in burials.order_by('cemetery__name'):
        c = b.cemetery
        if c.pk not in cc:
            c_names.append(c.name)
            cc_str += (u"%s, " % c.name)
            cc.append(c.pk)
    cc_str = cc_str[:len(cc_str)-2]
    if len(cc) > 1:
        count_doubles += 1
        print d['last_name'], d['first_name'], d['middle_name'], u': уч. %s, ряд %s, м. %s' % \
            (d['area'], d['row'], d['place_number'])
        print "   В регистре на кладбищах:", cc_str
        r = find_name(d['last_name'], c_names, d['area'], d['row'], d['place_number'])
        for r_ in r:
            counter[r_] += 1
        if r:
            rr = ", ".join(r)
            print "      НАЙДЕН в шахматках: ", rr
            if len(r) > 1:
                print "      ВНИМАНИЕ: на нескольких кладбищах из шахматок"
                count_several += 1
            else:
                count_one += 1

print u"\nИТОГО \"двойников\": %s" % count_doubles
print u"\nПопаданий по кладбищам:"
for c in counter:
    if counter[c]:
        print u"    %s: %s" % (c, counter[c],)
print "\n"
print u"Попаданий в одно кладбище: %s" % count_one
print u"Попаданий в несколько кладбищ: %s" % count_several
