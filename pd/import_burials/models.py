import os
import copy
import csv
import io
import datetime
import gc
import json
import codecs
import re
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction, connection, reset_queries
from django.db.models import Count
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from django.utils.translation import ugettext as _
from django.utils.formats import localize

from burials.models import Burial, BurialComment, ExhumationRequest, Cemetery, Area, Place, AreaPurpose, Grave, BurialFiles
from geo.models import Location, Country, Region, City, Street
from logs.models import write_log, LogOperation
from orders.models import Product, Order, OrderItem, CoffinData, CatafalqueData, AddInfoData
from pd.models import UnclearDate
from persons.models import AlivePerson, DeadPerson, PersonID, IDDocumentType, DocumentSource, DeathCertificate
from users.models import Org, Profile, Dover, BankAccount

csv.register_dialect("4minsk", escapechar="\\", quoting=csv.QUOTE_ALL, doublequote=False)

DT_TEMPLATE = '%Y-%m-%dT%H:%M:%S.%f'

NO_NAMES = (
    '?',
    '*',
    'ъ',
    'ь',
    'неизвест',
    'без хоз',
    'без фамил',
    )
NO_NAMES_RE = re.compile(r'^(?:%s)' % r'|'.join([re.escape(n) for n in NO_NAMES]))

def make_name(name):
    name = name.strip()
    if re.search(NO_NAMES_RE, name.lower()):
        name=''
    return name

def make_date(s):
    """
    Сделать UnclearDate из строки с датой
    """
    d = None
    try:
        d = datetime.datetime.strptime(s[:10], '%Y-%m-%d')
        d = UnclearDate(year=d.year, month=d.month, day=d.day)
        if d.month == 1 and d.day == 1:
           if d.year == 1900 or d.year <= 1800:
               d = None
           elif d.year < 1900:
               d.no_day = True
               d.no_month = True
    except ValueError:
        pass
    return d

COMMENT_URN_RE = re.compile(r'kombinat\:\d+.*\s+(?:урна|урнов)')

