from django.contrib import admin

from burials.models import Cemetery, BurialRequest, Reason, Area, Place, Burial
from burials.forms import CemeteryAdminForm


class AreaInine(admin.TabularInline):
    model = Area

class CemeteryAdmin(admin.ModelAdmin):
    form = CemeteryAdminForm
    inlines = [AreaInine, ]

admin.site.register(Cemetery, CemeteryAdmin)

class BurialRequestAdmin(admin.ModelAdmin):
    pass

admin.site.register(BurialRequest, BurialRequestAdmin)

class ReasonAdmin(admin.ModelAdmin):
    list_display = ['name', 'reason_type', 'text',]
    list_filter = ['reason_type',]

admin.site.register(Reason, ReasonAdmin)

class PlaceAdmin(admin.ModelAdmin):
    pass

admin.site.register(Place, PlaceAdmin)

class BurialAdmin(admin.ModelAdmin):
    pass

admin.site.register(Burial, BurialAdmin)

