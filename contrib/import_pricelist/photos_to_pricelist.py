# coding=utf-8

# photos_to_pricelist.py,

# TO_IMPORT_ODS = '/home/suprune20/musor/import_pricelist/pricelist-arnika.ods'
TO_IMPORT_ODS = '/home/suprune20/musor/pricelist.ods'
PHOTOS_FOLDER = '/home/suprune20/musor/product-photo'
# Название организации изменено, чтоб еще раз не запустить процесс
LORU_NAME = u'ЧТУП "ОПТОМИКСБРЕСТ"'

# Считать товары, изменить фотки товаров. Товары ищутся по именам,
# так что не должно быть дублирующих имен
#
# Запуск из ./manage.py shell :
# execfile('../contrib/import_pricelist/photos_to_pricelist.py')

# Требования:
# -----------
# * python-odfpy

import os

from odf.opendocument import load
from odf.opendocument import Spreadsheet
from odf.text import P
from odf.table import TableRow, TableCell

from django.db import transaction
from django.core.files.base import ContentFile

from users.models import Org
from orders.models import Product, ProductCategory

@transaction.commit_on_success
def main():
    loru = Org.objects.get(name=LORU_NAME)
    ods = load(TO_IMPORT_ODS).spreadsheet
    rows = ods.getElementsByType(TableRow)
    for row in rows[1:]:
        try:
            cells = row.getElementsByType(TableCell)
            name = ods_cell(cells[1])
            if not name:
                break
            product = Product.objects.get(loru=loru, name=name)
            fname = ods_cell(cells[5])
            if fname:
                fname = u"%s.jpg" % fname
                f = open(os.path.join(PHOTOS_FOLDER, fname), 'r')
                s = f.read()
                f.close()
                product.photo.save(fname, ContentFile(s))
        except IndexError:
            # тоже конец списка
            break

def ods_cell(cell):
    return "".join([unicode(data) for data in cell.getElementsByType(P)]).strip()

main()