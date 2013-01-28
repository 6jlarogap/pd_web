from django.contrib import admin
from logs.models import Log


class LogsAdmin(admin.ModelAdmin):
    list_display = ['dt', 'user', 'ct', 'obj_id', 'msg']
    list_display_links = []

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Log, LogsAdmin)