# -*- coding: utf-8 -*-

import sys, os, codecs

from django.core.management.base import BaseCommand
from django.template import loader, Context

from django.conf import settings

from orders.models import ProductStatus, ProductHistory
from users.models import Org


class Command(BaseCommand):
    args = '<front-end url> (default: https://pohoronnoedelo.ru)>'
    help = 'Create sitemap.xml'
    
    def handle(self, *args, **options):
        sitemap = os.path.join(settings.MEDIA_ROOT, 'sitemap.xml')
        try:
            url = args[0]
        except IndexError:
            url = 'https://pohoronnoedelo.ru'
        if not url.endswith('/'):
            url += '/'

        catalog_org_pk = Org.get_catalog_org_pk()
        product_statuses = ProductStatus.objects.filter(
            status__in=(ProductHistory.PRODUCT_OPERATION_PUBLISH, ProductHistory.PRODUCT_OPERATION_UPDATE, ),
            ugh__pk=catalog_org_pk,
        )

        t = loader.get_template('sitemap.xml')
        xml = unicode(t.render(Context({
            'product_statuses': product_statuses,
            'url': url,
        })))
        
        with codecs.open(sitemap, 'w', encoding='utf-8') as f:
            f.write(xml)
