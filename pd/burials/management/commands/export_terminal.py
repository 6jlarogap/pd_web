# -*- coding: utf-8 -*-

# export_terminal.py
# ------------------

# Запуск: : ./manage.py export_terminal

# Формирование .csv файлов для имеющихся терминалов на кладбищах

import sys, csv

from django.core.management.base import NoArgsCommand
from burials.models import Place, Grave, Burial, Cemetery

# ПАРАМЕТРЫ ----------------------------------------------
# ОМС, на которых кладбища с терминалами
#
UGH_PK = 2

# Кладбища, на которых установлены терминалы. На одном из из минских кладбищ
# может формироваться экспорт для нескольких "подкладбищ"

CEMETERIES = (
    dict(
        export='vostochnoe',
        csv_kwargs=dict(delimiter=" ", quotechar='"', quoting=csv.QUOTE_ALL),
        cemeteries=(u'Восточное', u'Уручье',),
   ),
    dict(
        export='voennoe',
        csv_kwargs=dict(delimiter="\t"),
        cemeteries=(u'Военное',),
   ),
    dict(
        export='kolodischi',
        csv_kwargs=dict(delimiter="\t"),
        cemeteries=(u'Колодищи',),
   ),
    dict(
        export='zapadnoe',
        csv_kwargs=dict(delimiter="\t"),
        cemeteries=(u'Западное',),
   ),
)

EXPORT_PATH = '/home/sev'

# --------- ----------------------------------------------

class Command(NoArgsCommand):
    help = "Form export csv files for terminal at some cemeteries"

    def handle_noargs(self, **options):
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
            f = open("%s/%s" % (EXPORT_PATH, cemetery_parms['export'],), "w")
            writer = csv.writer(f, cemetery_parms['export'])
            f.close()