def do_import_burials_minsk(csv_fileobj, cemetery, user):
    
    ugh=user.profile.org
    cemetery = Cemetery.objects.filter(name=cemetery, ugh=ugh)[0]
    # Defaults:
    area_availability = Area.AVAILABILITY_OPEN
    area_purpose, _created = AreaPurpose.objects.get_or_create(name='общественный')
    comment_child_burial = "Захоронение детское"
    comment_child_burial_2 = "Детское захоронение"
    re_comment_child_burial = re.escape(comment_child_burial)
    re_comment_child_burial_2 = re.escape(comment_child_burial_2)

    (musor_str_id,
        account_number,
        deadman_ln, deadman_fn, deadman_mn,
        musor_initials,
        fact_date,
        area_name, row_name, place_number,
        applicant_ln, applicant_fn, applicant_mn,
        musor_cust_initials,
        city_name, street_name, house, block, flat,
        comments,
        country_name,
        region_name,
        phone,
        file_names, file_comments,
        post_index, building,
        op_type,
     ) = list(range(28))
    today = datetime.date.today()
    today_str = "{0:d}/{1:02d}/{2:02d}".format(today.year, today.month, today.day)
     
    def urn_by_comment(row):
        comment = row[comments].lower()
        return bool(re.search(COMMENT_URN_RE, comment))

    def make_burial(row, burial_type, is_urn=False):
        """
        Создать захоронение
        
        В зависимости от того, новое оно, подзахоронение, в существующую
        """
        row[area_name] = row[area_name].strip()
        if not row[area_name]:
            row[area_name] = 'Без имени'

        area, _created = Area.objects.get_or_create(
            cemetery=cemetery,
            name=row[area_name],
            defaults = {'availability': area_availability,
                        'purpose': area_purpose,
                        'places_count': 2,
                       }
        )

        row[row_name] = row[row_name].strip()
        row[place_number] = row[place_number].strip()
        place, _created = Place.objects.get_or_create(
            cemetery=cemetery,
            area=area,
            row=row[row_name],
            place=row[place_number],
        )

        applicant = None
        last_name = make_name(row[applicant_ln])
        phones = row[phone].strip()
        row[city_name] = row[city_name].strip()
        if last_name or row[city_name] or phones:
            # Адрес заявителя. Формируем, когда хотя бы есть город
            country = region = city = street = location = None
            row[country_name] = row[country_name].strip()
            if row[country_name].lower() == 'неизвестен':
                row[country_name] = 'Беларусь'
            if row[country_name]:
                country, _created = Country.objects.get_or_create(
                    name=row[country_name],
                )
            row[region_name] = row[region_name].strip()
            if row[region_name].lower() == 'неизвестен':
                row[region_name] = 'Минская обл.'
            if row[region_name] and country:
                region, _created = Region.objects.get_or_create(
                    country=country,
                    name=row[region_name],
                )
            if row[city_name].lower() == 'неизвестен':
                row[city_name] = 'Минск'
            if row[city_name] and region:
                city, _created = City.objects.get_or_create(
                    region=region,
                    name=row[city_name],
                )
            if city:
                row[street_name] = row[street_name].strip()
                if row[street_name] and city:
                    street, _created = Street.objects.get_or_create(
                        city=city,
                        name=row[street_name],
                    )
                location = Location.objects.create(
                    country=country,
                    region=region,
                    city=city,
                    street=street,
                    post_index=row[post_index].strip(),
                    house=row[house].strip(),
                    block=row[block].strip(),
                    building=row[building].strip(),
                    flat=row[flat].strip(),
                )
            if phones:
                phones = phones.replace("\n", "; ")
            applicant = AlivePerson.objects.create(
                last_name=last_name,
                first_name=last_name and make_name(row[applicant_fn]) or '',
                middle_name=last_name and make_name(row[applicant_mn]) or '',
                address=location,
                phones=phones,
            )

        graves_count = place.get_graves_count()
        grave_number = graves_count + 1
        grave = None
        if not graves_count or \
           burial_type in (Burial.BURIAL_NEW, Burial.BURIAL_ADD):
            grave = Grave.objects.create(
                place=place,
                grave_number=grave_number,
            )
        if burial_type == Burial.BURIAL_OVER and graves_count:
            # все захоронения в существующую, а также урны кладем
            # в 1-ю могилу
            grave_number = 1
            grave = Grave.objects.get(
                place=place,
                grave_number=grave_number,
            )

        burial_container = Burial.CONTAINER_URN if is_urn or row[op_type].lower() == 'урна' \
                                                else Burial.CONTAINER_COFFIN

        row[deadman_ln] = row[deadman_ln].strip()
        deadman = None
        last_name = make_name(row[deadman_ln])
        if last_name:
            deadman = DeadPerson.objects.create(
                last_name=last_name,
                first_name=make_name(row[deadman_fn]),
                middle_name=make_name(row[deadman_mn]),
            )

        burial = Burial.objects.create(
            burial_type=burial_type,
            burial_container=burial_container,
            source_type=Burial.SOURCE_TRANSFERRED,
            account_number=row[account_number].strip(),
            place=place,
            cemetery=cemetery,
            area=area,
            row=row[row_name],
            place_number=row[place_number],
            grave=grave,
            grave_number=grave_number,
            fact_date=make_date(row[fact_date][:10]),
            deadman=deadman,
            applicant=applicant,
            ugh=ugh,
            status=Burial.STATUS_CLOSED,
            changed_by=user,
            flag_no_applicant_doc_required = True,
        )
        
        request = HttpRequest()
        request.user = user
        if row[op_type].lower() == "захоронение детское":
            if not re.search(re_comment_child_burial, row[comments], flags=re.I) and \
               not re.search(re_comment_child_burial_2, row[comments], flags=re.I):
                BurialComment.objects.create(
                    burial=burial,
                    creator=user,
                    comment=comment_child_burial,
                )
                write_log(request, burial, "Комментарий: %s" % comment_child_burial)

        if row[comments]:
            for c in row[comments].split('\t'):
                try:
                    i_sep = c.index('~')
                    date_of_comment = datetime.datetime.strptime(c[:i_sep], DT_TEMPLATE)
                    comment = BurialComment.objects.create(
                        burial=burial,
                        creator=user,
                        comment=c[i_sep+1:],
                    )
                    BurialComment.objects.filter(pk=comment.pk).update(
                        dt_created=date_of_comment,
                        dt_modified=date_of_comment,
                    )
                    write_log(request, burial, "Комментарий (%s):\n%s" % (
                            localize(date_of_comment, use_l10n=True),
                            c[i_sep+1:],
                    ))
                except ValueError:
                    BurialComment.objects.create(
                        burial=burial,
                        creator=user,
                        comment=row[comments],
                    )
                    write_log(request, burial, "Комментарий: %s" % row[comments])
        write_log(request, burial, operation=LogOperation.CLOSED_BURIAL_TRANSFERRED)
        
        if row[file_names]:
            files = row[file_names].split('\n')
            fcomments = row[file_comments].split('\t')
            for i, f in enumerate(files):
                original_name = re.sub(r'^ofiles/(.+)', r'\1', f)
                f = f.replace('ofiles/','bfiles/%s/%s/' % (today_str, burial.pk, ))
                try:
                    fcomment = fcomments[i].strip() if fcomments[i] else original_name
                except IndexError:
                    fcomment = original_name
                BurialFiles.objects.create(
                    burial=burial,
                    bfile=f,
                    comment=fcomment,
                    original_name=original_name,
                )
        
    # Будут несколько проходов по считанному файлу импорта, надо бы сохранить
    tmp_file = os.path.join(settings.MEDIA_ROOT, 'csv_minsk.tmp')
    f = open(tmp_file, 'w')
    f.write(csv_fileobj.read().decode('utf-8'))
    f.close()
   
    total = 0
    f = open(tmp_file, 'r', newline='')
    csvreader = csv.reader(f, dialect="4minsk")
    print('1-st step: new burials: burials, kid burials, honour burials')
    n = 0
    for i, row in enumerate(csvreader):
        row[op_type] = row[op_type].lower()
        if row[op_type] in ('', 'захоронение', 'захоронение детское', 'почетное захоронение', ):
            if urn_by_comment(row):
                continue
            n += 1
            total += 1
            make_burial(row, Burial.BURIAL_NEW)
            if n % 1000 == 0:
                transaction.commit()
                print('Processed', n)
    if n % 1000 != 0:
        print('Processed', n)
    f.close()

    f = open(tmp_file, 'r', newline='')
    csvreader = csv.reader(f, dialect="4minsk")
    print('2-nd step: burials to add to existing place')
    n = 0
    for i, row in enumerate(csvreader):
        row[op_type] = row[op_type].lower()
        if row[op_type].startswith('подзахоронен'):
            if urn_by_comment(row):
                continue
            n += 1
            total += 1
            make_burial(row, Burial.BURIAL_ADD)
            if n % 1000 == 0:
                transaction.commit()
                print('Processed', n)
    if n % 1000 != 0:
        print('Processed', n)
    f.close()

    f = open(tmp_file, 'r', newline='')
    csvreader = csv.reader(f, dialect="4minsk")
    print('3-rd step: burials to existing graves, including urns')
    n = 0
    for i, row in enumerate(csvreader):
        row[op_type] = row[op_type].lower()
        is_urn = urn_by_comment(row)
        if row[op_type].startswith('захоронение в существ') or \
           row[op_type] == 'урна' or \
           is_urn:
            n += 1
            total += 1
            make_burial(row, Burial.BURIAL_OVER, is_urn=is_urn)
            if n % 1000 == 0:
                transaction.commit()
                print('Processed', n)
    if n % 1000 != 0:
        print('Processed', n)
    f.close()
    print('Processed total', total)

    os.remove(tmp_file)
    return total
    
