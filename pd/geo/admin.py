from django.contrib import admin

from geo.models import Country, City, Street, Region

class CountryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Country, CountryAdmin)

class CityAdmin(admin.ModelAdmin):
    search_fields = ['name', 'region__name']

admin.site.register(City, CityAdmin)

class StreetAdmin(admin.ModelAdmin):
    search_fields = ['name', 'city__name']

admin.site.register(Street, StreetAdmin)

class RegionAdmin(admin.ModelAdmin):
    pass

admin.site.register(Region, RegionAdmin)

