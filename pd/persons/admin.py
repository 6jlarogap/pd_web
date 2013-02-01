from django.contrib import admin

from persons.models import IDDocumentType, ZAGS

class IDDocumentTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(IDDocumentType, IDDocumentTypeAdmin)

class ZAGSAdmin(admin.ModelAdmin):
    pass

admin.site.register(ZAGS, ZAGSAdmin)

