# -*- coding: utf-8 -*-

import sys, os, codecs, datetime

from django.core.management.base import BaseCommand
from django.template import loader, Context

from django.conf import settings

from orders.models import Product, ProductStatus, ProductHistory
from users.models import Org


class Command(BaseCommand):
    args = '<front-end url> (default: https://pohoronnoedelo.ru)>'
    help = 'Create sitemap.xml'
    
    def handle(self, *args, **options):
        sitemap = os.path.join(settings.MEDIA_ROOT, 'sitemap.xml')
        sitemap_temp = u"%s.TMP" % sitemap
        try:
            url = args[0]
        except IndexError:
            url = 'https://pohoronnoedelo.ru'
        if not url.endswith('/'):
            url += '/'

        published_statuses = (
            ProductHistory.PRODUCT_OPERATION_PUBLISH,
            ProductHistory.PRODUCT_OPERATION_UPDATE,
        )
        catalog_org_pk = Org.get_catalog_org_pk()
        product_statuses = ProductStatus.objects.filter(
            status__in=published_statuses,
            ugh__pk=catalog_org_pk,
        )
        
        # Поставщики: дата их последней модификации является датой,
        # когда они внесли свой последний опубликованный товар
        suppliers = Product.objects.filter(
            productstatus__status__in=published_statuses,
            productstatus__ugh__pk=catalog_org_pk,
        ).order_by('loru__slug','-productstatus__dt',). \
        values('loru__slug', 'productstatus__dt',).\
        distinct('loru__slug',)

        t = loader.get_template('sitemap.xml')
        xml = unicode(t.render(Context({
            'product_statuses': product_statuses,
            'suppliers': suppliers,
            'url': url,
        })))
        
        with codecs.open(sitemap_temp, 'w', encoding='utf-8') as f:
            f.write(xml)
        try:
            os.remove(sitemap)
        except OSError:
            pass
        os.rename(sitemap_temp, sitemap)
