from django.contrib import admin

from burials.models import Cemetery, Burial, Reason, Area, Place, AreaPurpose, ExhumationRequest

class AreaInine(admin.TabularInline):
    model = Area
    can_delete = False

class AreaPurposeAdmin(admin.ModelAdmin):
    pass

admin.site.register(AreaPurpose, AreaPurposeAdmin)

class BurialAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'burial_type', 'source_type', ]

admin.site.register(Burial, BurialAdmin)

class ReasonAdmin(admin.ModelAdmin):
    list_display = ['name', 'reason_type', 'text',]
    list_filter = ['reason_type',]

admin.site.register(Reason, ReasonAdmin)

class PlaceAdmin(admin.ModelAdmin):
    pass

admin.site.register(Place, PlaceAdmin)

class ExhumationRequestAdmin(admin.ModelAdmin):
    pass

admin.site.register(ExhumationRequest, ExhumationRequestAdmin)

