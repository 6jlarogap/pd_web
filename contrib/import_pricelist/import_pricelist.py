# coding=utf-8

# import_pricelist.py,

TO_IMPORT_ODS = '/home/suprune20/musor/pricelist.ods'
PHOTOS_FOLDER = '/home/suprune20/musor/product-photo'
# Название организации изменено, чтоб еще раз сдуру не запустить процесс
LORU_NAME = u'ИП Дащинская С.В.---'

# Импортировать товары лору LORU_NAME из таблицы TO_IMPORT_ODS
# Сделать эти товары предназначенными для показа оптовикам,
# если указана ненулевая цена, иначе поставщик сам укажет
# потом цену и внесет ва оптовый каталог
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

@transaction.atomic
def main():
    loru = Org.objects.get(name=LORU_NAME)
    ods = load(TO_IMPORT_ODS).spreadsheet
    rows = ods.getElementsByType(TableRow)
    no = 1
    for row in rows[1:]:
        no += 1
        try:
            cells = row.getElementsByType(TableCell)
            sku = ods_cell(cells[0])
            name = ods_cell(cells[1])
            description = ods_cell(cells[2])
            try:
                price = price_wholesale = float(ods_cell(cells[3]))
            except ValueError:
                # цена не указана, значит конец списка
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
                is_wholesale=bool(price),
            )
            if not p.sku:
                p.sku = str(p.pk)
                p.save()
            fname = ods_cell(cells[5])
            if fname:
                fname = u"%s.png" % fname
                f = open(os.path.join(PHOTOS_FOLDER, fname), 'r')
                s = f.read()
                f.close()
                p.photo.save(fname, ContentFile(s))
        except IndexError:
            # тоже конец списка
            break

def ods_cell(cell):
    return "".join([unicode(data) for data in cell.getElementsByType(P)]).strip()

main()
