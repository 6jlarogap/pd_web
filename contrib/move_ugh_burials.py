# coding=utf-8
#
# move_ugh_burials.py
#

# Искажение во избежание случайного запуска процедуры
#
UGH_PK = -394

CEMETERY_SOURCE_PK = 80
CEMETERY_DEST_PK = 104

# Перенести захоронения, кроме тех, что добавлены по фото в организации 
# с первичным ключом UGH_PK из кладбища с первичным ключом CEMETERY_SOURCE_PK
# в кладбище с первичным ключом CEMETERY_DEST_PK
#
# Запуск из ./manage.py shell :
# execfile('../contrib/move_ugh_burials')

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from logs.models import Log, LogOperation
from burials.models import Cemetery, Burial, Area, Place, Grave, AreaPurpose

@transaction.commit_on_success
def main():
    
    cemetery_source = Cemetery.objects.get(ugh__pk=UGH_PK, pk=CEMETERY_SOURCE_PK)
    cemetery_dest = Cemetery.objects.get(ugh__pk=UGH_PK, pk=CEMETERY_DEST_PK)

    ct = ContentType.objects.get(app_label="burials", model="burial")
    area_purpose = AreaPurpose.objects.get(name=u'общественный')

    pks = list()
    for b in Burial.objects.filter(cemetery=cemetery_source):
        if not Log.objects.filter(
            ct=ct,
            obj_id=b.pk,
            operation=LogOperation.BURIAL_PHOTO_PROCESSED
        ).exists():
            pks.append(b.pk)
    for pk in pks:
        b = Burial.objects.get(pk=pk)
        if not b.is_exhumated():
            area, created_ = Area.objects.get_or_create(
                cemetery=cemetery_dest,
                name=b.area.name,
                defaults = dict(availability=Area.AVAILABILITY_OPEN,
                    purpose=area_purpose,
                    places_count=b.place and b.place.area.places_count,
            ))
            row = b.row
            place_number = b.place_number
            Burial.objects.filter(pk=pk).update(
                cemetery=cemetery_dest,
                area=area,
            )
            if b.is_closed():
                place, created_ = Place.objects.get_or_create(
                    cemetery=cemetery_dest,
                    area=area,
                    row=row,
                    place=place_number,
                )
                grave = place.get_or_create_graves(b.grave_number or 1)
                Burial.objects.filter(pk=pk).update(
                    place=place,
                    grave=grave,
                )
            print u"Burial %s transferred" % pk
main()
