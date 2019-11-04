# -*- coding: utf-8 -*-

#   fill_cemetery_coords.py,
#
#   Заполнить координаты кладбищ, у тех, у которых нет координат,
#   но есть адрес, хотя бы страна
#
# Запуск из ./manage.py shell :
# execfile('/path/to/fill_cemetery_coords.py')

from burials.models import Cemetery

count_all = count_changed = count_failed = 0
for cemetery in Cemetery.objects.all().order_by('ugh__name', 'name').iterator(chunk_size=100):
    count_all += 1
    address = cemetery.address
    print(cemetery.ugh, '---',  cemetery.name)
    if address and \
       address.country and \
       address.country.name and \
       (address.gps_y is None or address.gps_x is None):
        print(" - looking for coordinates")
        location = address.get_yandex_coords()
        if location:
            address.gps_y = location['latitude']
            address.gps_x = location['longitude']
            address.save()
            count_changed += 1
            print("   : coordinates put")
        else:
            print("   : failed to get coordinates")
            count_failed += 1
    else:
        print(" - no address or has already coordinates")
print("\nCemeteries total: %s, changed: %s, failed to get coordinates: %s" % (
    count_all,
    count_changed,
    count_failed,
))
