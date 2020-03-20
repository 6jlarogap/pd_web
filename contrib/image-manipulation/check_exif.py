# coding: utf-8

# До сих пор пользовались модулем exifread для получения ориентации,
# сейчас надо перейти к piexif, который позволяет сохранять exif
# Надо проверить все наши фотки, как у piexif с ориентацией, 
# относительно надежно зарекомендовавший себя модуля exifread

import datetime, piexif, exifread

try:
    from PIL import Image, ImageChops, ImageFilter
except ImportError:
    import Image
    import ImageChops
    import ImageFilter

from django.conf import settings
from burials.models import PlacePhoto

d_final = datetime.datetime(2016, 10, 31, 0, 0, 0)

count = count_exif = 0
for ph in PlacePhoto.objects.filter(dt_modified__lt=d_final).iterator(chunk_size=100):
    count += 1
    if not ph.bfile:
        continue
    try:
        f = open(str(ph.bfile.path), 'rb')
        tags = exifread.process_file(f, details=False)
        try:
            exifread_orientation = tags['Image Orientation'].values[0]
        except (AttributeError, KeyError, IndexError):
            exifread_orientation = None
        f.close()
        if exifread_orientation:
            count_exif += 1
            im = Image.open(str(ph.bfile.path))
            exif_dict = piexif.load(im.info["exif"])
            try:
                piexif_orientation = exif_dict["0th"][piexif.ImageIFD.Orientation]
            except KeyError:
                print(("piexif: orientation not found: %s" % ph.bfile.path))
            im.close()
            if piexif_orientation != exifread_orientation:
                print((" piexif_orientation (%s) != exifread_orientation (%s): %s" % (
                    piexif_orientation,
                    exifread_orientation,
                )))
                print(("url", ph.place.url()))
                print(("ugh", ph.place.cemetery.ugh.name))
                break
    except IOError:
        print(("Not found: %s" % ph.bfile.path))

print(("\n", "count all", count, ", count with exif", count_exif))
