# encoding: utf-8

import datetime
from django.core.management.base import BaseCommand, CommandError
from geo.models import DFiasAddrobj, Country, Region, City

class Command(BaseCommand):
    help = 'Imports cities from FIAS table'

    def handle(self, *args, **options):
        fias_list = DFiasAddrobj.objects.filter(aolevel__lt=5, ctarcode='000', placecode='000', streetcode='0000').exclude(citycode='000').using('fias')
        fias_cnt = fias_list.count()
        i = 0
        
        for fias in fias_list:
            region = None
            parent = fias
            while not region:
                parent = DFiasAddrobj.objects.using('fias').filter(aoguid=parent.parentguid, enddate__gte=datetime.datetime.now())[0]
                if not parent.parentguid:
                    region = Region.objects.get(name=u'%s %s' % (parent.formalname, parent.shortname))
            City.objects.get_or_create(name=u'%s %s' % (fias.shortname, fias.formalname), region=region)
            i += 1
            if i % 100 == 0:
                print '%s of %s ready, %s %%' % (i, fias_cnt, float(i)/fias_cnt*100)
            
