# coding=utf-8
#
# comment_child_burials.py,
#
# Поставить комментарии "Детское захоронение" для захоронений
# из экспорта таковых из минской набивалки, 'export.csv'
# в домашнем каталоге пользователя
#
# Запуск из ./manage.py shell :
#  execfile('../contrib/comment_child_burials.py')

import os, csv, datetime

from django.db.models.query_utils import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from burials.models import Burial, BurialComment
from import_burials.models import UnicodeReader
from logs.models import Log

fname = os.path.join(os.getenv("HOME"), 'export.csv')
csv.register_dialect("4minsk", escapechar="\\", quoting=csv.QUOTE_ALL, doublequote=False)
csv_export_dialect = csv.get_dialect("4minsk")
io = open(fname, "r")
csvreader = UnicodeReader(io, dialect="4minsk")

(
    deadman_ln,
    deadman_fn,
    deadman_mn,
    fact_date,
    cemetery_name,
    area_name,
    row_name,
    place_number,
) = range(8)

UGH_PK = 2

user = User.objects.filter(profile__org__pk=UGH_PK).order_by('pk')[0]
ct = ContentType.objects.get_for_model(Burial)

comment_child_burial = u"Захоронение детское"
comment_child_burial_2 = u"Детское захоронение"

n = n_already = 0
for i, row in enumerate(csvreader):
    n += 1

    q = Q(ugh__pk=UGH_PK, source_type=Burial.SOURCE_TRANSFERRED)
    
    if row[deadman_ln] and row[deadman_ln] != u'*' and \
        row[deadman_ln].lower() != u'неизвестен':
        q &= Q(
            deadman__last_name__iexact=row[deadman_ln],
            deadman__first_name__iexact=row[deadman_fn],
            deadman__middle_name__iexact=row[deadman_mn],
        )
    else:
        q &= Q(deadman__isnull=True)

    if row[fact_date]:
        f_date=datetime.datetime.strptime(row[fact_date][:10], "%Y-%m-%d")
        q &= Q(
            fact_date__year=f_date.year,
            fact_date__month=f_date.month,
            fact_date__day=f_date.day,
        )
    else:
        q &= Q(fact_date__isnull=True)
    
    q &= Q(cemetery__name=row[cemetery_name])
    if row[area_name]:
        q &=Q(area__name = row[area_name])
    else:
        q &=Q(area__name = u'Без имени')
    q &= Q(row=row[row_name].strip())
    q &= Q(place_number=row[place_number].strip())
    
    try:
        burial = Burial.objects.get(q)
    except Burial.DoesNotExist:
        print 'Not found, rec No %d' % n
    except Burial.MultipleObjectsReturned:
        print 'Multiple burials found for rec No %d' % n

    q_comment = Q(comment__icontains=comment_child_burial) | \
                Q(comment__icontains=comment_child_burial_2)
    if BurialComment.objects.filter(burial=burial).filter(q_comment).exists():
        n_already += 1
    else:
        BurialComment.objects.create(
            burial=burial,
            creator=user,
            comment=comment_child_burial,
        )
        Log.objects.create(
            user=user,
            ct=ct,
            obj_id=burial.pk,
            msg=u"Комментарий: %s" % comment_child_burial,
            code='',
        )

    if n % 100 == 0:
        print 'Processed', n
if n % 100 != 0:
    print 'Processed', n
print "Already commented as child burial: %d" % n_already
io.close()
