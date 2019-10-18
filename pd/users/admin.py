from django.contrib import admin

from users.models import Profile, Org, ProfileLORU, Dover, CustomerProfile, Role


class AgentDoverInline(admin.TabularInline):
    model = Dover
    can_delete = False

class ProfileLORUInline(admin.TabularInline):
    model = ProfileLORU
    fk_name = 'ugh'

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'org', 'is_agent', ]
    list_filter = ['is_agent',]
    inlines = [AgentDoverInline, ]
    search_fields = ['user__username', 'user_last_name', 'org__name']

admin.site.register(Profile, ProfileAdmin)

class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_phone', 'last_name_initials', ]
    search_fields = ['user__username', 'user_last_name', 'login_phone']

admin.site.register(CustomerProfile, CustomerProfileAdmin)

class OrgAdmin(admin.ModelAdmin):
    inlines = [ProfileLORUInline, ]
    list_display = ['id', 'name', 'type']
    readonly_fields =  ['off_address', ]
    search_fields = ['name']

admin.site.register(Org, OrgAdmin)

class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', ]

admin.site.register(Role, RoleAdmin)

