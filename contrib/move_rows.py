# Перемещение мест/захоронений с одного участка на другой
#
# Ялта пгт Ливадия мемориальное
#   участок "4", ряды под номерами 6 7  8  9  и  10
#   переместить в участок "5" со всеми данными содержащимися в них;
#   с сохранением номеров рядов

# Fake ugh pk, чтобы не запустили сдуру
#

UGH_PK = -394
CEMETERY_NAME = 'Ялта пгт Ливадия мемориальное'
AREA_OLD_NAME = '4'
AREA_NEW_NAME = '5'
ROWS = ('6', '7', '8', '9', '10',)

from burials.models import Cemetery, Area, Place, Burial

cemetery = Cemetery.objects.get(ugh__pk=UGH_PK, name=CEMETERY_NAME)
area_old = Area.objects.get(cemetery=cemetery, name=AREA_OLD_NAME)
area_new = Area.objects.get(cemetery=cemetery, name=AREA_NEW_NAME)

print('Check places\' existence at the given rows')
for row in ROWS:
    if Place.objects.filter(cemetery=cemetery, area=area_old, row=row).exists():
        print ('    row', row, 'OK')
    else:
        print ('    row', row, 'no places!. EXIT')
        quit()

print('Move places of the given rows from area %s to area %s' % (
    AREA_OLD_NAME, AREA_NEW_NAME
))
for row in ROWS:
    print('    row', row)
    places_pks = []
    for place in Place.objects.filter(cemetery=cemetery, area=area_old, row=row):
        places_pks.append(place.pk)
    for place_pk in places_pks:
        place = Place.objects.get(pk=place_pk)
        print('        ', str(place))
        place.area = area_new
        place.save()
        print('        ', '    area changed ->')
        print('        ', str(place))
        print('        ', '    place\'s burials:')
        count = 0
        for b in Burial.objects.filter(place=place):
            b.area = area_new
            b.save()
            count += 1
        print('        ', '    ', count, 'burials changed')
        

