# -*- coding: utf-8 -*-

import sys, os

from django.core.management.base import BaseCommand
from django.template import loader, Context

from django.conf import settings

from orders.models import Product, ProductHistory
from users.models import Org


class Command(BaseCommand):
    args = '<sitemap.xml location(default: <settings.MEDIA_ROOT>/sitemap.xml)>'
    help = 'Create sitemap.xml'
    
    def handle(self, *args, **options):
        try:
            sitemap = args[0]
        except IndexError:
            sitemap = os.path.join(settings.MEDIA_ROOT, 'sitemap.xml')

        catalog_org_pk = Org.get_catalog_org_pk()
        published_products = Product.objects.filter(
            productstatus__status__in=\
                (ProductHistory.PRODUCT_OPERATION_PUBLISH, ProductHistory.PRODUCT_OPERATION_UPDATE, ),
                productstatus__ugh__pk=catalog_org_pk,
        )

        t = loader.get_template('sitemap.xml')
        print t.render(Context({ 'published_products': published_products }))
        
        for p in published_products:
            print p.productstatus.dt

