# export_terminal.py
#
# Запуск: : ./manage.py export_terminal каталог_для_результатов
#
# Формирование .csv файлов для имеющихся терминалов на кладбищах

import sys, os, re
import pytils

from django import db
from django.db.models.query_utils import Q
from django.db import connection
from django.core.management.base import BaseCommand
from django.utils import translation

from burials.models import Place, Grave, Burial, Cemetery

# ПАРАМЕТРЫ ----------------------------------------------

# Кладбища, на которых установлены терминалы. На одном из из минских кладбищ
# может формироваться экспорт для нескольких "подкладбищ"

CEMETERIES = (
    dict(
        export='chizhovskoe_cemeteries',
        cemeteries=[
            35,         # Колумбарий, кладбище Чижовское
            33,         # Красная Слобода
            34,         # Лошица
            36,         # Малый Тростенец
            24,         # Чижовское
        ],
   ),
    dict(
        export='severnoe_cemeteries',
        cemeteries=[
            41,         # Колумбарий кладбища Северное-1
            42,         # Колумбарий кладбища Северное-2
            43,         # Колумбарий кладбища Северное-3
            29,         # Северное-1
            27,         # Северное-2
            30,         # Северное-3
            31,         # Цна
        ],
   ),
    dict(
        export='kolodischi_cemeteries',
        cemeteries=[28, ],
   ),
    dict(
        export='voennoe_cemeteries',
        cemeteries=[23, ],
   ),
    dict(
        export='vostochnoe_cemeteries',
        cemeteries=[
            2,              # Восточное
            7,              # Уручье
            37,             # Колумбарий Восточного
            ],
   ),
    dict(
        export='zapadnoe_cemeteries',
        cemeteries=[
            32,         # Западное
            44,         # Колумбарий кладбища Западное
        ],
   ),
)

# --------- ----------------------------------------------

# ОМС, на котором кладбища с терминалами (fool-proof)
#
UGH_PK = 2

# --------- ----------------------------------------------

