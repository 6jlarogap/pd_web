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
    
    d_removed = "%7d removed"
    
    print '\nremove deadmen'
    i = 0
    for deadperson in DeadPerson.objects.filter(burial__cemetery=cemetery):
        i += 1 
        Burial.objects.filter(deadman=deadperson).update(deadman=None)
        deadperson.delete()
        if i % 1000 == 0:
            print d_removed % i
    print d_removed % i

    print '\nremove burial applicants- alivepersons'
    i = 0
    for aliveperson in AlivePerson.objects.filter(applied_burials__cemetery=cemetery):
        i += 1
        Burial.objects.filter(applicant=aliveperson).update(applicant=None)
        aliveperson.delete()
        if i % 1000 == 0:
            print d_removed % i
    print d_removed % i

    print '\nremove non-closed burial responsibles- alivepersons'
    i = 0
    for aliveperson in AlivePerson.objects.filter(responsible_burials__cemetery=cemetery):
        i += 1
        Burial.objects.filter(responsible=aliveperson).update(responsible=None)
        aliveperson.delete()
    print d_removed % i

    print '\nremove exhumationrequest applicants- alivepersons'
    i = 0
    for aliveperson in AlivePerson.objects.filter(exhumationrequest__burial__cemetery=cemetery):
        i += 1
        ExhumationRequest.objects.filter(applicant=aliveperson).update(applicant=None)
        aliveperson.delete()
    print d_removed % i

    print '\nremove exhumations'
    q = ExhumationRequest.objects.filter(burial__cemetery=cemetery)
    i = q.count()
    q.delete()
    print d_removed % i

    print '\nremove burial files'
    # По одному. Иначе не вызывается функция delete(), убирающая файлы
    # с диска
    i = 0
    for burialfile in BurialFiles.objects.filter(burial__cemetery=cemetery):
        i += 1
        burialfile.delete()
        if i % 1000 == 0:
            print d_removed % i
    print d_removed % i

    print '\nremove burial comments'
    q = BurialComment.objects.filter(burial__cemetery=cemetery)
    i = q.count()
    q.delete()
    print d_removed % i

    i = 0
    print '\nremove burials'
    Order.objects.filter(burial__cemetery=cemetery).update(burial=None)
    ct = ContentType.objects.get(app_label="burials", model="burial")
    for burial in Burial.objects.filter(cemetery=cemetery):
        i += 1
        Log.objects.filter(ct=ct, obj_id = burial.pk).delete()
        burial.delete()
        if i % 1000 == 0:
            print d_removed % i
    print d_removed % i

    print '\nremove graves'
    q = Grave.objects.filter(place__cemetery=cemetery)
    i = q.count()
    q.delete()
    print d_removed % i

    print '\nremove place responsibles - alivepersons'
    i = 0
    for aliveperson in AlivePerson.objects.filter(place__cemetery=cemetery):
        i += 1
        Place.objects.filter(responsible=aliveperson).update(responsible=None)
        if not aliveperson.user:
            aliveperson.delete()
            if i % 1000 == 0:
                print d_removed % i
    print d_removed % i

    print '\nremove places'
    PlacePhoto.objects.filter(place__cemetery=cemetery).delete()
    PlaceStatusFiles.objects.filter(placestatus__place__cemetery=cemetery).delete()
    PlaceStatus.objects.filter(place__cemetery=cemetery).delete()
    ct = ContentType.objects.get(app_label="burials", model="place")
    i = 0
    for place in Place.objects.filter(cemetery=cemetery):
        i += 1
        Log.objects.filter(ct=ct, obj_id = place.pk).delete()
        place.delete()
        if i % 1000 == 0:
            print d_removed % i
    print d_removed % i

    print '\nremove areas'
    AreaCoordinates.objects.filter(area__cemetery=cemetery).delete()
    AreaPhoto.objects.filter(area__cemetery=cemetery).delete()
    q = Area.objects.filter(cemetery=cemetery)
    i = q.count()
    q.delete()
    print d_removed % i

    print '\nremove cemetery log recs'
    ct = ContentType.objects.get(app_label="burials", model="cemetery")
    q = Log.objects.filter(ct=ct, obj_id=cemetery.pk)
    i = q.count()
    q.delete()
    print d_removed % i

main()
