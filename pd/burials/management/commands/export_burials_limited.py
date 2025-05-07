# export_terminal.py
#
# Запуск: : ./manage.py export_burials каталог_для_результатов
#
# Формирование .csv файлов для имеющихся терминалов на кладбищах, limit захоронений

import sys, os, re, json

from django import db
from django.db.models.query_utils import Q
from django.core.management.base import BaseCommand

from burials.models import \
    Place, Grave, Burial, Cemetery, Area, BurialFiles, BurialComment, \
    PlacePhoto, AreaPhoto, CemeteryPhoto
from persons.models import DeadPerson, AlivePerson
from geo.models import Country, Region, City
from users.models import Org


class Command(BaseCommand):

    burial_states = (Burial.STATUS_CLOSED,)

    help = "Form export json files for all burials of a organization"

    def add_arguments(self, parser):
        parser.add_argument('ugh_pk', type=str)
        parser.add_argument('export_path', type=str)
        parser.add_argument('url_media', type=str)
        parser.add_argument('limit', type=int)

    def handle(self, *args, **kwargs):
        ugh_pk = kwargs['ugh_pk']
        export_path = kwargs['export_path']
        export_path = export_path.rstrip('/')
        url_media = kwargs['url_media']
        if not url_media:
            url_media = 'https://org.pohoronnoedelo.ru/media'
        url_media = url_media.rstrip('/')
        limit = kwargs['limit']

        ugh = Org.objects.get(pk=ugh_pk)
        media_txt = open(f'{export_path}/media.txt', 'w')

        print('IDS')
        b_pks = set(); p_pks = set(); a_pks = set(); c_pks = set()
        for b in Burial.objects.filter(
                ugh=ugh,
                status__in=self.burial_states,
                annulated=False,
            ).order_by(
                'pk'
            )[:limit]:
            b_pks.add(b.pk)
            p_pks.add(b.place_id)
            a_pks.add(b.area_id)
            c_pks.add(b.cemetery_id)

        print('BURIAL FILES')
        burialfile = dict()
        burialfile_qs = BurialFiles.objects.filter(
            burial__pk__in=b_pks,
        ).order_by('pk')
        n = 0
        for f in burialfile_qs.iterator(chunk_size=100):
            if f.bfile:
                if burialfile.get(f.burial_id) == None:
                    burialfile[f.burial_id] = []
                f_export = f.export_dict()
                media_txt.write(f'{url_media}/{f_export["path"]}\n')
                burialfile[f.burial_id].append(f_export)
                if n and n % 1000 == 0:
                    print(f'{n} burial files processed')
                n += 1
        print(f'{n} burial files total')

        print('BURIAL COMMENTS')
        burialcomment = dict()
        burialcomment_qs = BurialComment.objects.filter(
            burial__pk__in=b_pks,
        ).order_by('pk')
        n = 0
        for f in burialcomment_qs.iterator(chunk_size=100):
            if f.comment.strip():
                if burialcomment.get(f.burial_id) == None:
                    burialcomment[f.burial_id] = []
                f_export = f.export_dict()
                burialcomment[f.burial_id].append(f_export)
                if n and n % 1000 == 0:
                    print(f'{n} burial comments processed')
                n += 1
        print(f'{n} burial comments total')

        burial_qs = Burial.objects.filter(
            pk__in=b_pks,
        ).select_related(

            'deadman',
            'deadman__address',
            'deadman__address__country', 'deadman__address__region',
            'deadman__address__city', 'deadman__address__street',
            'deadman__deathcertificate', 'deadman__deathcertificate__deathcertificatescan', 'deadman__deathcertificate__zags',

            'applicant',
            'applicant__address',
            'applicant__address__country', 'applicant__address__region',
            'applicant__address__city', 'applicant__address__street',
            'applicant__personid', 'applicant__personid__id_type', 'applicant__personid__source',

            'exhumationrequest', 'exhumationrequest__applicant',
            'exhumationrequest__applicant__address', 'exhumationrequest__applicant__address__country',
            'exhumationrequest__applicant__address__region', 'exhumationrequest__applicant__address__street',

        ).order_by('pk')

        print('BURIALS')
        burial = []
        n = 0
        for b in burial_qs.iterator(chunk_size=100):
            r = b.export_dict()

            files = None
            if burialfile.get(b.pk):
                files=burialfile[b.pk]
            r.update(files=files)

            comments = None
            if burialcomment.get(b.pk):
                comments=burialcomment[b.pk]
            r.update(comments=comments)

            try:
                scan_path = r["deadman"]["death_certificate"]["scan"]["path"]
                media_txt.write(f'{url_media}/{scan_path}\n')
            except TypeError:
                pass

            burial.append(r)
            if n and n % 1000 == 0:
                print(f'{n} burials processed')
            n += 1
        print(f'{n} burials total')

        print('CEMETERY PHOTOS')
        cemeteryphoto = dict()
        cemeteryphoto_qs = CemeteryPhoto.objects.filter(
            cemetery__pk__in=c_pks,
        ).order_by('pk')
        n = 0
        for f in cemeteryphoto_qs.iterator(chunk_size=100):
            if f.photo:
                if cemeteryphoto.get(f.cemetery_id) == None:
                    cemeteryphoto[f.cemetery_id] = []
                f_export = f.export_dict()
                media_txt.write(f'{url_media}/{f_export["path"]}\n')
                cemeteryphoto[f.cemetery_id].append(f_export)
                if n and n % 1000 == 0:
                    print(f'{n} cemetery photos processed')
                n += 1
        print(f'{n} cemetery photos total')

        cemetery_qs = Cemetery.objects.filter(
            pk__in=c_pks,
        ).select_related(
            'address', 'address__country', 'address__region',
            'address__city', 'address__street',
        ).order_by('pk')

        print('CEMETERIES')
        cemetery = []
        n = 0
        for c in cemetery_qs.iterator(chunk_size=100):
            r = c.export_dict()
            photos = None
            if cemeteryphoto.get(c.pk):
                photos=cemeteryphoto[c.pk]
            r.update(photos=photos)
            cemetery.append(r)
            if n and n % 1000 == 0:
                print(f'{n} cemeteries processed')
            n += 1
        print(f'{n} cemeteries total')

        print('AREA PHOTOS')
        areaphoto = dict()
        areaphoto_qs = AreaPhoto.objects.filter(
            area__pk__in=a_pks,
        ).order_by('pk')
        n = 0
        for f in areaphoto_qs.iterator(chunk_size=100):
            if f.bfile:
                if areaphoto.get(f.area_id) == None:
                    areaphoto[f.area_id] = []
                f_export = f.export_dict()
                media_txt.write(f'{url_media}/{f_export["path"]}\n')
                areaphoto[f.area_id].append(f_export)
                if n and n % 1000 == 0:
                    print(f'{n} area photos processed')
                n += 1
        print(f'{n} area photos total')

        area_qs = Area.objects.filter(
            pk__in=a_pks,
        ).select_related(
            'purpose',
        ).order_by('pk')

        print('AREAS')
        area = []
        n = 0
        for a in area_qs.iterator(chunk_size=100):
            r = a.export_dict()
            photos = None
            if areaphoto.get(c.pk):
                photos=areaphoto[c.pk]
            r.update(photos=photos)
            area.append(r)
            if n and n % 1000 == 0:
                print(f'{n} areas processed')
            n += 1
        print(f'{n} areas total')


        print('PLACE PHOTOS')
        placephoto = dict()
        placephoto_qs = PlacePhoto.objects.filter(
            place__pk__in=p_pks,
        ).order_by('pk')

        n = 0
        for f in placephoto_qs.iterator(chunk_size=100):
            if f.bfile:
                if placephoto.get(f.place_id) == None:
                    placephoto[f.place_id] = []
                f_export = f.export_dict()
                media_txt.write(f'{url_media}/{f_export["path"]}\n')
                placephoto[f.place_id].append(f_export)
                if n and n % 1000 == 0:
                    print(f'{n} place photos processed')
                n += 1
        print(f'{n} place photos total')

        place_qs = Place.objects.filter(
            pk__in=p_pks,
        ).select_related(

            'responsible',
            'responsible__address',
            'responsible__address__country', 'responsible__address__region',
            'responsible__address__city', 'responsible__address__street',
            'responsible__personid', 'responsible__personid__id_type', 'responsible__personid__source',

        ).order_by('pk')

        print('PLACES')
        place = []
        n = 0
        for p in place_qs.iterator(chunk_size=100):
            r = p.export_dict()
            photos = None
            if placephoto.get(p.pk):
                photos=placephoto[p.pk]
            r.update(photos=photos)
            place.append(r)
            if n and n % 1000 == 0:
                print(f'{n} places processed')
            n += 1
        print(f'{n} places total')

        media_txt.close()

        for v in ('burial', 'cemetery', 'area', 'place'):
            with open(f'{export_path}/{v}.json', 'w') as f:
                f.write(json.dumps(eval(v), indent=4, ensure_ascii=False,))
