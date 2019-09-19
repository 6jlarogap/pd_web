from django.contrib import admin

from halls.models import Hall, HallTimeTable

class HallAdmin(admin.ModelAdmin):
    pass
admin.site.register(Hall, HallAdmin)

class HallTimeTableAdmin(admin.ModelAdmin):
    pass
admin.site.register(HallTimeTable, HallTimeTableAdmin)

