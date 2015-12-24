# coding=utf-8
import os
import copy
import csv
import cStringIO
import datetime
import gc
import json
import codecs
import re
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction, connection
from django.db.models import Count
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from django.utils.translation import ugettext as _
from django.utils.formats import localize

from burials.models import Burial, BurialComment, ExhumationRequest, Cemetery, Area, Place, AreaPurpose, Grave, BurialFiles
from geo.models import Location, Country, Region, City, Street
from logs.models import write_log
from orders.models import Product, Order, OrderItem, CoffinData, CatafalqueData, AddInfoData
from pd.models import UnclearDate
from persons.models import AlivePerson, DeadPerson, PersonID, IDDocumentType, DocumentSource, DeathCertificate
from users.models import Org, Profile, Dover, BankAccount

csv.register_dialect("4minsk", escapechar="\\", quoting=csv.QUOTE_ALL, doublequote=False)

DT_TEMPLATE = '%Y-%m-%dT%H:%M:%S.%f'

class UTF8Recoder:
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def import_location(location_data):
    country, _created = Country.objects.get_or_create(name=location_data[0])
    location = Location.objects.create(
        country = country,
        house = location_data[4],
        block = location_data[5],
        building = location_data[6],
        flat = location_data[7],
    )
    location.region, _created = Region.objects.get_or_create(country=location.country, name=location_data[1])
    location.city, _created = City.objects.get_or_create(region=location.region, name=location_data[2])
    location.street, _created = Street.objects.get_or_create(city=location.city, name=location_data[3])

    location.save()
    return location

def do_import_orgs(csv_fileobj):
    csvreader = UnicodeReader(csv_fileobj)
    for i, row in enumerate(csvreader):
        if i > 0:
            row = map(lambda c: '' if c == 'None' else c, row)
            org = None
            try:
                if row[0]:
                    org = Org.objects.get(inn=row[0])
                elif row[2]:
                    org = Org.objects.get(full_name=row[2])
            except Org.DoesNotExist:
                pass

            if not org:
                org = Org.objects.create(
                    type=Org.PROFILE_LORU,
                    inn=row[0],
                    name=row[1],
                    full_name=row[2],
                    director=row[3],
                )
                if row[4]:
                    org.off_address = import_location(row[4:12])

def make_unc_date(d):
    if d:
        pd_bits = d.split('.')
        if len(pd_bits) != 3:
            pd_bits = d.split('-')
        else:
            pd_bits.reverse()
        pd_bits = [b.isdigit() and int(b) or None for b in pd_bits]
        return UnclearDate(*pd_bits)
    return None

def import_alive_person(data):
    f,i,o = data[:3]
    if not any([f,i,o]):
        return None
    try:
        return AlivePerson.objects.get(last_name=f, first_name=i, middle_name=o)
    except AlivePerson.DoesNotExist:
        ap = AlivePerson.objects.create(
            last_name=f,
            first_name=i,
            middle_name=o,
            phones=data[3],
        )
        if data[5]:
            ap.address = import_location(data[5:13])
            ap.save()

        return ap

def import_dead_person(data):
    f,i,o = data[:3]
    if not any([f,i,o]) or f.lower() == u'биоотходы':
        return None

    birth_dt = make_unc_date(data[3])
    death_dt = make_unc_date(data[4])

    try:
        dp = DeadPerson.objects.get(last_name=f, first_name=i, middle_name=o)
        dp.birth_date = birth_dt
        dp.death_date = death_dt
        dp.save()
        return dp
    except DeadPerson.DoesNotExist:
        dp = DeadPerson.objects.create(
            last_name=f,
            first_name=i,
            middle_name=o,
            birth_date=birth_dt,
            death_date=death_dt,
        )
        if data[5]:
            dp.address = import_location(data[5:13])
            dp.save()

        return dp

