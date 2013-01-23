# -*- coding: utf-8 -*-

from django.contrib import admin

from burials.admin import OwnedObjectsAdmin
from orders.models import Product


class ProductAdmin(OwnedObjectsAdmin):
    list_display = ['id', 'name', 'creator', 'type', 'price']
    list_editable = ['name', 'type', 'price']
    list_display_links = ['id']

admin.site.register(Product, ProductAdmin)