class Command(BaseCommand):
    help = "Form export csv files for terminal at some cemeteries"

    def add_arguments(self, parser):
        parser.add_argument('export_path', type=str)

    def handle(self, *args, **kwargs):
        export_path = kwargs['export_path']

        cursor = connection.cursor()

        cursor.execute(
            "create temporary table tmp_terminal_export ("
                "last_name varchar(255),"
                "initials varchar(255),"
                "pk bigint,"
                "date varchar(255),"
                "cemetery_name varchar(255),"
                "area varchar(255),"
                "row_seat varchar(255)"
            ");"
        )
        cursor.execute(
            "create index tmp_terminal_export_idx ON "
            "tmp_terminal_export ("
                "last_name,"
                "initials,"
                "pk"
            ");"
        )
        translation.activate('ru')

        for cemetery_parms in CEMETERIES:
            print("Processing bundle of cemeteries for %s.csv" % cemetery_parms['export'])
            cursor.execute(
                "delete from tmp_terminal_export;"
            )
            cemeteries = []
            for cemetery_pk in cemetery_parms['cemeteries']:
                try:
                    cemetery = Cemetery.objects.get(ugh__pk=UGH_PK, pk=cemetery_pk)
                    cemeteries.append(cemetery)
                except Cemetery.DoesNotExist:
                    pass
            if not cemeteries:
                print("    !!! No cemeteries in system found for bundle %s" % cemetery_parms['export'])
                continue
            q = Q(
                    annulated=False,
                    status=Burial.STATUS_CLOSED,
                    cemetery__in=cemeteries,
                    deadman__isnull=False,
                ) & \
                ~Q(
                    burial_container=Burial.CONTAINER_BIO,
                )
            print("    %s: %s" % (
                "Cemetery" if len(cemeteries) == 1 else "Cemeteries",
                # Запуск из cron'a не терпит non-ASCII stdout output
                ", ".join([pytils.translit.slugify(cemetery.name) for cemetery in cemeteries]),
            ))
            burials = Burial.objects.filter(q).order_by(
                "deadman__last_name",
                "deadman__first_name",
                "deadman__middle_name",
                # pk добавлен, чтобы те, у которых совпадают ФИО,
                # при разных запусках сценария шли в одном порядке
                "pk",

            )
            for burial in burials.iterator(chunk_size=100):
                deadman = burial.deadman
                last_name = self.correct_str(deadman.last_name)
                last_name_lower = last_name and last_name.lower() or ''
                place = burial.place
                if last_name_lower and \
                   place and \
                   not 'неизвестен' in last_name_lower and \
                   not 'безфамильн' in last_name_lower and \
                   not 'резервирование' in last_name_lower and \
                   not re.search(r'^м[её]ртво\s*рожд[её]н', last_name_lower) and \
                   re.search(r'^[а-яёa-z\-]{2,}$', last_name_lower):
                    pk = str(deadman.pk)

                    last_name = last_name.upper()
                    last_name = last_name.replace('Ё', 'Е')
                    initials = ""
                    first_name = deadman.first_name and deadman.first_name.rstrip(".")
                    first_name = self.correct_str(first_name)
                    middle_name = deadman.middle_name and deadman.middle_name.rstrip(".")
                    middle_name = self.correct_str(middle_name)
                    if first_name:
                        if len(first_name) == 1:
                            initials = deadman.get_initials()
                        else:
                            initials = first_name
                            if middle_name:
                                initials = "%s %s" % (first_name, middle_name,)
                    if len(initials) > 30:
                        initials = "%s..." % initials[:28]
                    initials = initials or "-"
                    initials = initials.replace('Ё', 'Е')
                    initials = initials.replace('ё', 'е')

                    b_date = burial.fact_date
                    if b_date:
                        date = "%02d.%02d.%04d" % (b_date.day, b_date.month, b_date.year)
                    else:
                        date = "-"

                    area = self.correct_str(place.area.name)
                    if not area:
                        area = "-"

                    row = self.correct_str(place.row)
                    seat = self.correct_str(place.place)

                    cemetery_name = burial.cemetery and burial.cemetery.name or ''
                    if not cemetery_name:
                        cemetery_name = "-"
                    cemetery_name_lower = cemetery_name.lower()
                    if 'колумбари' not in cemetery_name_lower and \
                        'кладбищ' not in cemetery_name_lower:
                        cemetery_name = "Кладбище %s" % cemetery_name
                    if cemetery_name.startswith("Колумбарий") and \
                        'кладбищ' in cemetery_name:
                        cemetery_name = cemetery_name.replace("кладбище", "кл.")
                        cemetery_name = cemetery_name.replace("кладбища", "кл.")
                    if row and seat:
                        row_seat = "ряд %s, %s %s " % (
                            row,
                            place.place_name(),
                            seat
                        )
                    elif seat:
                        row_seat = "%s %s" % (
                            place.place_name(),
                            seat
                        )
                    elif row:
                        row_seat = "ряд %s" % (
                            row,
                        )
                    else:
                        row_seat = "-"

                    cursor.execute(
                        "insert into tmp_terminal_export ("
                            "last_name,"
                            "initials,"
                            "pk,"
                            "date,"
                            "cemetery_name,"
                            "area,"
                            "row_seat"
                        ") values("
                            "'%(last_name)s',"
                            "'%(initials)s',"
                            "%(pk)s,"
                            "'%(date)s',"
                            "'%(cemetery_name)s',"
                            "'%(area)s',"
                            "'%(row_seat)s'"
                        ");" % dict(
                            last_name=last_name,
                            initials=initials,
                            pk=pk,
                            date=date,
                            cemetery_name=cemetery_name,
                            area=area,
                            row_seat=row_seat,
                    ))
                    db.reset_queries()

            fname_export = os.path.join(export_path, "%s.csv" % cemetery_parms['export'])
            fname_export_partial = "%s.partial" % fname_export
            f = open(fname_export_partial, "wb")
            cursor.execute(
                "select "
                    "pk::text as pk,"
                    "last_name,"
                    "initials,"
                    "date,"
                    "cemetery_name,"
                    "area,"
                    "row_seat"
                    " "
                "from "
                    "tmp_terminal_export "
                "order by "
                    "last_name, initials, pk;"
            )
            columns = [col[0] for col in cursor.description]
            while True:
                row_ = cursor.fetchone()
                if not row_:
                    break
                row_ = dict(zip(columns, row_))
                columns_str = b''
                for c in columns:
                    columns_str += self.encode_(row_[c]) + b'\t'
                columns_str = columns_str[:-1]
                columns_str += b'\r\n'
                f.write(columns_str)
            f.close()
            os.rename(fname_export_partial, fname_export)

        translation.deactivate()

        cursor.execute(
            "drop table tmp_terminal_export;"
        )

    def correct_str(self, s):

        # Символы, которые могут в фамилии, имени, отч., по ошибке
        #
        BAD_CHAR_RE = r'\\|\"|\'\%'
        return re.sub(BAD_CHAR_RE, '', s)

    def encode_(self, s):
        """
        Кодирование, исправление ошибок в поле
        """

        ENCODING = 'cp1251'
        try:
            result = s.encode(ENCODING)
        except UnicodeEncodeError:
            result = b''
            for c in s:
                try:
                    next_char = c.encode(self.ENCODING)
                except UnicodeEncodeError:
                    next_char = '?'.encode(self.ENCODING)
                result += next_char
        return result

