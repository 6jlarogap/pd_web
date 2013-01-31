from django.contrib import admin

from burials.models import Cemetery, BurialRequest


class CemeteryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Cemetery, CemeteryAdmin)

class BurialRequestAdmin(admin.ModelAdmin):
    pass

admin.site.register(BurialRequest, BurialRequestAdmin)
