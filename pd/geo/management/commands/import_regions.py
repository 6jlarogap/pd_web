# encoding: utf-8

from django.core.management.base import BaseCommand, CommandError
from geo.models import DFiasAddrobj, Country, Region

class Command(BaseCommand):
    help = 'Imports regions from FIAS table'

    def handle(self, *args, **options):
        fias_list = DFiasAddrobj.objects.filter(parentguid='').using('fias')
        fias_cnt = fias_list.count()
        i = 0
        
        country, _tmp = Country.objects.get_or_create(name=u'Россия') 
        
        for fias in fias_list:
            print 'fias.formalname, fias.shortname', fias.formalname, fias.shortname
            country.region_set.get_or_create(name=u'%s %s' % (fias.formalname, fias.shortname))
            i += 1
            if i % 100 == 0:
                print '%s of %s ready, %s %%' % (i, fias_cnt, float(i/fias_cnt)*100)
            
