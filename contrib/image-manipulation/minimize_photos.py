# coding: utf-8

# Минимизировать размер фото

import datetime, gc, piexif

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from PIL import Image, ImageChops, ImageFilter
except ImportError:
    import Image
    import ImageChops
    import ImageFilter

from django.conf import settings

from burials.models import PlacePhoto
from restthumbnails.files import ThumbnailContentFile

d_final = datetime.datetime(2016, 10, 31, 0, 0, 0)

count = count_modified = 0
for ph in PlacePhoto.objects.filter(
                dt_modified__lt=d_final,
                ).iterator():
    count += 1
    image = None

    if not ph.bfile:
        print u"Empty bfile: %s" % ph.pk
        continue

    try:
        f = open(unicode(ph.bfile.path), 'rb')
    except IOError:
        print u"Not found : %s" % ph.bfile.path
        continue

    buff = f.read()
    try:
        image = Image.open(StringIO(buff))
        image.load()
    except IOError:
        print u"Not image file: %s" % ph.bfile.path
        continue

    if image.size[0] * image.size[1] >= 1600*1200:
        image.close()
        image = None
        f = open(unicode(ph.bfile.path), 'rb')
        photo_content = ThumbnailContentFile(
            f,
            quality=30,
            minsize=1600*1200,
        ).generate()
        photo_content = photo_content.read()
        f = open(unicode(ph.bfile.path), 'wb')
        f.write(photo_content)
        f.close()
        PlacePhoto.objects.filter(pk=ph.pk).update(dt_modified=datetime.datetime.now())
        count_modified += 1
    else:
        print u"Low resolution : %s x %s, %s" % (
            image.size[0], image.size[1],
            ph.bfile.path
        )
    if image:
        image.close()
    buff = image = None
    gc.collect()

    # Будем частями, ибо 80000+ фоток,
    # мало ли что: утечки памяти и т.п.
    #
    if count >= 10000:
        break

    if count % 250 == 0:
        print "count all", count, ", count modified", count_modified

print "\n", "count all", count, ", count modified", count_modified
