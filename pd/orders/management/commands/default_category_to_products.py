# -*- coding: utf-8 -*-

import sys

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _
from django.db import IntegrityError

from orders.models import Product, ProductCategory

class Command(BaseCommand):
    help = ""

    def handle(self, *args, **kwargs):
        """
        Заполнить товары категориями, где они еще не заполнены
        """
        print('*** Filling Product items with the default ProductCategory, if neccessary')
        for pc in (_('Прочие товары'), _('Прочие услуги'), ):
            try:
                ProductCategory.objects.get(name=pc).delete()
            except (IntegrityError, ProductCategory.DoesNotExist, ):
                pass
        category_default, created = ProductCategory.objects.get_or_create(
            name=_('Прочие товары и услуги'),
        )
        if not created:
            print('!!! WARNING: Default ProductCategory already existed')
        n_filled = Product.objects.filter(productcategory__isnull=True).update(productcategory=category_default)
        print('*** %d products filled' % (n_filled, ))
