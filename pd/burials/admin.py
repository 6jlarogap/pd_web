from django.contrib import admin

from burials.models import Cemetery


class CemeteryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Cemetery, CemeteryAdmin)
