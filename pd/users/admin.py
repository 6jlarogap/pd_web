from django.contrib import admin

from users.models import Profile, Org, ProfileLORU, Dover


class ProfileAdmin(admin.ModelAdmin):
    pass

admin.site.register(Profile, ProfileAdmin)

class ProfileLORUInline(admin.TabularInline):
    model = ProfileLORU
    fk_name = 'ugh'

class AgentDoverInline(admin.TabularInline):
    model = Dover
    can_delete = False

class OrgAdmin(admin.ModelAdmin):
    inlines = [ProfileLORUInline, AgentDoverInline, ]
    list_display = ['name', 'type']

admin.site.register(Org, OrgAdmin)
