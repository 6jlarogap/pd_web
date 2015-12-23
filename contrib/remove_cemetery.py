# coding=utf-8
#
# remove_cemetery.py
#
# Удалить кладбище с местами, усопшими, ответственными, заявителями-ФЛ...
# Само кладбище оставить
#
# Запуск из ./manage.py shell :
# execfile('../contrib/remove_cemetery.py')

from django.db import transaction, IntegrityError
from django.db.models.query_utils import Q
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User
from logs.models import Log
from burials.models import Cemetery, Burial, ExhumationRequest, BurialFiles, \
                           BurialComment, Area, AreaCoordinates, AreaPhoto, \
                           Place, PlaceStatus, PlacePhoto, PlaceStatusFiles, \
                           Grave
from orders.models import Order
from persons.models import AlivePerson, DeadPerson

CEMETERY_NAME = u'Восточное'
#
# Искажение во избежание случайного запуска процедуры
#
UGH_PK = -2

@transaction.commit_on_success
def main():
    
    cemetery = Cemetery.objects.get(ugh__pk=UGH_PK, name=CEMETERY_NAME)
    
    print '\nremove deadmen'
    i = 0
    for deadperson in DeadPerson.objects.filter(burial__cemetery=cemetery).iterator():
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
            transaction.commit()
    print_removed(i)

    print '\nremove burial applicants- alivepersons'
    i = 0
    for aliveperson in AlivePerson.objects.filter(applied_burials__cemetery=cemetery).iterator():
        i += 1
        Burial.objects.filter(applicant=aliveperson).update(applicant=None)
        aliveperson.delete()
        if i % 1000 == 0:
            print_removed(i)
            transaction.commit()
    print_removed(i)

    print '\nremove non-closed burial responsibles- alivepersons'
    i = 0
    for aliveperson in AlivePerson.objects.filter(responsible_burials__cemetery=cemetery).iterator():
        i += 1
        Burial.objects.filter(responsible=aliveperson).update(responsible=None)
        aliveperson.delete()
        if i % 1000 == 0:
            print_removed(i)
            transaction.commit()
    print_removed(i)
    transaction.commit()

    print '\nremove exhumationrequest applicants- alivepersons'
    i = 0
    for aliveperson in AlivePerson.objects.filter(exhumationrequest__burial__cemetery=cemetery).iterator():
        i += 1
        ExhumationRequest.objects.filter(applicant=aliveperson).update(applicant=None)
        aliveperson.delete()
        if i % 1000 == 0:
            print_removed(i)
            transaction.commit()
    print_removed(i)
    transaction.commit()

    print '\nremove exhumations'
    ExhumationRequest.objects.filter(burial__cemetery=cemetery).delete()

    print '\nremove burial files'
    i = 0
    for burialfile in BurialFiles.objects.filter(burial__cemetery=cemetery).iterator():
        i += 1
        burialfile.delete()
        if i % 1000 == 0:
            print_removed(i)
            transaction.commit()
    print_removed(i)

    print '\nremove burial comments'
    BurialComment.objects.filter(burial__cemetery=cemetery).delete()

    i = 0
    print '\nremove burial logs / per burial'
    ct = ContentType.objects.get(app_label="burials", model="burial")
    for burial in Burial.objects.filter(cemetery=cemetery).iterator():
        i += 1
        Log.objects.filter(ct=ct, obj_id = burial.pk).delete()
        if i % 1000 == 0:
            print_removed(i)
            transaction.commit()
    print_removed(i)

    print '\nremove burials'
    Order.objects.filter(burial__cemetery=cemetery).update(burial=None)
    Burial.objects.filter(cemetery=cemetery).delete()

    print '\nremove graves'
    Grave.objects.filter(place__cemetery=cemetery).delete()

    print '\nremove place responsibles - alivepersons'
    i = 0
    for aliveperson in AlivePerson.objects.filter(place__cemetery=cemetery).iterator():
        i += 1
        Place.objects.filter(responsible=aliveperson).update(responsible=None)
        if not aliveperson.user:
            aliveperson.delete()
            if i % 1000 == 0:
                print_removed(i)
                transaction.commit()
    print_removed(i)

    print '\nremove place photos'
    i = 0
    for ph in PlacePhoto.objects.filter(place__cemetery=cemetery).iterator():
        i += 1
        ph.delete()
        if i % 1000 == 0:
            print_removed(i)
            transaction.commit()
    print_removed(i)

    print '\nremove place logs / per place'
    ct = ContentType.objects.get(app_label="burials", model="place")
    i = 0
    for place in Place.objects.filter(cemetery=cemetery).iterator():
        i += 1
        Log.objects.filter(ct=ct, obj_id = place.pk).delete()
        if i % 1000 == 0:
            print_removed(i)
            transaction.commit()
    print_removed(i)

    print '\nremove places'
    PlaceStatusFiles.objects.filter(placestatus__place__cemetery=cemetery).delete()
    PlaceStatus.objects.filter(place__cemetery=cemetery).delete()
    Place.objects.filter(cemetery=cemetery).delete()
    transaction.commit()

    print '\nremove areas'
    AreaCoordinates.objects.filter(area__cemetery=cemetery).delete()
    AreaPhoto.objects.filter(area__cemetery=cemetery).delete()
    Area.objects.filter(cemetery=cemetery).delete()
    transaction.commit()

    print '\nremove cemetery log recs'
    ct = ContentType.objects.get(app_label="burials", model="cemetery")
    Log.objects.filter(ct=ct, obj_id=cemetery.pk).delete()

def print_removed(i):
    print "%7d removed" % (i or 0)

main()
