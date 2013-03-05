from django.contrib import admin

from users.models import Profile, Org, ProfileLORU, Dover


class AgentDoverInline(admin.TabularInline):
    model = Dover
    can_delete = False

class ProfileLORUInline(admin.TabularInline):
    model = ProfileLORU
    fk_name = 'ugh'

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'is_agent', ]
    list_filter = ['is_agent',]
    inlines = [AgentDoverInline, ]

admin.site.register(Profile, ProfileAdmin)

class OrgAdmin(admin.ModelAdmin):
    inlines = [ProfileLORUInline, ]
    list_display = ['name', 'type']

admin.site.register(Org, OrgAdmin)
