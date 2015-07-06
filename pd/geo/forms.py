# coding=utf-8
import datetime

from django import forms
from django.utils.translation import ugettext as _

from geo.models import Location, Country, Region, City, Street
from pd.forms import PartialFormMixin


class LocationForm(PartialFormMixin, forms.ModelForm):
    country_name = forms.CharField(label=_(u"Страна"), required=False)
    region_name =  forms.CharField(label=_(u"Регион"), required=False)
    city_name = forms.CharField(label=_(u"Город"), required=False)
    street_name = forms.CharField(label=_(u"Улица"), required=False)

    fias_address = forms.CharField(label='', required=False)
    fias_street = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Location
        exclude = ['country', 'region', 'city', 'street', ]

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        self.is_addr_str = False
        self.initial = self.initial or {}
        if self.instance:
            if self.instance.addr_str:
                for f in ('country_name', 'region_name', 'city_name', 'street_name',
                         'fias_address', 'fias_street', 'info'):
                    del self.fields[f]
                self.is_addr_str = True
            else:
                del self.fields['addr_str']
                if self.instance.country:
                    self.initial['country_name'] = self.instance.country.name

                    if self.instance.region:
                        self.initial['region_name'] = self.instance.region.name
                        if self.instance.city:
                            self.initial['city_name'] = self.instance.city.name
                        if self.instance.street:
                            self.initial['street_name'] = self.instance.street.name

        if 'info' in self.fields:
            self.fields['info'].widget = forms.TextInput()

    def is_valid_data(self):
        return self.is_valid() and any(self.cleaned_data.values())

    def save(self, commit=True, *args, **kwargs):
        if self.instance and self.is_addr_str:
            return super(LocationForm, self).save(commit, *args, **kwargs)
        elif self.cleaned_data['country_name']:
            loc = super(LocationForm, self).save(commit=False, *args, **kwargs)
            loc.country, _tmp = Country.objects.get_or_create(name=self.cleaned_data['country_name'])
            if not self.cleaned_data.get('fias_street'):
                if self.cleaned_data['region_name']:
                    loc.region, _tmp = Region.objects.get_or_create(name=self.cleaned_data['region_name'], country=loc.country)
                    if self.cleaned_data['city_name']:
                        loc.city, _tmp = City.objects.get_or_create(name=self.cleaned_data['city_name'], region=loc.region)
                        if self.cleaned_data['street_name']:
                            loc.street, _tmp = Street.objects.get_or_create(name=self.cleaned_data['street_name'], city=loc.city)
            else:
                loc.region = None
                loc.city = None
                loc.street = None
            if commit:
                loc.save()
            return loc

