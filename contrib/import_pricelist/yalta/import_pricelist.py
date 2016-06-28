# coding=utf-8

# import_pricelist.py,

TO_IMPORT_ODS = '/home/suprune20/musor/pricelist.ods'
PHOTOS_FOLDER = '/home/suprune20/musor/product-photo'
# Название организации изменено, чтоб еще раз сдуру не запустить процесс
LORU_NAME = u'ООО "ЯЛТИНСКАЯ ПОХОРОННАЯ КОМПАНИЯ" ---'

# Импортировать товары лору LORU_NAME из таблицы TO_IMPORT_ODS
# Сделать эти товары предназначенными для показа оптовикам,
#
# Запуск из ./manage.py shell :
# execfile('../contrib/import_pricelist/import_pricelist.py')

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
    no = 1
    count = 0
    for row in rows[1:]:
        # Самая первая строка в листе -- заголовок
        no += 1
        try:
            cells = row.getElementsByType(TableCell)
            sku = ods_cell(cells[0])
            name = ods_cell(cells[1])
            description = ''
            measure = ods_cell(cells[2])
            price_str = ods_cell(cells[3]).replace(' ', '')
            try:
                price = price_wholesale = float(price_str)
            except ValueError:
                # цена не указана, значит конец списка
                print u'Ok. End of List (Price ValueError). %s products imported' % count
                break
            try:
                productcategory = ProductCategory.objects.get(name=ods_cell(cells[4]))
            except ProductCategory.DoesNotExist:
                print '**** line %d' % no
                raise
            p = Product.objects.create(
                loru=loru,
                name=name,
                description=description,
                productcategory=productcategory,
                price=price,
                price_wholesale=price_wholesale,
                sku=sku,
            )
            if not p.sku:
                p.sku = str(p.pk)
                p.save()
            count += 1
            # print no, sku, name, measure, price
            fname = ods_cell(cells[5])
            if fname:
                fname = u"%s.png" % fname
                f = open(os.path.join(PHOTOS_FOLDER, fname), 'r')
                s = f.read()
                f.close()
                p.photo.save(fname, ContentFile(s))
        except IndexError:
            # тоже конец списка
            print u'Ok. End of List (IndexError). %s products imported' % count
            break

def ods_cell(cell):
    return "".join([unicode(data) for data in cell.getElementsByType(P)]).strip()

main()