# remove_cemetery.py
#
# Удалить кладбище с местами, усопшими, ответственными, заявителями-ФЛ...
#
# Запуск из ./manage.py shell :
# exec(open('../contrib/remove_cemetery.py').read())

import gc

from django.db.models.query_utils import Q
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User
from logs.models import Log
from burials.models import Cemetery, Burial, ExhumationRequest, BurialFiles, \
                           BurialComment, Area, AreaCoordinates, AreaPhoto, \
                           Place, PlaceStatus, PlacePhoto, PlaceStatusFiles, \
                           Grave
from persons.models import AlivePerson, DeadPerson

CEMETERY_NAME = 'Новое-213'
#
# Искажение во избежание случайного запуска процедуры
#
UGH_PK = -2

def main():
    cemetery = Cemetery.objects.get(ugh__pk=UGH_PK, name=CEMETERY_NAME)
    
    print('\nremove deadmen')
    i = 0
    for deadperson in DeadPerson.objects.filter(burial__cemetery=cemetery).iterator(chunk_size=100):
        i += 1 
        Burial.objects.filter(deadman=deadperson).update(deadman=None)
        #
        # Здесь и далее, если по одному удаляю строчки из модели,
        # значит функция модель.delete() вызывает еще методы,
        # что не происходит при model.objects.filter(...).delete()
        #
        deadperson.delete()
        if i % 1000 == 0:
            print_removed(i)
            gc.collect()
    print_removed(i)

    print('\nremove burial applicants- alivepersons')
    i = 0
    for aliveperson in AlivePerson.objects.filter(applied_burials__cemetery=cemetery).iterator(chunk_size=100):
        i += 1
        Burial.objects.filter(applicant=aliveperson).update(applicant=None)
        aliveperson.delete()
        if i % 1000 == 0:
            print_removed(i)
            gc.collect()
    print_removed(i)

    print('\nremove non-closed burial responsibles- alivepersons')
    i = 0
    for aliveperson in AlivePerson.objects.filter(responsible_burials__cemetery=cemetery).iterator(chunk_size=100):
        i += 1
        Burial.objects.filter(responsible=aliveperson).update(responsible=None)
        aliveperson.delete()
        if i % 1000 == 0:
            print_removed(i)
            gc.collect()
    print_removed(i)
    gc.collect()

    print('\nremove exhumationrequest applicants- alivepersons')
    i = 0
    for aliveperson in AlivePerson.objects.filter(exhumationrequest__burial__cemetery=cemetery).iterator(chunk_size=100):
        i += 1
        ExhumationRequest.objects.filter(applicant=aliveperson).update(applicant=None)
        aliveperson.delete()
        if i % 1000 == 0:
            print_removed(i)
            gc.collect()
    print_removed(i)
    gc.collect()

    print('\nremove exhumations')
    ExhumationRequest.objects.filter(burial__cemetery=cemetery).delete()

    print('\nremove burial files')
    i = 0
    for burialfile in BurialFiles.objects.filter(burial__cemetery=cemetery).iterator(chunk_size=100):
        i += 1
        burialfile.delete()
        if i % 1000 == 0:
            print_removed(i)
            gc.collect()
    print_removed(i)

    i = 0
    print('\nremove burials')
    ct = ContentType.objects.get(app_label="burials", model="burial")
    for burial in Burial.objects.filter(cemetery=cemetery).iterator(chunk_size=100):
        i += 1
        Log.objects.filter(ct=ct, obj_id = burial.pk).delete()
        BurialComment.objects.filter(burial=burial).delete()
        burial.delete()
        if i % 1000 == 0:
            print_removed(i)
            gc.collect()
    print_removed(i)

    print('\nremove place responsibles - alivepersons')
    i = 0
    for aliveperson in AlivePerson.objects.filter(place__cemetery=cemetery).iterator(chunk_size=100):
        i += 1
        Place.objects.filter(responsible=aliveperson).update(responsible=None)
        if not aliveperson.user:
            aliveperson.delete()
            if i % 1000 == 0:
                print_removed(i)
                gc.collect()
    print_removed(i)

    print('\nremove place photos')
    i = 0
    for ph in PlacePhoto.objects.filter(place__cemetery=cemetery).iterator(chunk_size=100):
        i += 1
        ph.delete()
        if i % 1000 == 0:
            print_removed(i)
            gc.collect()
    print_removed(i)

    print('\nremove places')
    PlaceStatusFiles.objects.filter(placestatus__place__cemetery=cemetery).delete()
    PlaceStatus.objects.filter(place__cemetery=cemetery).delete()
    ct = ContentType.objects.get(app_label="burials", model="place")
    i = 0
    for place in Place.objects.filter(cemetery=cemetery).iterator(chunk_size=100):
        i += 1
        Log.objects.filter(ct=ct, obj_id = place.pk).delete()
        Grave.objects.filter(place=place).delete()
        place.delete()
        if i % 1000 == 0:
            print_removed(i)
            gc.collect()
    print_removed(i)

    print('\nremove areas')
    AreaCoordinates.objects.filter(area__cemetery=cemetery).delete()
    AreaPhoto.objects.filter(area__cemetery=cemetery).delete()
    Area.objects.filter(cemetery=cemetery).delete()
    gc.collect()
    print('\nremove cemetery log recs')
    ct = ContentType.objects.get(app_label="burials", model="cemetery")
    Log.objects.filter(ct=ct, obj_id=cemetery.pk).delete()
    print('\nremove cemetery')
    cemetery.delete()

def print_removed(i):
    print("%7d removed" % (i or 0))

main()
