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

from django.db import transaction, connection

from burials.models import Burial, Cemetery, Area, Place
from users.models import Profile

from pd.utils import dictfetchall

def main():
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
        for b in burials.order_by('cemetery__name'):
            c = b.cemetery
            if c.pk not in cc:
                cc_str += (u"%s, " % c.name)
                cc.append(c.pk)
        cc_str = cc_str[:len(cc_str)-2]
        if len(cc) > 1:
            print d['last_name'], d['first_name'], d['middle_name'], u': уч. %s, ряд %s, м. %s' % \
                (d['area'], d['row'], d['place_number'])
            print "   ", cc_str
            print ''

main()
