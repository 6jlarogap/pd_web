# -*- coding: utf-8 -*-

# export_terminal.py
# ------------------

# Запуск: : ./manage.py export_terminal каталог_для_результатов

# Формирование .csv файлов для имеющихся терминалов на кладбищах

import sys, csv, os, re
import pytils

from django import db
from django.core.management.base import BaseCommand
from django.db.models.query_utils import Q
from django.utils import translation

from burials.models import Place, Grave, Burial, Cemetery

# ПАРАМЕТРЫ ----------------------------------------------

# Кладбища, на которых установлены терминалы. На одном из из минских кладбищ
# может формироваться экспорт для нескольких "подкладбищ"

CEMETERIES = (
    #dict(
        ## Имя csv файла
        ##
        #export='kolodischi',

        ## Список кладбищ/колумбариев, первичные ключи
        ##
        #cemeteries=[28, ],

        ## формат:
        ##   если False:
        ##       pk last_name first_name__middle_name date area row seat
        ##   если True:
        ##       pk last_name first_name__middle_name date cemetery area row_seat
        ##
        ## * разделитель полей: символ табуляции
        ## * seat: номер участка (места)
        ## * row_seat: 'ряд X, место Y' или 'место Y', где место может быть
        ##   'место' для колумбария или 'участок' для кладбищенского сектора
        ##
        #put_cemeteries=False,
   #),

    #dict(
        #export='voennoe',
        #cemeteries=[23, ],
        #put_cemeteries=False,
   #),

    #dict(
        #export='vostochnoe',
        #cemeteries=[
            #2,              # Восточное
            #7,              # Уручье
            #],
        #put_cemeteries=False,
   #),

    dict(
        export='vostochnoe_cemeteries',
        cemeteries=[
            2,              # Восточное
            7,              # Уручье
            37,             # Колумбарий Восточного
            ],
        put_cemeteries=True,
   ),

    dict(
        export='zapadnoe',
        cemeteries=[32, ],
        put_cemeteries=False,
   ),

    dict(
        export='zapadnoe_cemeteries',
        cemeteries=[
            32,         # Западное
            44,         # Колумбарий кладбища Западное
        ],
        put_cemeteries=True,
   ),
)

# --------- ----------------------------------------------

# ОМС, на котором кладбища с терминалами (fool-proof)
#
UGH_PK = 2

# Формат csv файла
#
CSV_KWARGS = dict(delimiter="\t")

# Символы, которые могут в фамилии, имени, отч., по ошибке
#
BAD_CHAR_RE = r'\\|\"|\''

# --------- ----------------------------------------------

