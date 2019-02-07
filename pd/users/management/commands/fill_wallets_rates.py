# -*- coding: utf-8 -*-

import sys

from django.core.management.base import BaseCommand
from users.models import Org
from billing.models import Currency

class Command(BaseCommand):
    help = 'Fill <Currency_code> wallets for existing lorus and ughs, rates for ughs'
    
    def add_arguments(self, parser):
        parser.add_argument('code', type=str, help='currency code (RUR, BYN etc)')

    def handle(self, *args, **options):
        code = kwargs['code'].upper()
        currency = Currency.objects.get(code=code)
        for org in Org.objects.filter(type__in=(Org.PROFILE_UGH, Org.PROFILE_LORU, )):
            org.create_wallet_rate(currency)
