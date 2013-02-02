from django.contrib import admin

from burials.models import Cemetery, BurialRequest
from burials.forms import CemeteryAdminForm


class CemeteryAdmin(admin.ModelAdmin):
    form = CemeteryAdminForm

admin.site.register(Cemetery, CemeteryAdmin)

class BurialRequestAdmin(admin.ModelAdmin):
    pass

admin.site.register(BurialRequest, BurialRequestAdmin)
