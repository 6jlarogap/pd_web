# -*- coding: utf-8 -*-
#
# one_ugh_leave.py
# 
# - оставить в базе только один ОМС
# - сформировать список медийных файлов, принадлежащих этому ОМС
#
# Запуск: ./manage.py one_ugh_leave <pk>
#

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.db.models.query_utils import Q

from django.contrib.auth.models import User
from users.models import Org, ProfileLORU, Profile, Dover, OrgCertificate, \
                         OrgGallery, OrgContract, UserPhoto
from logs.models import Log
from burials.models import Cemetery, CemeteryCoordinates, Area, AreaCoordinates, \
                           Place, PlaceSize, PlacePhoto, Grave, \
                           Burial, BurialFiles, Reason, ExhumationRequest, \
                           BurialComment, PlaceStatus, AreaPhoto, PlaceStatusFiles
from orders.models import Order, OrderItem, ServiceItem, OrgService, OrgServicePrice, \
                          OrderComment, ResultFile
from persons.models import DeadPerson, AlivePerson, DeathCertificateScan

class Command(BaseCommand):
    args = 'OMS_pk OMS_media_list'
    help = "Leave only one OMS in the database, form the list of its media file"
    
    media_file = None
    count_media = 0

    # Главная функция
    #
    @transaction.commit_on_success
    def handle(self, *args, **options):
        if len(args) < 2:
            print "ERROR! PLease give me a parm. Type --help to get help"
            quit()
        ugh_pk = args[0]
        try:
            ugh_one = Org.objects.get(type=Org.PROFILE_UGH, pk=ugh_pk)
        except Org.DoesNotExist:
            print "ERROR! Failed to gind OMS with pk=%s" % ugh_pk
            quit()
        media_list = args[1]
        print 'Forming the list of media of the OMS, %s' % media_list

        try:
            self.media_file = open(media_list, 'w')
        except IOError:
            print "ERROR! Failed to open '%s' for write" % media_list
            quit()

        for model in (OrgCertificate, OrgGallery, OrgContract,):
            self.collect_media(model, Q(org=ugh_one))
        self.collect_media(UserPhoto, Q(user__profile__org=ugh_one))
        self.collect_media(
            DeathCertificateScan,
            Q(deathcertificate__person__burial__ugh=ugh_one)
        )
        self.collect_media(AreaPhoto, Q(area__cemetery__ugh=ugh_one))
        self.collect_media(PlacePhoto, Q(place__cemetery__ugh=ugh_one))
        self.collect_media(
            PlaceStatusFiles,
            Q(placestatus__place__cemetery__ugh=ugh_one)
        )
        self.collect_media(BurialFiles, Q(burial__ugh=ugh_one))
        
        self.media_file.close()
        print '\n%s total media recs written\n' % self.count_media
        
        ugh_qs = Q(type=Org.PROFILE_UGH) & ~Q(pk=ugh_pk)

        print 'Looking for UGHs to be removed'
        for ugh in Org.objects.filter(ugh_qs):
            print ugh
            print 'removing deadmen in burial'
            i = 0
            for deadperson in DeadPerson.objects.filter(burial__ugh=ugh).iterator():
                i += 1 
                Burial.objects.filter(deadman=deadperson).update(deadman=None)
                deadperson.delete()
                if i % 1000 == 0:
                    print "%d deadmen removed" % i
            print 'removing burial applicants- alivepersons'
            transaction.commit()
            i = 0
            for aliveperson in AlivePerson.objects.filter(applied_burials__ugh=ugh).iterator():
                i += 1 
                Burial.objects.filter(applicant=aliveperson).update(applicant=None)
                aliveperson.delete()
                if i % 1000 == 0:
                    print "%d burial applicants removed" % i
            print 'removing non-closed burial responsibles- alivepersons'
            transaction.commit()
            for aliveperson in AlivePerson.objects.filter(responsible_burials__ugh=ugh).iterator():
                Burial.objects.filter(responsible=aliveperson).update(applicant=None)
                aliveperson.delete()
            print 'removing exhumationrequest applicants- alivepersons'
            for aliveperson in AlivePerson.objects.filter(exhumationrequest__burial__ugh=ugh).iterator():
                ExhumationRequest.objects.filter(applicant=aliveperson).update(applicant=None)
                aliveperson.delete()
            transaction.commit()

            print 'removing orderItems'
            OrderItem.objects.filter(order__burial__ugh=ugh).delete()
            ServiceItem.objects.filter(order__burial__ugh=ugh).delete()

            print 'removing orders'
            Order.objects.filter(burial__ugh=ugh).delete()
            transaction.commit()

            print 'Marking dependent fields in Burials as None'
            Burial.objects.filter(Q(applicant_organization=ugh) & ~Q(ugh=ugh_one)). \
                update(applicant_organization=None)
            Burial.objects.filter(Q(agent__org=ugh) & ~Q(ugh=ugh_one)). \
                update(agent=None)
            Burial.objects.filter((Q(dover__agent__org=ugh) | Q(dover__target_org=ugh)) & ~Q(ugh=ugh_one)). \
                update(dover=None)
            ExhumationRequest.objects.filter(Q(applicant_organization=ugh)  & ~Q(burial__ugh=ugh_one)). \
                update(applicant_organization=None)
            ExhumationRequest.objects.filter(Q(agent__org=ugh) & ~Q(burial__ugh=ugh_one)). \
                update(agent=None)
            ExhumationRequest.objects.filter((Q(dover__agent__org=ugh) | Q(dover__target_org=ugh))  & ~Q(burial__ugh=ugh_one)). \
                update(dover=None)
            Burial.objects.filter(Q(loru=ugh)  & ~Q(ugh=ugh_one)). \
                update(loru=None)
            Burial.objects.filter(Q(loru_agent__org=ugh) & ~Q(ugh=ugh_one)). \
                update(loru_agent=None)
            Burial.objects.filter((Q(loru_dover__agent__org=ugh) | Q(loru_dover__target_org=ugh)) & ~Q(ugh=ugh_one)). \
                update(loru_dover=None)
            transaction.commit()

            print 'removing burials'
            ExhumationRequest.objects.filter(burial__ugh=ugh).delete()
            BurialFiles.objects.filter(burial__ugh=ugh).delete()
            BurialComment.objects.filter(burial__ugh=ugh).delete()
            Burial.objects.filter(ugh=ugh).delete()
            transaction.commit()
            print 'removing graves'
            Grave.objects.filter(place__cemetery__ugh=ugh).delete()
            transaction.commit()

            print 'removing place responsibles- alivepersons'
            i = 0
            for aliveperson in AlivePerson.objects.filter(place__cemetery__ugh=ugh).iterator():
                i += 1
                Place.objects.filter(responsible=aliveperson).update(responsible=None)
                try:
                    user = aliveperson.user
                except (AttributeError, User.DoesNotExist,):
                    aliveperson.delete()
                    if i % 1000 == 0:
                        print "%d place responsibles removed" % i
                        transaction.commit()

            print 'removing places'
            PlaceSize.objects.filter(org=ugh).delete()
            PlacePhoto.objects.filter(place__cemetery__ugh=ugh).delete()
            PlaceStatusFiles.objects.filter(placestatus__place__cemetery__ugh=ugh).delete()
            PlaceStatus.objects.filter(place__cemetery__ugh=ugh).delete()
            Place.objects.filter(cemetery__ugh=ugh).delete()
            transaction.commit()

            print 'removing areas'
            AreaPhoto.objects.filter(area__cemetery__ugh=ugh).delete()
            AreaCoordinates.objects.filter(area__cemetery__ugh=ugh).delete()
            Area.objects.filter(cemetery__ugh=ugh).delete()
            print 'removing cemeteries'
            CemeteryCoordinates.objects.filter(cemetery__ugh=ugh).delete()
            Cemetery.objects.filter(ugh=ugh).delete()
            Reason.objects.filter(org=ugh).delete()
            transaction.commit()
            
            self.remove_org(ugh)
            print 'UGH deleted'
            transaction.commit()

        print 'Current Stats'
        print 'Burials total: %s' % Burial.objects.all().count()
        print 'DeadPerson total: %s' % DeadPerson.objects.all().count()
        print 'Places total: %s' % Place.objects.all().count()

        print 'DeathCertificateScans total: %s' % DeathCertificateScan.objects.all().count()
        print 'PlacePhoto total: %s' % PlacePhoto.objects.all().count()
        print 'Burial Files total: %s' % BurialFiles.objects.all().count()

    def remove_org(self, org):
        org.store_set.all().delete()
        org.favorite_loru.all().delete()
        org.bankaccount_set.all().delete()
        OrgCertificate.objects.filter(org=org).delete()
        OrgContract.objects.filter(org=org).delete()
        OrgGallery.objects.filter(org=org).delete()
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

    def collect_media(self, model, filter_, field='bfile'):
        print ' - %s' % model._meta.object_name
        count_model = 0
        for rec in model.objects.filter(filter_):
            self.count_media += 1
            count_model +=1
            self.media_file.write(u"%s\n" % getattr(rec, field).name)
        print '     %s media recs written' % count_model
