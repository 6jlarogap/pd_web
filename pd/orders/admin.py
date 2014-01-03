from django.contrib import admin

from orders.models import Product, Order, OrderItem, ProductCategory


class ProductAdmin(admin.ModelAdmin):
    pass

class ProductCategoryAdmin(admin.ModelAdmin):
    pass

class OrderItemInline(admin.TabularInline):
    model = OrderItem

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, ]

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductCategory, ProductCategoryAdmin)
admin.site.register(Order, OrderAdmin)
