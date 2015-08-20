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

from django.contrib.auth.models import User
from burials.models import Cemetery, Burial
from persons.models import AlivePerson, DeadPerson

CEMETERY_NAME = u'Восточное'
#
# Искажение во избежание случайного запуска процедуры
#
UGH_PK = -2

@transaction.commit_on_success
def main():
    
    cemetery = Cemetery.objects.get(ugh__pk=UGH_PK, name=CEMETERY_NAME)
    
    d_removed = " %d removed"
    
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
        Burial.objects.filter(responsible=aliveperson).update(applicant=None)
        aliveperson.delete()
    print d_removed % i

    print '\nremove exhumationrequest applicants- alivepersons'
    i = 0
    for aliveperson in AlivePerson.objects.filter(exhumationrequest__burial__cemetery=cemetery):
        i += 1
        ExhumationRequest.objects.filter(applicant=aliveperson).update(applicant=None)
        aliveperson.delete()
    print d_removed % i

    print '\remove exhumations'
    q = ExhumationRequest.objects.filter(burial__cemetery=cemetery)
    i = q.count()
    q.delete()
    print d_removed % i

    print '\remove burial files'
    q = BurialFiles.objects.filter(burial__cemetery=cemetery)
    i = q.count()
    q.delete()
    print d_removed % i

    print '\remove burial comments'
    for comment in BurialComment.objects.filter(burial__cemetery=cemetery)
    i = q.count()
    q.delete()
    print d_removed % i

    print '\remove burials'
    q = Burial.objects.filter(cemetery=cemetery)
    i = q.count()
    q.delete()
    print d_removed % i

    print '\remove graves'
    Grave.objects.filter(place__cemetery=cemetery)
    i = q.count()
    q.delete()
    print d_removed % i

    transaction.rollback()
    
main()
