# coding=utf-8
import datetime

from django import forms
from django.utils.translation import ugettext as _

from geo.models import Location, Country, Region, City, Street, DFiasAddrobj
from pd.forms import PartialFormMixin


FIAS_QS = DFiasAddrobj.objects.using('fias').filter(actstatus=1, enddate__gte=datetime.date.today())

class LocationForm(PartialFormMixin, forms.ModelForm):
    country_name = forms.CharField(label=_(u"Страна"), required=False)
    region_name =  forms.CharField(label=_(u"Регион"), required=False)
    city_name = forms.CharField(label=_(u"Город"), required=False)
    street_name = forms.CharField(label=_(u"Улица"), required=False)

    fias_address = forms.CharField(label=_(u"Адрес ФИАС"), required=False)
    fias_street = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Location
        exclude = ['country', 'region', 'city', 'street', ]

    def __init__(self, *args, **kwargs):

        super(LocationForm, self).__init__(*args, **kwargs)
        self.initial = self.initial or {}
        if self.instance:
            if self.instance.country:
                self.initial['country_name'] = self.instance.country.name

                if self.instance.region:
                    self.initial['region_name'] = self.instance.region.name
                    if self.instance.city:
                        self.initial['city_name'] = self.instance.city.name
                    if self.instance.street:
                        self.initial['street_name'] = self.instance.street.name
                else:
                    fias_all = list(self.instance.fias_parents.all())
                    if fias_all:
                        fias_addr = u', '.join([f.name for f in fias_all])
                        if self.instance.house:
                            fias_addr += u', д. %s' % self.instance.house
                        if self.instance.block:
                            fias_addr += u', к. %s' % self.instance.block
                        if self.instance.building:
                            fias_addr += u', стр. %s' % self.instance.building
                        if self.instance.flat:
                            fias_addr += u', кв. %s' % self.instance.flat
                        self.initial['fias_address'] = fias_addr
                        self.initial['fias_street'] = fias_all[-1].guid

    def clean_fias_street(self):
        if self.cleaned_data.get('fias_street'):
            try:
                return DFiasAddrobj.objects.get(aoguid=self.cleaned_data['fias_street'])
            except DFiasAddrobj.DoesNotExist:
                raise forms.ValidationError(_(u"Неверная ссылка"))
        else:
            return

    def is_valid_data(self):
        return self.is_valid() and any(self.cleaned_data.values())

    def save(self, commit=True, *args, **kwargs):
        if self.cleaned_data['country_name']:
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

                loc.fias_parents.all().delete()
                fias = self.cleaned_data.get('fias_street')
                while fias:
                    loc.fias_parents.create(
                        guid=fias.aoguid,
                        name=u'%s %s' % (fias.offname, fias.shortname),
                        level=fias.aolevel,
                    )
                    fias = fias.get_parent()
            return loc

