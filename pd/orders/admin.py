from django.contrib import admin

from orders.models import Product, Order, OrderItem, ProductCategory, ProductStatus


class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'loru', 'name', )

admin.site.register(Product, ProductAdmin)

class ProductCategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(ProductCategory, ProductCategoryAdmin)

class ProductStatusAdmin(admin.ModelAdmin):
    pass

admin.site.register(ProductStatus, ProductStatusAdmin)

class OrderItemInline(admin.TabularInline):
    model = OrderItem

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, ]

admin.site.register(Order, OrderAdmin)
