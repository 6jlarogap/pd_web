from django.contrib import admin

from users.models import Profile, Org, ProfileLORU


class ProfileAdmin(admin.ModelAdmin):
    pass

admin.site.register(Profile, ProfileAdmin)

class ProfileLORUInline(admin.TabularInline):
    model = ProfileLORU
    fk_name = 'ugh'

class OrgAdmin(admin.ModelAdmin):
    inlines = [ProfileLORUInline, ]
    list_display = ['name', 'type']

admin.site.register(Org, OrgAdmin)
