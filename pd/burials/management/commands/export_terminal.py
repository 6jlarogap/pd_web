# -*- coding: utf-8 -*-

# export_terminal.py
# ------------------

# Запуск: : ./manage.py export_terminal каталог_для_результатов

# Формирование .csv файлов для имеющихся терминалов на кладбищах

import sys, csv, os
import pytils

from django import db
from django.core.management.base import BaseCommand
from django.db.models.query_utils import Q

from burials.models import Place, Grave, Burial, Cemetery

# ПАРАМЕТРЫ ----------------------------------------------
# ОМС, на которых кладбища с терминалами
#
UGH_PK = 2

# Кладбища, на которых установлены терминалы. На одном из из минских кладбищ
# может формироваться экспорт для нескольких "подкладбищ"

CEMETERIES = (
    dict(
        export='voennoe',
        csv_kwargs=dict(delimiter="\t"),
        cemeteries=(u'Военное',),
        # put_cemetery = True,
        full_name_separate_line = True,
   ),
    dict(
        export='vostochnoe',
        #csv_kwargs=dict(delimiter=" ", quotechar='"', quoting=csv.QUOTE_ALL),
        #cemeteries=(
            #u'Восточное',
            #u'Уручье',
            #),
        #put_cemetery = True,

        csv_kwargs=dict(delimiter="\t"),
        cemeteries=(
            u'Восточное',
            u'Уручье',
            ),
        # put_cemetery = True,
        full_name_separate_line = True,
   ),
    dict(
        export='kolodischi',
        csv_kwargs=dict(delimiter="\t"),
        cemeteries=(u'Колодищи',),
        full_name_separate_line = False,
   ),
    dict(
        export='zapadnoe',
        csv_kwargs=dict(delimiter="\t"),
        cemeteries=(u'Западное',),
        full_name_separate_line = False,
   ),
)

# --------- ----------------------------------------------

class Command(BaseCommand):
    args = 'output_folder'
    help = "Form export csv files for terminal at some cemeteries"

    def handle(self, *args, **options):
        try:
            export_path=args[0]
        except IndexError:
            print "No export path specified as the parameter"
            quit()
        for cemetery_parms in CEMETERIES:
            print "Processing bundle of cemeteries for %s" % cemetery_parms['export']
            cemeteries = []
            for cemetery_name in cemetery_parms['cemeteries']:
                try:
                    cemetery = Cemetery.objects.get(ugh__pk=UGH_PK, name=cemetery_name)
                    cemeteries.append(cemetery)
                except Cemetery.DoesNotExist:
                    pass
            if not cemeteries:
                print "    !!! No cemeteries in system found for bundle %s" % cemetery_parms['export']
                continue
            csv.register_dialect(cemetery_parms['export'], **cemetery_parms['csv_kwargs'])
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
                last_name_lower = deadman.last_name and deadman.last_name.lower() or ''
                place = burial.place
                if last_name_lower and \
                   place and \
                   not u'неизвестен' in last_name_lower and \
                   not u'безфамильн' in last_name_lower:
                    pk = str(deadman.pk)

                    last_name = deadman.last_name.upper().encode('cp1251')
                    if cemetery_parms.get('full_name_separate_line'):
                        initials = u""
                        first_name = deadman.first_name and deadman.first_name.rstrip(u".")
                        middle_name = deadman.middle_name and deadman.middle_name.rstrip(u".")
                        if first_name:
                            if len(first_name) == 1:
                                initials = deadman.get_initials()
                            else:
                                initials = first_name
                                if middle_name:
                                    initials = u"%s %s" % (first_name, middle_name,)
                        if len(initials) > 30:
                            initials = u"%s..." % initials[:28]
                    else:
                        initials = deadman.get_initials()
                    initials = initials.encode('cp1251') or u"-"

                    b_date = burial.fact_date
                    if b_date:
                        date = "%02d.%02d.%04d" %(b_date.day, b_date.month, b_date.year)
                    else:
                        date = u"-"
                    area = place.area.name.encode('cp1251')
                    row = place.row.encode('cp1251')
                    seat = place.place.encode('cp1251')
                    columns = [pk, last_name, initials, date, area, row, seat]
                    if cemetery_parms.get('put_cemetery'):
                        cemetery = place.cemetery.name.encode('cp1251')
                        columns.append(cemetery)
                    writer.writerow(columns)
                    db.reset_queries()
            f.close()
            os.rename(fname_export_partial, fname_export)
