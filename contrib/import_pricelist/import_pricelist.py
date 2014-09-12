# coding=utf-8

# import_pricelist.py,

# TO_IMPORT_ODS = '/home/suprune20/musor/import_pricelist/pricelist-arnika.ods'
TO_IMPORT_ODS = '/home/suprune20/musor/import_pricelist/pricelist-optomiks-2.ods'
# Название организации изменено, чтоб еще раз не запустить процесс
LORU_NAME = u'ЧТУП "ОПТОМИКСБРЕСТ"'

# Импортировать товары лору LORU_NAME из таблицы TO_IMPORT_ODS
# Сделать эти товары предназначенными для показа оптовикам
#
# Запуск из ./manage.py shell :
# execfile('../contrib/import_pricelist/import_pricelist.py')

# Требования:
# -----------
# * python-odfpy

from odf.opendocument import load
from odf.opendocument import Spreadsheet
from odf.text import P
from odf.table import TableRow, TableCell

from django.db import transaction

from users.models import Org
from orders.models import Product, ProductCategory

@transaction.commit_on_success
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
                currency=loru.currency,
                sku=sku,
                is_wholesale=True,
            )
            if not p.sku:
                p.sku = str(p.pk)
                p.save()
        except IndexError:
            # тоже конец списка
            break

def ods_cell(cell):
    return "".join([unicode(data) for data in cell.getElementsByType(P)]).strip()

main()