@transaction.commit_on_success
def do_import_burials_minsk(csv_fileobj, cemetery, user):
    
    ugh=user.profile.org
    cemetery = Cemetery.objects.filter(name=cemetery, ugh=ugh)[0]
    # Defaults:
    area_availability = Area.AVAILABILITY_OPEN
    area_purpose, _created = AreaPurpose.objects.get_or_create(name='общественный')
    comment_child_burial = u"Захоронение детское"
    comment_child_burial_2 = u"Детское захоронение"
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
     ) = range(28)
    today = datetime.date.today()
    today_str = "{0:d}/{1:02d}/{2:02d}".format(today.year, today.month, today.day)
     
    def make_name(name):
        name = name.strip()
        if not name or name.lower() in (u'*', u'ъ', u'неизвестен',):
            name = ''
        return name

    def make_burial(row, burial_type):
        """
        Создать захоронение
        
        В зависимости от того, новое оно, подзахоронение, в существующую
        """
        row[area_name] = row[area_name].strip()
        if not row[area_name]:
            row[area_name] = u'Без имени'

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
        if last_name:
            # Адрес заявителя. Формируем, когда хотя бы есть город
            country = region = city = street = location = None
            row[country_name] = row[country_name].strip()
            if row[country_name]:
                country, _created = Country.objects.get_or_create(
                    name=row[country_name],
                )
            row[region_name] = row[region_name].strip()
            if row[region_name] and country:
                region, _created = Region.objects.get_or_create(
                    country=country,
                    name=row[region_name],
                )
            row[city_name] = row[city_name].strip()
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
            phones = row[phone].strip()
            if phones:
                phones = phones.replace("\n", "; ")
            applicant = AlivePerson.objects.create(
                last_name=last_name,
                first_name=make_name(row[applicant_fn]),
                middle_name=make_name(row[applicant_mn]),
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

        burial_container = Burial.CONTAINER_URN if row[op_type].lower() == u'урна' \
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
            fact_date=row[fact_date][:10] or None,
            deadman=deadman,
            applicant=applicant,
            ugh=ugh,
            status=Burial.STATUS_CLOSED,
            changed_by=user,
            flag_no_applicant_doc_required = True,
        )
        
        request = HttpRequest()
        request.user = user
        if row[op_type].lower() == u"захоронение детское":
            if not re.search(re_comment_child_burial, row[comments], flags=re.I) and \
               not re.search(re_comment_child_burial_2, row[comments], flags=re.I):
                BurialComment.objects.create(
                    burial=burial,
                    creator=user,
                    comment=comment_child_burial,
                )
                write_log(request, burial, u"Комментарий: %s" % comment_child_burial)

        if row[comments]:
            for c in row[comments].split('\t'):
                try:
                    i_sep = c.index(u'~')
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
                    write_log(request, burial, u"Комментарий (%s):\n%s" % (
                            localize(date_of_comment, use_l10n=True),
                            c[i_sep+1:],
                    ))
                except ValueError:
                    BurialComment.objects.create(
                        burial=burial,
                        creator=user,
                        comment=row[comments],
                    )
                    write_log(request, burial, u"Комментарий: %s" % row[comments])
        write_log(request, burial, _(u"Импорт"))
        
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
    f.write(csv_fileobj.read())
    f.close()
   
    total = 0
    f = open(tmp_file, 'r')
    csvreader = UnicodeReader(f, dialect="4minsk")
    print '1-st step: new burials: burials, kid burials, honour burials'
    n = 0
    for i, row in enumerate(csvreader):
        row[op_type] = row[op_type].lower()
        if row[op_type] in (u'', u'захоронение', u'захоронение детское', u'почетное захоронение', ):
            n += 1
            total += 1
            make_burial(row, Burial.BURIAL_NEW)
            if n % 1000 == 0:
                transaction.commit()
                print 'Processed', n
    if n % 1000 != 0:
        print 'Processed', n
    f.close()

    f = open(tmp_file, 'r')
    csvreader = UnicodeReader(f, dialect="4minsk")
    print '2-nd step: burials to add to existing place'
    n = 0
    for i, row in enumerate(csvreader):
        row[op_type] = row[op_type].lower()
        if row[op_type].startswith(u'подзахоронен'):
            n += 1
            total += 1
            make_burial(row, Burial.BURIAL_ADD)
            if n % 1000 == 0:
                transaction.commit()
                print 'Processed', n
    if n % 1000 != 0:
        print 'Processed', n
    f.close()

    f = open(tmp_file, 'r')
    csvreader = UnicodeReader(f, dialect="4minsk")
    print '3-rd step: burials to existing graves, including urns'
    n = 0
    for i, row in enumerate(csvreader):
        row[op_type] = row[op_type].lower()
        if row[op_type].startswith(u'захоронение в существ') or \
           row[op_type] == u'урна':
            n += 1
            total += 1
            make_burial(row, Burial.BURIAL_OVER)
            if n % 1000 == 0:
                transaction.commit()
                print 'Processed', n
    if n % 1000 != 0:
        print 'Processed', n
    f.close()
    print 'Processed total', total

    os.remove(tmp_file)
    return total
    
