from django.contrib import admin

from persons.models import IDDocumentType, DocumentSource, DeadPerson, AlivePerson, PersonID, DeathCertificate


class IDDocumentTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(IDDocumentType, IDDocumentTypeAdmin)

class DocumentSourceAdmin(admin.ModelAdmin):
    pass

admin.site.register(DocumentSource, DocumentSourceAdmin)

class DeadPersonAdmin(admin.ModelAdmin):
    pass

admin.site.register(DeadPerson, DeadPersonAdmin)

class AlivePersonAdmin(admin.ModelAdmin):
    pass

admin.site.register(AlivePerson, AlivePersonAdmin)

class PersonIDAdmin(admin.ModelAdmin):
    pass

admin.site.register(PersonID, PersonIDAdmin)

class DeathCertificateAdmin(admin.ModelAdmin):
    pass

admin.site.register(DeathCertificate, DeathCertificateAdmin)


