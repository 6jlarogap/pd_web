# export_terminal.py
#
# Запуск: : ./manage.py export_burials каталог_для_результатов
#
# Формирование .csv файлов для имеющихся терминалов на кладбищах

import sys, os, re, json

from django import db
from django.db.models.query_utils import Q
from django.core.management.base import BaseCommand

from burials.models import Place, Grave, Burial, Cemetery, BurialFiles
from persons.models import DeadPerson, AlivePerson
from geo.models import Country, Region, City
from users.models import Org


class Command(BaseCommand):

    burial_states = (Burial.STATUS_CLOSED, Burial.STATUS_EXHUMATED,)

    help = "Form export json files for all burials of a organization"

    def add_arguments(self, parser):
        parser.add_argument('ugh_pk', type=str)
        parser.add_argument('export_path', type=str)

    def handle(self, *args, **kwargs):
        ugh_pk = kwargs['ugh_pk']
        export_path = kwargs['export_path']

        ugh = Org.objects.get(pk=ugh_pk)

        media_txt = open(f'{export_path}/media.txt', 'w')

        burialfile = dict()
        burialfile_qs = BurialFiles.objects.filter(
            burial__ugh=ugh,
            burial__status__in=self.burial_states,
            burial__annulated=False,
        ).order_by('pk')
        n = 0
        for f in burialfile_qs.iterator(chunk_size=100):
            if f.bfile:
                if burialfile.get(f.burial_id) == None:
                    burialfile[f.burial_id] = []
                f_export = f.export_dict()
                media_txt.write(f'{f_export["path"]}\n')
                burialfile[f.burial_id].append(f.export_dict())
                if n and n % 1000 == 0:
                    print(f'{n} burial files processed')
                n += 1
        print(f'{n} burial files total')

        burial_qs = Burial.objects.filter(
            ugh=ugh,
            status__in=self.burial_states,
            annulated=False,
        ).select_related(
            'applicant',
            'applicant__address', 'applicant__address__country',
            'applicant__address__region', 'applicant__address__street',
            'deadman',
            'deadman__address', 'deadman__address__country',
            'deadman__address__region', 'deadman__address__street',
            'responsible',
            'responsible__address', 'responsible__address__country',
            'responsible__address__region', 'responsible__address__street',
            'exhumationrequest', 'exhumationrequest__applicant',
            'exhumationrequest__applicant__address', 'exhumationrequest__applicant__address__country',
            'exhumationrequest__applicant__address__region', 'exhumationrequest__applicant__address__street',
            'deadman__deathcertificate', 'deadman__deathcertificate__deathcertificatescan', 'deadman__deathcertificate__zags',
        ).order_by('pk')[:2000]

        print('BURIAL')
        burial = []
        n = 0
        for b in burial_qs.iterator(chunk_size=100):
            r = b.export_dict()
            if burialfile.get(b.pk):
                r.update(file=burialfile[b.pk])
            try:
                media_txt.write(f'{r["deadman"]["death_certificate"]["scan"]["path"]}\n')
            except TypeError:
                pass
            burial.append(r)
            if n and n % 1000 == 0:
                print(f'{n} burials processed')
            n += 1
        print(f'{n} burials total')

        media_txt.close()

        for v in ('burial', ):
            with open(f'{export_path}/{v}.json', 'w') as f:
                f.write(json.dumps(eval(v), indent=4, ensure_ascii=False,))