@transaction.commit_on_success
def do_import_burials(csv_fileobj, user):
    csvreader = UnicodeReader(csv_fileobj)
    try:
        loru = Org.objects.get(inn='4028046796')
    except Org.DoesNotExist:
        loru = None
    BURIAL_TYPES = {
        u'Захоронение': Burial.BURIAL_NEW,
        u'Подзахоронение к существ': Burial.BURIAL_ADD,
        u'Захоронение в существующ': Burial.BURIAL_OVER,
        u'Урна': Burial.BURIAL_URN,
    }
    real_i = 0
    dupes_i = 0
    for i, row in enumerate(csvreader):
        if i > 0:
            if i % 400 == 0:
                transaction.commit()
                gc.collect()
                connection.queries = []
                print 'Processed', i

            row = map(lambda c: '' if c == 'None' else c, row)
            try:
                cemetery = Cemetery.objects.get(name=row[6])
            except Cemetery.DoesNotExist:
                cemetery = Cemetery.objects.create(
                    name=row[6], time_begin='10:00', time_end='17:00',
                    creator=user, ugh=user.profile.org,
                    places_algo=Cemetery.PLACE_BURIAL_ACCOUNT_NUMBER
                )

            try:
                changed_dt = row[64].split(' ', 2)[2].rsplit(':', 1)[0]
            except Exception, e:
                print 'Error parsing', row[64], e
                changed_dt = datetime.datetime.now()

            try:
                b = Burial.objects.get(cemetery=cemetery, account_number=row[0])
                if b.changed != changed_dt:
                    b.changed = changed_dt
                if not b.applicant and not b.applicant_organization:
                    b.applicant = import_alive_person(row[41:55])
                b.deadman = import_dead_person(row[27:41])
                b.save()
                dupes_i += 1
            except Burial.DoesNotExist:
                area, _created = Area.objects.get_or_create(
                    name=row[7] or '',
                    cemetery=cemetery
                )

                area.availability = Area.AVAILABILITY_OPEN
                area.purpose, _created = AreaPurpose.objects.get_or_create(name='общественный')
                area.places_count = 2
                area.save()

                # row[26], Burial.grave_id в kaluga_new:
                #   - null:     всего одна могила, с номером 1
                #   - 0:        1-я могила, но есть еще могилы в этом месте
                #   - 1:        2-я могила, но есть еще могилы в этом месте,
                #               по крайней мере есть 1-я
                #   и т.д.
                grave_number=row[26]
                if grave_number:
                    grave_number = int(grave_number) + 1
                else:
                    grave_number = 1

                place, _created = Place.objects.get_or_create(
                    cemetery=cemetery,
                    area=area,
                    row=row[8],
                    place=row[9],
                    # places_count, неудачное название поля в place, лучше было бы graves_count
                    #
                    places_count=row[10] or 1,
                )

                responsible = import_alive_person(data=row[12:26])
                if responsible:
                    place.responsible = responsible
                    place.save()

                agent = None
                app_org = None
                dover = None

                if row[56]:
                    try:
                        if row[55]:
                            app_org = Org.objects.get(inn=row[55])
                        else:
                            app_org = Org.objects.get(full_name=row[56])
                    except Org.DoesNotExist:
                        print 'Org not found', row[55], row[56]
                        app_org = None

                if row[58]:
                    fm = u'%s %s' % (row[59] or '', row[60] or '')
                    fm = fm.strip()[:30]
                    try:
                        agent = Profile.objects.get(
                            user__last_name=row[58], user__first_name=fm, org=app_org, is_agent=True
                        )
                    except Profile.DoesNotExist:
                        agent = Profile.objects.create(
                            user=User.objects.create(
                                last_name=row[58], first_name=fm, username='imported_%s' % i, is_active=False,
                            ), org=app_org, is_agent=True
                        )

                    if agent and row[61]:
                        dover, _created = Dover.objects.get_or_create(
                            target_org=user.profile.org,
                            agent=agent,
                            number=row[61],
                            begin=row[62],
                            end=row[63],
                        )

                plan_date = make_unc_date(row[2])
                burial_container = Burial.CONTAINER_COFFIN
                if row[27].lower() == u'биоотходы':
                    burial_container = Burial.CONTAINER_BIO
                elif BURIAL_TYPES[row[1]] == Burial.BURIAL_URN:
                    burial_container = Burial.CONTAINER_URN
                params = dict(
                    account_number=row[0],
                    burial_type=BURIAL_TYPES[row[1]],
                    burial_container = burial_container,
                    plan_date=plan_date and plan_date.strftime('%Y-%m-%d') or None,
                    fact_date=row[3],
                    plan_time=row[4] or None,
                    source_type=Burial.SOURCE_TRANSFERRED,
                    place=place,
                    cemetery=cemetery,
                    area=area,
                    row=row[8],
                    place_number=row[9],
                    responsible=None,       # ! так в закрытых захоронениях
                    grave_number=grave_number,
                    deadman=import_dead_person(row[27:41]),
                    applicant=import_alive_person(row[41:55]),
                    ugh=user.profile.org,
                    applicant_organization=app_org,
                    agent_director=row[57] == 'True',
                    agent=agent,
                    dover=dover,
                    order=Order.objects.create(loru=loru),
                    status=Burial.STATUS_CLOSED,
                    changed=changed_dt,
                    changed_by=user,
                )
                b = Burial.objects.create(**params)

                real_i += 1

                if row[5]:
                    ExhumationRequest.objects.create(
                        burial=b,
                        place=b.place,
                        fact_date=row[5],
                    )

                request = HttpRequest()
                request.user = user
                if not area.name:
                    write_log(request, b, _(u'Участок не был указан'))

                if row[64]:
                    # В файле импорта: Создано: %s %s' % (b.creator, b.added)
                    # В журнал должно уйти: Создано: %s' % (b.creator, )
                    try:
                        created_by = ' '.join(row[64].split(' ')[0:2])
                    except:
                        created_by = row[64]
                    write_log(request, b, created_by)

                write_log(request, b, _(u'Тип до импорта: %s') % row[1])

    return real_i, dupes_i

