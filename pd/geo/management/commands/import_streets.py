# encoding: utf-8

import datetime
import gc
from django.core.management.base import BaseCommand, CommandError
from django import db
from geo.models import DFiasAddrobj, Country, Region, City, Street

class Command(BaseCommand):
    help = 'Imports cities from FIAS table'
    
    @db.transaction.commit_on_success
    def handle(self, *args, **options):
        fias_list = DFiasAddrobj.objects.filter(aolevel__lt=8, extrcode='0000', sextcode='000').exclude(streetcode='0000').using('fias')
        fias_cnt = fias_list.count()
        i = 0
        
        while i < fias_cnt:
            for fias in fias_list[i:i+1000]:
                city = None
                parent = fias
                while not city:
                    prev_parent = parent
                    parent = DFiasAddrobj.objects.using('fias').filter(aoguid=parent.parentguid, enddate__gte=datetime.datetime.now())[0]
                    if parent.citycode != '000':
                        try:
                            city = City.objects.get(name=u'%s %s' % (parent.shortname, parent.formalname))
                        except City.DoesNotExist:
                            pass
                        except City.MultipleObjectsReturned:
                            pass
                    if parent.parentguid == '':
                        break
                if city:
                    Street.objects.get_or_create(name=u'%s %s' % (fias.shortname, fias.formalname), city=city)

            i += 1000
            print '%s of %s ready, %s %%' % (i, fias_cnt, float(i)/fias_cnt*100)
            db.reset_queries()  
            gc.collect()
            db.transaction.commit()
            
