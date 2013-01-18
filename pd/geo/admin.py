# -*- coding: utf-8 -*-

from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect

from geo.models import Region, City, Country, Street, Location

class StreetForm(forms.ModelForm):
    combine_with = forms.ModelChoiceField(
        queryset=Street.objects.all(), label=u"Слить с улицей", help_text=u"Текущая улица будет удалена", required=False)
    really_combine = forms.BooleanField(label=u"Подтвердить слияние", required=False)

    class Meta:
        model = Street

    def __init__(self, *args, **kwargs):
        Street.__unicode__ = lambda s: u'%s %s' % (s.name, s.city)
        super(StreetForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.instance and self.cleaned_data.get('combine_with') and self.cleaned_data.get('really_combine'):
            new_street = self.cleaned_data.get('combine_with')
            Location.objects.filter(street=self.instance).update(
                street=new_street,
                city=new_street.city,
                region=new_street.city and new_street.city.region,
                country=new_street.city and new_street.city.region and new_street.city.region.country,
            )
            self.instance.delete()
        else:
            return super(StreetForm, self).save(*args, **kwargs)

    def save_m2m(self, *args, **kwargs):
        return

class GeoAdmin(admin.ModelAdmin):
    ordering = ['name', ]
    search_fields = ['name', ]

class StreetAdmin(admin.ModelAdmin):
    form = StreetForm
    raw_id_fields = ['city', ]
    ordering = ['name', ]
    search_fields = ['name', ]

    def save_model(self, request, obj, form, change):
        if not obj:
            return
        else:
            super(StreetAdmin, self).save_model(request, obj, form, change)

    def log_change(self, request, object, message):
        if not object:
            return
        else:
            return super(StreetAdmin, self).log_change(request, object, message)

    def response_change(self, request, obj):
        if not obj:
            return HttpResponseRedirect('..')
        return super(StreetAdmin, self).response_change(request, obj)

admin.site.register(Country, GeoAdmin)
admin.site.register(City, GeoAdmin)
admin.site.register(Region, GeoAdmin)
admin.site.register(Street, StreetAdmin)