def do_import_services(csv_fileobj):
    csvreader = UnicodeReader(csv_fileobj)
    try:
        loru = Org.objects.get(inn='4028046796')
    except Org.DoesNotExist:
        loru = None
    for i, row in enumerate(csvreader):
        if i > 0:
            row = map(lambda c: '' if c == 'None' else c, row)
            try:
                Product.objects.get(name=row[0])
            except Product.DoesNotExist:
                Product.objects.create(
                    loru=loru,
                    ptype=None,
                    name=row[0],
                    measure=row[2],
                    price=row[3],
                    default=row[1] == 'True',
                )

@transaction.commit_on_success
def do_import_orders(csv_fileobj):
    csvreader = UnicodeReader(csv_fileobj)
    try:
        loru = Org.objects.get(inn='4028046796')
    except Org.DoesNotExist:
        loru = None
    real_i = 0
    dupes_i = 0
    for i, row in enumerate(csvreader):
        if i > 0:
            if i % 100 == 0:
                transaction.commit()
                gc.collect()
                connection.queries = []
                print 'Processed', i

            row = map(lambda c: '' if c == 'None' else c, row)
            
            all_data = {}
            if row[4]:
                all_data = json.loads(row[4])
                print_data = all_data['print']
                items_data = all_data['positions']
            else:
                all_data = {}
                print_data = {}
                items_data = {}

            try:
                if row[1].lower() == u'биоотходы':
                    o = Order.objects.filter(burial__account_number=row[0], burial__deadman__isnull=True)[0]
                else:
                    o = Order.objects.filter(burial__account_number=row[0], burial__deadman__last_name=row[1],
                                            burial__deadman__first_name=row[2], burial__deadman__middle_name=row[3])[0]

                b = o.get_burial()
                dover = b.dover
                if b.dover and (o.dover is None or o.dover == b.dover):
                    dover = copy.deepcopy(b.dover)
                    dover.id = None
                    dover.target_org = loru
                    dover.save(force_insert=True)

                o.loru = loru
                o.payment = row[5]
                o.applicant = b.applicant
                o.applicant_organization = b.applicant_organization != loru and b.applicant_organization or None
                o.agent_director = b.agent_director
                o.agent = b.agent
                o.dover = dover
                dt = b.changed and b.changed - datetime.timedelta(1) or o.dt or datetime.datetime.now()
                o.dt = datetime.date(year=dt.year, month=dt.month, day=dt.day)
                o.save()

                real_i += 1
            except IndexError:
                print 'Order not found:'
                print ','.join(row[:4])
                dupes_i += 1
                continue
            #else:
                #b = o.get_burial()
                #if b:                                                                                    # !!!! ?????
                    #Order.objects.filter(pk=o.pk).update(agent_director=b.agent_director, agent=b.agent, dover=b.dover)

            for d in items_data:
                if not d['active']:
                    continue
                try:
                    OrderItem.objects.get(order=o, product__name=d.get('order_product') or d.get('service'))
                except OrderItem.DoesNotExist:
                    if d.get('order_product'):
                        try:
                            p = Product.objects.get(name=d['order_product'])
                        except Product.DoesNotExist:
                            p = Product.objects.create(loru=loru, name=d['order_product'], price=d['price'])
                    elif d.get('service'):
                        try:
                            p = Product.objects.get(name=d['service'])
                        except Product.DoesNotExist:
                            p = Product.objects.create(loru=loru, name=d['service'], price=d['price'])

                    OrderItem.objects.create(
                        order=o,
                        product=p,
                        cost=d['price'],
                        quantity=d['count'],
                    )

            if print_data and print_data.get('coffin_size'):
                try:
                    CoffinData.objects.get(order=o)
                except CoffinData.DoesNotExist:
                    CoffinData.objects.create(order=o, size=print_data['coffin_size'])

            if print_data and print_data.get('add_info'):
                try:
                    AddInfoData.objects.get(order=o)
                except AddInfoData.DoesNotExist:
                    AddInfoData.objects.create(order=o, add_info=print_data['add_info'])

            if print_data and print_data.get('catafalque_time') and print_data.get('catafalque_route'):
                try:
                    CatafalqueData.objects.get(order=o)
                except CatafalqueData.DoesNotExist:
                    CatafalqueData.objects.create(
                        order=o,
                        route=print_data['catafalque_route'],
                        start_time=print_data['catafalque_time'],
                        start_place=print_data.get('catafalque_start') or None,
                        end_time=None,
                        cemetery_time=None,
                    )
    return real_i, dupes_i

