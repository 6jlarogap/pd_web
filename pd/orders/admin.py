from django.contrib import admin

from orders.models import Product, Order, OrderItem


class ProductAdmin(admin.ModelAdmin):
    pass

admin.site.register(Product, ProductAdmin)

class OrderItemInline(admin.TabularInline):
    model = OrderItem

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, ]

admin.site.register(Order, OrderAdmin)
