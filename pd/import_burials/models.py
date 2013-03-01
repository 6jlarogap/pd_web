# coding=utf-8
import csv
import cStringIO
import codecs

from geo.models import Location, Country, LocationFIAS, DFiasAddrobj, Region, City, Street
from users.models import Org


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
                    org.off_address = Location.objects.create(
                        country = Country.objects.get(name=row[4]),
                        house = row[8],
                        block = row[9],
                        building = row[10],
                        flat = row[11],
                    )
                    fias_street = None
                    if row[4] == u'Россия':
                        fias_street = DFiasAddrobj.objects.get_streets(row[4], row[5], row[6], row[7])[0]

                    if fias_street:
                        fias_parent = fias_street
                        while fias_parent:
                            LocationFIAS.objects.create(
                                loc = org.off_address,
                                guid = fias_parent.aoguid,
                                name = u'%s %s' % (fias_parent.shortname, fias_parent.formalname),
                                level = fias_parent.aolevel,
                            )
                            try:
                                fias_parent = DFiasAddrobj.objects.get(aoguid=fias_parent.parentguid, actstatus=1)
                            except DFiasAddrobj.DoesNotExist:
                                fias_parent = None
                    else:
                        org.off_address.region = Region.objects.get_or_create(country=org.off_address.country, name=row[5])
                        org.off_address.city = City.objects.get_or_create(region=org.off_address.region, name=row[6])
                        org.off_address.street = Street.objects.get_or_create(street=org.off_address.city, name=row[7])

                    org.off_address.save()
