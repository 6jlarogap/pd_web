import datetime

from django import forms
from django.utils.translation import gettext as _

from geo.models import Location, Country, Region, City, Street
from pd.forms import PartialFormMixin


class LocationForm(PartialFormMixin, forms.ModelForm):
    country_name = forms.CharField(label=_("Страна"), required=False)
    region_name =  forms.CharField(label=_("Регион"), required=False)
    city_name = forms.CharField(label=_("Город"), required=False)
    street_name = forms.CharField(label=_("Улица"), required=False)

    fias_address = forms.CharField(label='', required=False)

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
                         'fias_address', 'info'):
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
        if self.instance and self.is_addr_str and self.cleaned_data.get('addr_str', '').strip():
            return super(LocationForm, self).save(commit, *args, **kwargs)

        country_name = self.cleaned_data.get('country_name', '').strip()
        region_name = self.cleaned_data.get('region_name', '').strip()
        city_name = self.cleaned_data.get('city_name', '').strip()
        street_name = self.cleaned_data.get('street_name', '').strip()
        loc = super(LocationForm, self).save(commit=False, *args, **kwargs)
        if country_name:
            loc.country, _tmp = Country.objects.get_or_create(name=country_name)
            if region_name:
                loc.region, _tmp = Region.objects.get_or_create(name=region_name, country=loc.country)
                if city_name:
                    loc.city, _tmp = City.objects.get_or_create(name=city_name, region=loc.region)
                    if street_name:
                        loc.street, _tmp = Street.objects.get_or_create(name=street_name, city=loc.city)
                    else:
                        loc.street = None
                else:
                    loc.city = None
                    loc.street = None
            else:
                loc.region = None
                loc.city = None
                loc.street = None
            if commit:
                loc.save()
            return loc
        return None

