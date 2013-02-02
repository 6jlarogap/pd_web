from django.contrib import admin

from persons.models import IDDocumentType

class IDDocumentTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(IDDocumentType, IDDocumentTypeAdmin)
