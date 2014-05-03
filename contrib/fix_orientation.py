# coding=utf-8


# fix_orientation.py,
#
# Исправить ориентацию фотографий, снятых с мобильного приложения
#
# Запуск из ./manage.py shell :
# execfile('/path/to/fix_orientation.py')

# Требования:
#   - pip-installed ExifRead в virtualenv

import os

from PIL import Image 
import exifread

from burials.models import GravePhoto, PlacePhoto, AreaPhoto

# На сколько градусов надо крутить при различных значениях
# exif taga'a Orientation
#
rotate_howto = {
    3: 180,
    6: 270,
    8: 90,
}

cnt_total = cnt_rotated = 0
for model in (GravePhoto, PlacePhoto, AreaPhoto, ):
    for photo in model.objects.all():
        if photo.bfile and os.path.exists(photo.bfile.path):
            cnt_total += 1
            f = open(photo.bfile.path, 'rb')
            tags = exifread.process_file(f, details=False)
            if tags and 'Image Orientation' in tags:
                orientation = tags['Image Orientation'].values[0]
                if orientation in rotate_howto:
                    print "%s to rotate at %d degrees" % (photo.bfile.path, rotate_howto[orientation], )
                    im1 = Image.open(photo.bfile.path)
                    im2 = im1.rotate(rotate_howto[orientation])
                    im2.save(photo.bfile.path)
                    cnt_rotated += 1
            f.close()
print "%d of total %d photos rotated" % (cnt_rotated, cnt_total, )
