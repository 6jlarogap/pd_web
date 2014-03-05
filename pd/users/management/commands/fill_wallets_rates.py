# -*- coding: utf-8 -*-

import sys

from django.core.management.base import BaseCommand
from users.models import Org
from billing.models import Currency

class Command(BaseCommand):
    args = '<Currecy_code_(e.g._RUR)>'
    help = 'Fill Currency_code wallets for existing lorus and ughs, rates for ughs'
    
    def handle(self, *args, **options):
        currency = Currency.objects.get(code=args[0])
        for org in Org.objects.filter(type__in=(Org.PROFILE_UGH, Org.PROFILE_LORU, )):
            org.create_wallet_rate(currency)
