# coding=utf-8
import csv
import cStringIO
import datetime
import codecs
from django.contrib.auth.models import User
from django.http import HttpRequest

from django.utils.translation import ugettext as _

from burials.models import Burial, ExhumationRequest, Cemetery, Area, Place
from geo.models import Location, Country, LocationFIAS, DFiasAddrobj, Region, City, Street
from logs.models import write_log
from pd.models import UnclearDate
from persons.models import AlivePerson, DeadPerson
from users.models import Org, Profile, Dover


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
    fias_street = None
    if location_data[4] == u'Россия':
        fias_street = DFiasAddrobj.objects.get_streets(location_data[0], location_data[1], location_data[2], location_data[3])[0]

    if fias_street:
        fias_parent = fias_street
        while fias_parent:
            LocationFIAS.objects.create(
                loc = location,
                guid = fias_parent.aoguid,
                name = u'%s %s' % (fias_parent.shortname, fias_parent.formalname),
                level = fias_parent.aolevel,
                )
            try:
                fias_parent = DFiasAddrobj.objects.get(aoguid=fias_parent.parentguid, actstatus=1)
            except DFiasAddrobj.DoesNotExist:
                fias_parent = None
    else:
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
        pd_bits = map(int, pd_bits)
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
    if not any([f,i,o]):
        return None
    try:
        return DeadPerson.objects.get(last_name=f, first_name=i, middle_name=o)
    except DeadPerson.DoesNotExist:
        dp = DeadPerson.objects.create(
            last_name=f,
            first_name=i,
            middle_name=o,
            birth_date=make_unc_date(data[3]),
            death_date=make_unc_date(data[4]),
        )
        if data[5]:
            dp.address = import_location(data[5:13])
            dp.save()

        return dp

def do_import_burials(csv_fileobj, user):
    csvreader = UnicodeReader(csv_fileobj)
    BURIAL_TYPES = {
        u'Захоронение': Burial.BURIAL_NEW,
        u'Подзахоронение к существ': Burial.BURIAL_ADD,
        u'Захоронение в существующ': Burial.BURIAL_OVER,
        u'Урна': Burial.BURIAL_URN,
    }
    for i, row in enumerate(csvreader):
        if i > 0:
            row = map(lambda c: '' if c == 'None' else c, row)
            try:
                cemetery = Cemetery.objects.get(name=row[6])
            except Cemetery.DoesNotExist:
                cemetery = Cemetery.objects.create(name=row[6], time_begin='10:00', time_end='17:00')
            try:
                b = Burial.objects.get(cemetery=cemetery, account_number=row[0])
            except Burial.DoesNotExist:
                area = None
                area, _created = Area.objects.get_or_create(name=row[7] or '', cemetery=cemetery)


                place, _created = Place.objects.get_or_create(
                    cemetery=cemetery,
                    area=area,
                    row=row[8],
                    place=row[9],
                    places_count=row[10],
                )
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

                if row[57]:
                    fm = u'%s %s' % (row[58] or '', row[59] or '')
                    fm = fm.strip()[:30]
                    try:
                        agent = Profile.objects.get(
                            user__last_name=row[57], user__first_name=fm, org=app_org, is_agent=True
                        )
                    except Profile.DoesNotExist:

                        agent = Profile.objects.create(
                            user=User.objects.create(
                                last_name=row[57], first_name=fm, username='imported_%s' % i,
                            ), org=app_org, is_agent=True
                        )
                if agent and row[60]:
                    dover, _created = Dover.objects.get_or_create(
                        agent=agent,
                        number=row[60],
                        begin=row[61],
                        end=row[62],
                    )

                params = dict(
                    account_number=row[0],
                    burial_type=BURIAL_TYPES[row[1]],
                    plan_date=make_unc_date(row[2]).strftime('%Y-%m-%d'),
                    fact_date=row[3],
                    plan_time=row[4] or None,
                    source_type=Burial.SOURCE_ARCHIVE,
                    place=place,
                    cemetery=cemetery,
                    area=area,
                    row=row[9],
                    place_number=row[10],
                    responsible=import_alive_person(data=row[12:26]),
                    grave_number=row[26] or 1,
                    deadman=import_dead_person(row[27:41]),
                    applicant=import_alive_person(row[41:55]),
                    ugh=user.profile.org,
                    applicant_organization=app_org,
                    agent_director=False,
                    agent=agent,
                    dover=dover,
                    order=None,
                    status=Burial.STATUS_CLOSED,
                    changed=datetime.datetime.now(),
                    changed_by=user,
                )
                b = Burial.objects.create(**params)

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
                    write_log(request, b, _(u'Комментарий: %s') % row[64])