class Command(BaseCommand):
    args = 'output_folder'
    help = "Form export csv files for terminal at some cemeteries"

    def handle(self, *args, **options):
        translation.activate('ru')

        try:
            export_path=args[0]
        except IndexError:
            print "No export path specified as the parameter"
            quit()
        for cemetery_parms in CEMETERIES:
            print "Processing bundle of cemeteries for %s.csv" % cemetery_parms['export']
            cemeteries = []
            for cemetery_pk in cemetery_parms['cemeteries']:
                try:
                    cemetery = Cemetery.objects.get(ugh__pk=UGH_PK, pk=cemetery_pk)
                    cemeteries.append(cemetery)
                except Cemetery.DoesNotExist:
                    pass
            if not cemeteries:
                print "    !!! No cemeteries in system found for bundle %s" % cemetery_parms['export']
                continue
            csv.register_dialect(cemetery_parms['export'], **CSV_KWARGS)
            fname_export = os.path.join(export_path, "%s.csv" % cemetery_parms['export'])
            fname_export_partial = "%s.partial" % fname_export
            f = open(fname_export_partial, "w")
            writer = csv.writer(f, cemetery_parms['export'])
            q = Q(
                    annulated=False,
                    status=Burial.STATUS_CLOSED,
                    cemetery__in=cemeteries,
                    deadman__isnull=False,
                ) & \
                ~Q(
                    burial_container=Burial.CONTAINER_BIO,
                )
            print "    %s: %s" % (
                u"Cemetery" if len(cemeteries) == 1 else u"Cemeteries",
                # Запуск из cron'a не терпит non-ASCII stdout output
                u", ".join([pytils.translit.slugify(cemetery.name) for cemetery in cemeteries]),
            )
            burials = Burial.objects.filter(q).order_by(
                "deadman__last_name",
                "deadman__first_name",
                "deadman__middle_name"
            )
            for burial in burials.iterator():
                deadman = burial.deadman
                last_name = re.sub(BAD_CHAR_RE, '', deadman.last_name)
                last_name_lower = last_name and last_name.lower() or ''
                place = burial.place
                if last_name_lower and \
                   place and \
                   not u'неизвестен' in last_name_lower and \
                   not u'безфамильн' in last_name_lower:
                    pk = str(deadman.pk)

                    last_name = last_name.upper().encode('cp1251')
                    initials = u""
                    first_name = deadman.first_name and deadman.first_name.rstrip(u".")
                    first_name = re.sub(BAD_CHAR_RE, '', first_name)
                    middle_name = deadman.middle_name and deadman.middle_name.rstrip(u".")
                    middle_name = re.sub(BAD_CHAR_RE, '', middle_name)
                    if first_name:
                        if len(first_name) == 1:
                            initials = deadman.get_initials()
                        else:
                            initials = first_name
                            if middle_name:
                                initials = u"%s %s" % (first_name, middle_name,)
                    if len(initials) > 30:
                        initials = u"%s..." % initials[:28]
                    initials = initials.encode('cp1251') or u"-"

                    b_date = burial.fact_date
                    if b_date:
                        date = "%02d.%02d.%04d" % (b_date.day, b_date.month, b_date.year)
                    else:
                        date = u"-"

                    area = re.sub(BAD_CHAR_RE, '', place.area.name)
                    if not area:
                        area = u"-"
                    area = area.encode('cp1251')

                    row = re.sub(BAD_CHAR_RE, '', place.row)
                    seat = re.sub(BAD_CHAR_RE, '', place.place)

                    if cemetery_parms.get('put_cemeteries'):
                        cemetery_name = burial.cemetery and burial.cemetery.name or ''
                        if not cemetery_name:
                            cemetery_name = u"-"
                        cemetery_name_lower = cemetery_name.lower()
                        if u'колумбари' not in cemetery_name_lower and \
                           u'кладбищ' not in cemetery_name_lower:
                            cemetery_name = u"Кладбище %s" % cemetery_name
                        if cemetery_name.startswith(u"Колумбарий") and \
                           u'кладбищ' in cemetery_name:
                            cemetery_name = cemetery_name.replace(u"кладбище", u"кл.")
                            cemetery_name = cemetery_name.replace(u"кладбища", u"кл.")
                        cemetery_name = cemetery_name.encode('cp1251')
                        if row and seat:
                            row_seat = u"ряд %s, %s %s " % (
                                row,
                                place.place_name(),
                                seat
                            )
                        elif seat:
                            row_seat = u"%s %s" % (
                                place.place_name(),
                                seat
                            )
                        elif row:
                            row_seat = u"ряд %s" % (
                                row,
                            )
                        else:
                            row_seat = u"-"
                        row_seat = row_seat.encode('cp1251')
                        columns = [pk, last_name, initials, date, cemetery_name, area, row_seat]
                    else:
                        if not row:
                            row = u"-"
                        row = row.encode('cp1251')
                        if not seat:
                            seat = u"-"
                        seat = seat.encode('cp1251')
                        columns = [pk, last_name, initials, date, area, row, seat]

                    writer.writerow(columns)
                    db.reset_queries()
            f.close()
            os.rename(fname_export_partial, fname_export)

        translation.deactivate()
