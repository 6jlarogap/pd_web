from django.contrib import admin

from users.models import Profile, Org, ProfileLORU, Dover


class ProfileAdmin(admin.ModelAdmin):
    inlines = [AgentDoverInline, ]

admin.site.register(Profile, ProfileAdmin)

class ProfileLORUInline(admin.TabularInline):
    model = ProfileLORU
    fk_name = 'ugh'

class AgentDoverInline(admin.TabularInline):
    model = Dover
    can_delete = False

class OrgAdmin(admin.ModelAdmin):
    inlines = [ProfileLORUInline, ]
    list_display = ['name', 'type']

admin.site.register(Org, OrgAdmin)
