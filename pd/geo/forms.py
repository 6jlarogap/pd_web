# coding=utf-8
from django import forms
from django.utils.translation import ugettext as _

from geo.models import Location, Country, Region, City, Street


class LocationForm(forms.ModelForm):
    country_name = forms.CharField(label=_(u"Страна"))
    region_name =  forms.CharField(label=_(u"Регион"))
    city_name = forms.CharField(label=_(u"Город"))
    street_name = forms.CharField(label=_(u"Улица"))

    class Meta:
        model = Location
        exclude = ['country', 'region', 'city', 'street', ]

    def save(self, commit=True, *args, **kwargs):
        loc = super(LocationForm, self).save(commit=False, *args, **kwargs)
        loc.country, _tmp = Country.objects.get_or_create(name=self.cleaned_data['country_name'])
        loc.region, _tmp = Region.objects.get_or_create(name=self.cleaned_data['region_name'], country=loc.country)
        loc.city, _tmp = City.objects.get_or_create(name=self.cleaned_data['city_name'], region=loc.region)
        loc.street, _tmp = Street.objects.get_or_create(name=self.cleaned_data['street_name'], city=loc.city)
        if commit:
            loc.save()
        return loc

