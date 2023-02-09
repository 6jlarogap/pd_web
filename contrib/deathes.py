
# Обезличенные данные по годам жизни по УГХ

import datetime
from burials.models import Burial
from persons.models import DeadPerson

city = u'Минск'
ugh_pk = 2
output_csv = '/home/sev/d/deathes_minsk.csv'

max_age = 111
date_str_safe_format = 'd.m.y'

query = DeadPerson.objects.filter(
    birth_date__isnull=False,
    birth_date_no_day=False,
    birth_date_no_month=False,
    death_date__isnull=False,
    death_date_no_day=False,
    death_date_no_month=False,
    burial__cemetery__ugh__pk=ugh_pk,
    burial__status=Burial.STATUS_CLOSED,
    burial__annulated=False,
).order_by('birth_date', 'death_date').distinct()

count_invalid = 0
with open(output_csv, 'w') as f:
    for p in query.iterator(chunk_size=100):
        if p.death_date.year - p.birth_date.year > max_age or \
           p.death_date < p.birth_date:
            count_invalid += 1
            continue
        s = u'%(birth_date)s,%(death_date)s,%(city)s\n' % dict(
            birth_date = p.birth_date.str_safe(format=date_str_safe_format),
            death_date = p.death_date.str_safe(format=date_str_safe_format),
            city=city
        )
        f.write(s)

print ("Done. Invalid lifetime records excluded: %s" % count_invalid)
