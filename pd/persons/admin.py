from django.contrib import admin

from persons.models import IDDocumentType, DocumentSource


class IDDocumentTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(IDDocumentType, IDDocumentTypeAdmin)

class DocumentSourceAdmin(admin.ModelAdmin):
    pass

admin.site.register(DocumentSource, DocumentSourceAdmin)

