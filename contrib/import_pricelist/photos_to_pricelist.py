# coding=utf-8

# photos_to_pricelist.py,

# TO_IMPORT_ODS = '/home/suprune20/musor/import_pricelist/pricelist-arnika.ods'
TO_IMPORT_ODS = '/home/suprune20/musor/pricelist.ods'
PHOTOS_FOLDER = '/home/suprune20/musor/product-photo'
# Название организации изменено, чтоб еще раз сдуру не запустить процесс
LORU_NAME = u'ЧТУП "ОПТОМИКСБРЕСТ"-----'

# Считать товары, изменить фотки товаров. Товары ищутся по
# имени + артикул, так что не должно быть дубля имя+артикул
# у прикрепляемой фотки.
#
# Запуск из ./manage.py shell :
# execfile('../contrib/import_pricelist/photos_to_pricelist.py')

# Требования:
# -----------
# * python-odfpy

import os, shutil

from odf.opendocument import load
from odf.opendocument import Spreadsheet
from odf.text import P
from odf.table import TableRow, TableCell

from django.conf import settings
from django.core.files.base import ContentFile

from users.models import Org
from orders.models import Product, ProductCategory

def main():
    loru = Org.objects.get(name=LORU_NAME)
    ods = load(TO_IMPORT_ODS).spreadsheet
    rows = ods.getElementsByType(TableRow)
    # 0-й ряд -- заголовок таблицы
    for row in rows[1:]:
        try:
            cells = row.getElementsByType(TableCell)
            name = ods_cell(cells[1])
            if not name:
                # конец списка
                break
            fname = ods_cell(cells[5])
            if fname:
                print ''
                print 'photo: %s' % fname
                sku = ods_cell(cells[0])
                product = Product.objects.get(
                    loru=loru,
                    name=name,
                    sku=sku,
                    )
                print "product: name='%s', sku='%s'" % (product.name, product.sku)
                fname = u"%s.jpg" % fname
                f = open(os.path.join(PHOTOS_FOLDER, fname), 'r')
                s = f.read()
                f.close()
                if product.photo and product.photo.path:
                    print 'product is with a photo: %s' % product.photo.name
                    if os.path.exists(product.photo.path):
                        try:
                            os.remove(product.photo.path)
                            print 'existing product photo is removed'
                        except IOError:
                            pass
                    thmb = os.path.join(settings.THUMBNAILS_STORAGE_ROOT, product.photo.name)
                    if os.path.exists(thmb):
                        shutil.rmtree(thmb, ignore_errors=True)
                        print 'existing product thumbnails are removed'
                product.photo.save(fname, ContentFile(s))
                print 'product photo is saved'
        except IndexError:
            # тоже конец списка
            break

def ods_cell(cell):
    return "".join([unicode(data) for data in cell.getElementsByType(P)]).strip()

main()
