# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.core.urlresolvers import reverse
from django import forms

from burials.models import *
from burials.forms import *
from django.forms.models import modelformset_factory
from orgs.models import BankAccount
from persons.models import ZAGS, IDDocumentType

class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['action_time', 'object_link', 'user', ]

    def object_link(self, obj):
        o = obj.get_edited_object()
        if isinstance(o, Burial):
            return u'<a href="%s">Захоронение %s (%s)</a>' % (reverse('edit_burial', args=[o.pk]), o.account_number, o.person)
        else:
            return u'%s' % o
    object_link.allow_tags = True

class PersonAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'middle_name', 'get_unclear_birth_date', 'get_death_date', 'get_address']
    search_fields = ['last_name', 'first_name', 'middle_name']
    lookup_allowed = lambda *args: True

    def get_unclear_birth_date(self, obj):
        d = obj.unclear_birth_date
        return d and d.strftime('%d.%m.%Y') or ''
    get_unclear_birth_date.short_description = u'Дата рождения'

    def get_death_date(self, obj):
        d = obj.death_date
        return d and d.strftime('%d.%m.%Y') or ''
    get_death_date.short_description = u'Дата смерти'

    def get_address(self, obj):
        return obj.address or ''
    get_address.short_description = u'Адрес'

class OwnedObjectsAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.creator:
            obj.creator = request.user
        obj.save()

    def queryset(self, request):
        return super(OwnedObjectsAdmin, self).queryset(request).filter(Q(creator=None) | Q(creator=request.user))

class CemeteryAdmin(OwnedObjectsAdmin):
    raw_id_fields = ['organization', 'location', ]
    list_display = ['name', 'organization', 'ordering']
    list_editable = ['ordering']

class OperationAdmin(OwnedObjectsAdmin):
    list_display = ['name']

class ServiceAdmin(OwnedObjectsAdmin):
    list_display = ['name']

class PlaceAdmin(admin.ModelAdmin):
    list_display = ['cemetery', 'area', 'row', 'seat', 'rooms']
    search_fields = ['seat']
    list_filter = ['cemetery', ]

admin.site.register(Cemetery, CemeteryAdmin)
admin.site.register(Operation, OperationAdmin)
admin.site.register(Place, PlaceAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(ZAGS)
admin.site.register(IDDocumentType)
admin.site.register(LogEntry, LogEntryAdmin)