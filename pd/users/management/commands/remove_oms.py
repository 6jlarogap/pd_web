# -*- coding: utf-8 -*-

import sys

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.db.models.query_utils import Q
from django.db.models.query_utils import Q

from users.models import Org, ProfileLORU, Profile, Dover
from burials.models import Cemetery, Burial, BurialFiles, ExhumationRequest
from orders.models import Order, OrderItem, ServiceItem, OrgService, OrgServicePrice, \
                          OrderComment, ResultFile
from persons.models import DeadPerson, AlivePerson

class Command(BaseCommand):
    args = '<OMS pk>'
    help = 'Remove OMS, all its objects including LORUs'
    
    @transaction.commit_on_success
    def handle(self, *args, **options):
        try:
            ugh_pk=args[0]
        except IndexError:
            print 'Argument error: no OMS pk given'
            return
        ugh = Org.objects.get(pk=ugh_pk, type=Org.PROFILE_UGH)

        # Организации, ссылки на которые могут быть в захоронениях и в заказах на захоронения:
        org_qs = Q(burial__ugh=ugh) | \
                 Q(applicant_organization_burials__ugh=ugh) | \
                 Q(exhumationrequest__burial__ugh=ugh) | \
                 Q(ugh_list__ugh=ugh)
                 
        for org in Org.objects.filter(org_qs).distinct():
            ProfileLORU.objects.filter(loru=org).delete()

            OrderComment.objects.filter(order__loru=org).delete()
            ResultFile.objects.filter(order__loru=org).delete()
            OrderItem.objects.filter(
                Q(order__loru=org) | \
                Q(order__applicant_organization=org) | \
                Q(order__agent__org=org) | \
                Q(order__dover__agent__org=org) | Q(order__dover__target_org=org) | \
                Q(order__burial__ugh=org)
            ).delete()
            ServiceItem.objects.filter(orgservice__org=org).delete()
            OrgServicePrice.objects.filter(orgservice__org=org).delete()
            OrgService.objects.filter(org=org).delete()
            Order.objects.filter(
                Q(loru=org) | \
                Q(applicant_organization=org) | \
                Q(agent__org=org) | \
                Q(dover__agent__org=org) | Q(dover__target_org=org) | \
                Q(burial__ugh=org)
            ).delete()

            org.store_set.all().delete()
            org.favorite_loru.all().delete()
            org.bankaccount_set.all().delete()

            Burial.objects.filter(applicant_organization=org).update(applicant_organization=None)
            Burial.objects.filter(agent__org=org).update(agent=None)
            Burial.objects.filter(Q(dover__agent__org=org) | Q(dover__target_org=org)).update(dover=None)
            ExhumationRequest.objects.filter(applicant_organization=org).update(applicant_organization=None)
            ExhumationRequest.objects.filter(agent__org=org).update(agent=None)
            ExhumationRequest.objects.filter(Q(dover__agent__org=org) | Q(dover__target_org=org)).update(dover=None)
            Burial.objects.filter(loru=org).update(loru=None)
            Burial.objects.filter(loru_agent__org=org).update(loru_agent=None)
            Burial.objects.filter(Q(loru_dover__agent__org=org) | Q(loru_dover__target_org=org)).update(loru_dover=None)

            DeadPerson.objects.filter(burial__ugh=org).delete()
            AlivePerson.objects.filter(
                Q(applied_burials__ugh=org) | \
                Q(exhumationrequest__burial__ugh=org)
            ).delete()
            # TODO AlivePerson - заказчики заказов, responsibles незакрытых захоронений

            if org.off_address:
                off_address = org.off_address
                org.off_address = None
                org.save()
                try:
                    off_address.delete()
                except IntegrityError:
                    pass
            
            Cemetery.objects.filter(creator__profile__org=org).update(creator=None)
            BurialFiles.objects.filter(burial__ugh=org).delete()
            Burial.objects.filter(changed_by__profile__org=org).update(changed_by=None)
            Dover.objects.filter(Q(agent__org=org) | Q(target_org=org)).delete()
            for profile in Profile.objects.filter(org=org):
                user = profile.user
                profile.user = None
                profile.save()
                user.delete()
                profile.delete()
            org.delete()

        ExhumationRequest.objects.filter(burial__ugh=ugh).delete()
        Burial.objects.filter(ugh=ugh).delete()
