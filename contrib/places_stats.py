# Показать статистику по местам в соответствии с их статусом
#
# Запуск из ./manage.py shell :
#  exec(open('../contrib/places_stats.py').read())

UGH_PK = 2

from django.db.models import Count
from burials.models import Cemetery, Place

status_list = Place.STATUS_LIST
status_names = Place.status_dict()
total = dict()
l_count = []
for s in status_list:
    total[s] = 0
    l_count.append(Count('place__%s' % s))
cemeteries = Cemetery.objects.filter(ugh__pk=UGH_PK).order_by('name').annotate(*l_count)
for c in cemeteries:
    print(c.name)
    for s in status_list:
        count = getattr(c, 'place__%s__count' %s)
        if count:
            total[s] += count
            print('   ', status_names[s], ':', count)
print()
print('ВСЕГО:')
for s in status_list:
    print('   ', status_names[s], ':', total[s])
