from django.contrib import admin

# This is test sync from pd_web.

from burials.models import Cemetery, Burial, Reason, Area, Place, AreaPurpose, ExhumationRequest
from burials.forms import CemeteryAdminForm


class AreaInine(admin.TabularInline):
    model = Area
    can_delete = False

class CemeteryAdmin(admin.ModelAdmin):
    form = CemeteryAdminForm
    inlines = [AreaInine, ]

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Cemetery, CemeteryAdmin)

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

