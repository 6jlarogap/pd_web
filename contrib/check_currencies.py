# -*- coding: utf-8 -*-

# Запуск из ./manage.py shell :
# execfile('/path/to/script_name.py')

from users.models import Org
from orders.models import Product

for o in Org.objects.filter(type='loru').order_by('off_address__country'):
    products_currency = None
    same_currency = True
    if o.off_address and o.off_address.country:
        country = o.off_address.country
    else:
        country = 'Undefined'
    for p in Product.objects.filter(loru=o):
        if products_currency is None:
            products_currency = p.currency
        else:
            if p.currency != products_currency:
                same_currency = False
    print "Loru=%s, currency=%s, country=%s" % (o.name, o.currency, country)
    if products_currency is None:
        print " No products found"
    elif not same_currency:
        print " !!! different curriencies in products"
    elif products_currency != o.currency:
        print " Currency of products is the same: %s. Differs from Org.currency: %s" % (products_currency, o.currency)
    else:
        print " OK. Currency of products is the same: %s. The same as Org.currency" % (products_currency)
