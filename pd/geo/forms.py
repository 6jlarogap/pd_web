# coding=utf-8
import datetime

from django import forms
from django.utils.translation import ugettext as _

from geo.models import Location, Country, Region, City, Street, DFiasAddrobj


FIAS_QS = DFiasAddrobj.objects.using('fias').filter(actstatus=1, enddate__gte=datetime.date.today())

class LocationForm(forms.ModelForm):
    country_name = forms.CharField(label=_(u"Страна"), required=False)
    region_name =  forms.CharField(label=_(u"Регион"), required=False)
    city_name = forms.CharField(label=_(u"Город"), required=False)
    street_name = forms.CharField(label=_(u"Улица"), required=False)

    fias_1 = forms.ModelChoiceField(queryset=FIAS_QS.filter(aolevel=1).order_by('offname'), required=False)
    fias_2 = forms.ModelChoiceField(queryset=FIAS_QS.none(), required=False)
    fias_3 = forms.ModelChoiceField(queryset=FIAS_QS.none(), required=False)
    fias_4 = forms.ModelChoiceField(queryset=FIAS_QS.none(), required=False)
    fias_5 = forms.ModelChoiceField(queryset=FIAS_QS.none(), required=False)
    fias_6 = forms.ModelChoiceField(queryset=FIAS_QS.none(), required=False)
    fias_7 = forms.ModelChoiceField(queryset=FIAS_QS.none(), required=False)

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
                    for i, fias_link in enumerate(self.instance.fias_parents.all()):
                        self.initial['fias_%s' % (i+1)] = FIAS_QS.get(aoguid=fias_link.guid)

            for i in range(1, 7):
                prefix = self.prefix and '%s-' % self.prefix or ''
                init = self.initial.get('fias_%s' % i)
                data = self.data.get('%sfias_%s' % (prefix, i)) or (init and init.aoguid)
                if data:
                    try:
                        parent = FIAS_QS.get(aoguid=data)
                    except DFiasAddrobj.DoesNotExist:
                        break
                    else:
                        qs = FIAS_QS.filter(parentguid=parent.aoguid).order_by('offname')
                        self.fields['fias_%s' % (i+1)].queryset = qs

    def is_valid_data(self):
        return self.is_valid() and any(self.cleaned_data.values())

    def save(self, commit=True, *args, **kwargs):
        if self.cleaned_data['country_name']:
            loc = super(LocationForm, self).save(commit=False, *args, **kwargs)
            loc.country, _tmp = Country.objects.get_or_create(name=self.cleaned_data['country_name'])
            if not self.cleaned_data['fias_1']:
                if self.cleaned_data['region_name']:
                    loc.region, _tmp = Region.objects.get_or_create(name=self.cleaned_data['region_name'], country=loc.country)
                    if self.cleaned_data['city_name']:
                        loc.city, _tmp = City.objects.get_or_create(name=self.cleaned_data['city_name'], region=loc.region)
                        if self.cleaned_data['street_name']:
                            loc.street, _tmp = Street.objects.get_or_create(name=self.cleaned_data['street_name'], city=loc.city)
            if commit:
                loc.save()

                loc.fias_parents.all().delete()
                if self.cleaned_data['fias_1']:
                    for fi in range(1, 8):
                        f = 'fias_%s' % fi
                        fd = self.cleaned_data.get(f)
                        if fd:
                            loc.fias_parents.create(
                                guid=fd.aoguid,
                                name=u'%s %s' % (fd.offname, fd.shortname),
                                level=fd.aolevel,
                            )
                        else:
                            break
            return loc

