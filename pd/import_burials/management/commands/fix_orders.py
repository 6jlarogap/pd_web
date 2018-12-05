import datetime
import gc

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection

from burials.models import Burial
from orders.models import Order


class Command(BaseCommand):
    def handle(self, *args, **options):
        transaction.set_autocommit(False)
        try:
            no_applicant_orders = Order.objects.filter(applicant=None, applicant_organization=None)
            cnt = no_applicant_orders.count()
            i = 0
            for o in no_applicant_orders:
                b = o.get_burial()
                if b:
                    o.applicant = b.applicant
                    o.applicant_organization = b.applicant_organization
                    o.save()
                i += 1
                if i % 400 == 0:
                    transaction.commit()
                    gc.collect()
                    connection.queries = []
                    print 'Processed', i, 'of', cnt
            print 'Processed', cnt, 'with broken applicants'

            wrong_date_orders = Order.objects.filter(burial__source_type=Burial.SOURCE_TRANSFERRED, dt__gte='2013-03-12')
            cnt = wrong_date_orders.count()
            i = 0
            for o in wrong_date_orders:
                b = o.get_burial()
                if b:
                    dt = b.changed and b.changed - datetime.timedelta(1) or o.dt or datetime.datetime.now()
                    o.dt = datetime.date(year=dt.year, month=dt.month, day=dt.day)
                    o.save()
                i += 1
                if i % 400 == 0:
                    transaction.commit()
                    gc.collect()
                    connection.queries = []
                    print 'Processed', i, 'of', cnt
            print 'Processed', cnt, 'with broken datetime'
        finally:
            transaction.commit()
            transaction.set_autocommit(True)


