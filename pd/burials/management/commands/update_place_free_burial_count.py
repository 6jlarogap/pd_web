# -*- coding: utf-8 -*-

import sys

from django.core.management.base import BaseCommand
from burials.models import Place, Grave, Burial

class Command(BaseCommand):
    help = ""

    def handle(self, *args, **kwargs):
        """
        Fill place with grave available count
        """
        cnt = Place.objects.count()
        print "Apply migration on %d objects" % cnt
        
        row=0
        for place in Place.objects.all():
            place.available_count = max(0, place.get_graves_count() - place.burial_count())
            place.save()
            
            row += 1
            if row % 500 == 0:
                sys.stdout.write("\r%d%%" % int(row*100/cnt))
                sys.stdout.flush()
        print '\nDone'
       
