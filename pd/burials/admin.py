from django.contrib import admin

from burials.models import Cemetery, BurialRequest, Reason, Area, Place
from burials.forms import CemeteryAdminForm


class AreaInine(admin.TabularInline):
    model = Area

class CemeteryAdmin(admin.ModelAdmin):
    form = CemeteryAdminForm

admin.site.register(Cemetery, CemeteryAdmin)

class BurialRequestAdmin(admin.ModelAdmin):
    pass

admin.site.register(BurialRequest, BurialRequestAdmin)

class ReasonAdmin(admin.ModelAdmin):
    pass

admin.site.register(Reason, ReasonAdmin)

class PlaceAdmin(admin.ModelAdmin):
    pass

admin.site.register(Place, PlaceAdmin)

