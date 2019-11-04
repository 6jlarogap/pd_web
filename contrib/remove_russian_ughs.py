# coding=utf-8
#
# remove_russian_ughs.py,
#
# Подготовить базу данных для белорусского сайта. В нем не должно быть
# российских ОМС и организаций с пользователями, завязанных на эти ОМС
#
# Запуск из ./manage.py shell :
#  execfile('/path/to/this/file.py')

import sys

from django.db import transaction, IntegrityError
from django.db.models.query_utils import Q

from django.contrib.auth.models import User
from users.models import Org, ProfileLORU, Profile, Dover, OrgCertificate, CustomerProfile
from logs.models import Log
from burials.models import Cemetery, CemeteryCoordinates, Area, AreaCoordinates, \
                           Place, PlaceSize, PlacePhoto, Grave, \
                           Burial, BurialFiles, Reason, ExhumationRequest, \
                           BurialComment, PlaceStatus, AreaPhoto, PlaceStatusFiles
from orders.models import Order, OrderItem, ServiceItem, OrgService, OrgServicePrice, \
                          OrderComment, ResultFile
from persons.models import DeadPerson, AlivePerson, CustomPlace

# Искажаю во избежание случайного запуска процедуры
#
CURRENCY_CODE = '---RUR---'

def main():
    
    ugh_qs = Q(type=Org.PROFILE_UGH, currency__code=CURRENCY_CODE)
    org_qs = Q(currency__code=CURRENCY_CODE)

    print('Looking for russian orgs...')
    for org in Org.objects.filter(org_qs).distinct():
        print(org)
        ProfileLORU.objects.filter(loru=org).delete()

        print('removing orderItems')
        OrderItem.objects.filter(
            Q(order__loru=org) | \
            Q(order__loru__isnull=True) | \
            Q(order__applicant_organization=org) | \
            Q(order__agent__org=org) | \
            Q(order__dover__agent__org=org) | Q(order__dover__target_org=org) | \
            Q(order__burial__ugh=org)
        ).delete()
        OrgServicePrice.objects.filter(orgservice__org=org).delete()
        OrgService.objects.filter(org=org).delete()
        ServiceItem.objects.filter(orgservice__org=org).delete()
        transaction.commit()

        print('removing order applicants- alivepersons')
        i = 0
        for aliveperson in AlivePerson.objects.filter(
                Q(order__loru=org) | \
                Q(order__burial__ugh=org)
            ).iterator(chunk_size=100):
            i += 1 
            Order.objects.filter(applicant=aliveperson).update(applicant=None)
            aliveperson.delete()
            if i % 1000 == 0:
                print("%d order applicants removed" % i)
        transaction.commit()

        print('removing orders')
        OrderComment.objects.filter(order__loru=org).delete()
        ResultFile.objects.filter(order__loru=org).delete()
        Order.objects.filter(
            Q(loru=org) | \
            Q(loru__isnull=True) | \
            Q(applicant_organization=org) | \
            Q(agent__org=org) | \
            Q(dover__agent__org=org) | Q(dover__target_org=org) | \
            Q(burial__ugh=org)
        ).delete()
        transaction.commit()

        print('Marking dependent fields in Burials as None')
        Burial.objects.filter(applicant_organization=org).update(applicant_organization=None)
        Burial.objects.filter(agent__org=org).update(agent=None)
        Burial.objects.filter(Q(dover__agent__org=org) | Q(dover__target_org=org)).update(dover=None)
        ExhumationRequest.objects.filter(applicant_organization=org).update(applicant_organization=None)
        ExhumationRequest.objects.filter(agent__org=org).update(agent=None)
        ExhumationRequest.objects.filter(Q(dover__agent__org=org) | Q(dover__target_org=org)).update(dover=None)
        Burial.objects.filter(loru=org).update(loru=None)
        Burial.objects.filter(loru_agent__org=org).update(loru_agent=None)
        Burial.objects.filter(Q(loru_dover__agent__org=org) | Q(loru_dover__target_org=org)).update(loru_dover=None)
        transaction.commit()

        Burial.objects.filter(changed_by__profile__org=org).update(changed_by=None)
        print('removing dovers')
        Dover.objects.filter(Q(agent__org=org) | Q(target_org=org)).delete()
        if org.type != Org.PROFILE_UGH:
            remove_org(org)
            print('Org deleted')
        transaction.commit()

    print('Looking for russian UGHs...')
    for ugh in Org.objects.filter(ugh_qs):
        print(ugh)
        print('removing deadmen in burial')
        i = 0
        for deadperson in DeadPerson.objects.filter(burial__ugh=ugh).iterator(chunk_size=100):
            i += 1 
            Burial.objects.filter(deadman=deadperson).update(deadman=None)
            deadperson.delete()
            if i % 1000 == 0:
                print("%d deadmen removed" % i)
        print('removing burial applicants- alivepersons')
        transaction.commit()
        i = 0
        for aliveperson in AlivePerson.objects.filter(applied_burials__ugh=ugh).iterator(chunk_size=100):
            i += 1 
            Burial.objects.filter(applicant=aliveperson).update(applicant=None)
            aliveperson.delete()
            if i % 1000 == 0:
                print("%d burial applicants removed" % i)
        print('removing non-closed burial responsibles- alivepersons')
        transaction.commit()
        for aliveperson in AlivePerson.objects.filter(responsible_burials__ugh=ugh).iterator(chunk_size=100):
            Burial.objects.filter(responsible=aliveperson).update(applicant=None)
            aliveperson.delete()
        print('removing exhumationrequest applicants- alivepersons')
        for aliveperson in AlivePerson.objects.filter(exhumationrequest__burial__ugh=ugh).iterator(chunk_size=100):
            ExhumationRequest.objects.filter(applicant=aliveperson).update(applicant=None)
            aliveperson.delete()
        transaction.commit()

        print('removing burials')
        ExhumationRequest.objects.filter(burial__ugh=ugh).delete()
        BurialFiles.objects.filter(burial__ugh=ugh).delete()
        BurialComment.objects.filter(burial__ugh=ugh).delete()
        Burial.objects.filter(ugh=ugh).delete()
        transaction.commit()
        print('removing graves')
        Grave.objects.filter(place__cemetery__ugh=ugh).delete()
        transaction.commit()

        print('removing place responsibles- alivepersons')
        i = 0
        for aliveperson in AlivePerson.objects.filter(place__cemetery__ugh=ugh).iterator(chunk_size=100):
            i += 1
            Place.objects.filter(responsible=aliveperson).update(responsible=None)
            try:
                user = aliveperson.user
            except User.DoesNotExist:
                user = None
            aliveperson.delete()
            if user:
                CustomPlace.objects.filter(user=user).delete()
                AlivePerson.objects.filter(user=user).update(user=None)
                customerprofile = user.customerprofile
                customerprofile.user = None
                customerprofile.save()
                Log.objects.filter(user=user).delete()
                user.delete()
                customerprofile.delete()
            if i % 1000 == 0:
                print("%d place responsibles removed" % i)
                transaction.commit()

        print('removing places')
        PlaceSize.objects.filter(org=ugh).delete()
        PlacePhoto.objects.filter(place__cemetery__ugh=ugh).delete()
        PlaceStatusFiles.objects.filter(placestatus__place__cemetery__ugh=ugh).delete()
        PlaceStatus.objects.filter(place__cemetery__ugh=ugh).delete()
        Place.objects.filter(cemetery__ugh=ugh).delete()
        transaction.commit()

        print('removing areas')
        AreaPhoto.objects.filter(area__cemetery__ugh=ugh).delete()
        AreaCoordinates.objects.filter(area__cemetery__ugh=ugh).delete()
        Area.objects.filter(cemetery__ugh=ugh).delete()
        print('removing cemeteries')
        CemeteryCoordinates.objects.filter(cemetery__ugh=ugh).delete()
        Cemetery.objects.filter(ugh=ugh).delete()
        Reason.objects.filter(org=ugh).delete()
        transaction.commit()
        
        remove_org(ugh)
        print('UGH deleted')
        transaction.commit()

def remove_org(org):
    org.store_set.all().delete()
    org.favorite_loru.all().delete()
    org.bankaccount_set.all().delete()
    OrgCertificate.objects.filter(org=org).delete()
    for profile in Profile.objects.filter(org=org):
        user = profile.user
        profile.user = None
        profile.save()
        Log.objects.filter(user=user).delete()
        user.delete()
        profile.delete()
    if org.off_address:
        off_address = org.off_address
        org.off_address = None
        org.save()
        try:
            off_address.delete()
        except IntegrityError:
            pass
        
    org.delete()
    
transaction.set_autocommit(False)
try:
    main()
finally:
    transaction.commit()
    transaction.set_autocommit(True)
