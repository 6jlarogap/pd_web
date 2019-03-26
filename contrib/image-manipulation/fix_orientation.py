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

from burials.models import PlacePhoto, AreaPhoto
from orders.models import Product

# На сколько градусов надо крутить при различных значениях
# exif taga'a Orientation
#
rotate_howto = {
    3: 180,
    6: 270,
    8: 90,
}

cnt_total = cnt_rotated = 0
for model in (PlacePhoto, AreaPhoto, Product):
    for model in model.objects.all():
        photo_file = model.bfile if model in (PlacePhoto, AreaPhoto, ) else model.photo
        if photo_file and os.path.exists(photo_file.path):
            cnt_total += 1
            f = open(photo_file.path, 'rb')
            tags = exifread.process_file(f, details=False)
            if tags and 'Image Orientation' in tags:
                orientation = tags['Image Orientation'].values[0]
                if orientation in rotate_howto:
                    print("%s to rotate at %d degrees" % (photo_file.path, rotate_howto[orientation], ))
                    im1 = Image.open(photo_file.path)
                    im2 = im1.rotate(rotate_howto[orientation])
                    im2.save(photo_file.path)
                    cnt_rotated += 1
            f.close()
print("%d of total %d photos rotated" % (cnt_rotated, cnt_total, ))