def do_import_banks(csv_fileobj):
    csvreader = UnicodeReader(csv_fileobj)
    for i, row in enumerate(csvreader):
        if i > 0:
            row = map(lambda c: '' if c == 'None' else c, row)
            try:
                BankAccount.objects.get(ls=row[6])
            except BankAccount.DoesNotExist:
                BankAccount.objects.create(
                    organization=Org.objects.get_or_create(inn=row[0], full_name=row[1])[0],
                    rs=row[2],ks=row[3],bik=row[4],bankname=row[5],ls=row[6]
                )

def do_import_docs(csv_fileobj):
    """Ф,И,О,Тип,Серия,Номер,Кем выдан,Когда выдан"""
    csvreader = UnicodeReader(csv_fileobj)
    for i, row in enumerate(csvreader):
        if i > 0:
            row = map(lambda c: '' if c == 'None' else c, row)
            try:
                PersonID.objects.get(person__last_name=row[0], person__first_name=row[1], series=row[4], number=row[5])
            except PersonID.DoesNotExist:
                id_type, _created = IDDocumentType.objects.get_or_create(name=row[3])
                source, _created = DocumentSource.objects.get_or_create(name=row[6])
                PersonID.objects.create(
                    person=AlivePerson.objects.get_or_create(last_name=row[0], first_name=row[1], middle_name=row[2])[0],
                    id_type=id_type, series=row[4], number=row[5], source=source, date=row[7] or None
                )

def do_import_dcs(csv_fileobj):
    """Ф,И,О,Серия,Номер,Когда выдан,ЗАГС"""
    real_i = 0
    dupes_i = 0
    csvreader = UnicodeReader(csv_fileobj)
    for i, row in enumerate(csvreader):
        if i > 0:
            row = map(lambda c: '' if c == 'None' else c, row)
            try:
                DeathCertificate.objects.get(person__last_name=row[0], person__first_name=row[1], series=row[3], s_number=row[4])
            except DeathCertificate.DoesNotExist:
                zags, _created = Org.objects.get_or_create(name=row[6], type=Org.PROFILE_ZAGS)
                try:
                    person=DeadPerson.objects.get(last_name=row[0], first_name=row[1], middle_name=row[2])
                except DeadPerson.MultipleObjectsReturned:
                    print 'Duplicate dead person(s) for a death certificate:'
                    print ",".join(row)
                    dupes_i += 1
                except DeadPerson.DoesNotExist:
                    print 'Dead person not found for a death certificate:'
                    print ",".join(row)
                    dupes_i += 1
                else:
                    if DeathCertificate.objects.filter(person=person):
                        print 'Dead person already exists in the death certificate table:'
                        print ",".join(row)
                        dupes_i += 1
                        continue
                    try:
                        DeathCertificate.objects.create(
                            person=person,
                            series=row[4], s_number=row[3], zags=zags, release_date=row[5]
                        )
                        real_i += 1
                    except ValidationError:             # дата пустая или неверная
                        dupes_i += 1
    return real_i, dupes_i
