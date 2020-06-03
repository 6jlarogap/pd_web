import datetime

from django import forms
from django.utils.translation import ugettext as _
from django.db.models.fields.files import FieldFile

from django.conf import settings
from persons.models import DeadPerson, PersonID, DeathCertificate, DeathCertificateScan, AlivePerson, DocumentSource
from pd.models import UnclearDate
from users.models import Org
from logs.models import write_log
from pd.forms import BaseModelForm, StrippedStringsMixin, CustomClearableFileInput, CustomUploadModelForm

class ValidDataMixin:
    def is_valid_data(self):
        return self.is_valid() and any(self.cleaned_data.values())

class DeadPersonForm(ValidDataMixin, StrippedStringsMixin, forms.ModelForm):
    class Meta:
        model = DeadPerson
        fields = '__all__'

    def __init__(self, request, *args, **kwargs):
        death_date = None
        kwargs.setdefault('initial', {})
        death_date_offer = request.user.profile.org.death_date_offer
        if death_date_offer and request.user.profile.is_loru():
            death_date = datetime.date.today()
        elif death_date_offer and request.user.profile.is_ugh():
            death_date = datetime.date.today() - datetime.timedelta(1)
        if death_date and not kwargs.get('instance'):
            kwargs['initial'].update({
                'death_date': death_date,
            })
        super(DeadPersonForm, self).__init__(*args, **kwargs)

    def is_valid_data(self):
        return self.is_valid() and len([k for k,v in list(self.cleaned_data.items()) if v]) > 1 # more than just death date
    
class PersonIDForm(ValidDataMixin, StrippedStringsMixin, forms.ModelForm):
    flag_no_applicant_doc_required = forms.BooleanField(label=_('Документ не обязателен'), required=False)
    source = forms.CharField(label=_('Кем выдан'), required=False)

    class Meta:
        model = PersonID
        exclude = ['person', ]

    def clean_source(self):
        src, _created = DocumentSource.objects.get_or_create(name=self.cleaned_data['source'])
        return src

    def __init__(self, *args, **kwargs):
        super(PersonIDForm, self).__init__(*args, **kwargs)
        if self.initial and self.initial.get('source') and isinstance(self.initial.get('source'), DocumentSource):
            self.initial['source'] = self.initial.get('source').name
        if self.instance and self.instance.source and isinstance(self.instance.source, DocumentSource):
            self.initial.update({'source': self.instance.source.name})

    def clean_date(self):
        today = datetime.date.today()
        release_date = self.cleaned_data.get('date')
        if release_date and release_date > today:
            msg = _('Неверная дата выдачи')
            raise forms.ValidationError(msg)
        return release_date

    def clean_date_expire(self):
        date = self.cleaned_data.get('date')
        date_expire = self.cleaned_data.get('date_expire')
        if date_expire and date and date_expire < date:
            msg = _('Срок действия истек до даты выдачи')
            raise forms.ValidationError(msg)
        return date_expire

class DeathCertificateForm(StrippedStringsMixin, BaseModelForm):
    dt_modified = forms.IntegerField(widget=forms.HiddenInput, required=False, )
    zags = forms.CharField(required=False)

    class Meta:
        model = DeathCertificate
        exclude = ['person', ]

    def __init__(self, request, *args, **kwargs):
        self.request = request
        kwargs.setdefault('initial', {})
        instance = kwargs.get('instance')
        scan = None
        if instance and instance.pk:
            kwargs['initial'].update({
                'dt_modified': int(instance.dt_modified.strftime("%s")),
                'zags': instance.zags.name if instance.zags else '',
            })
            try:
                scan = instance.deathcertificatescan
            except DeathCertificateScan.DoesNotExist:
                pass
        if settings.DEATH_CERTIFICATE_REQUIRED and \
           (not instance or not instance.person) and \
            not request.GET.get('archive'):
            kwargs['initial'].update({
                'release_date': datetime.date.today(),
            })
        kwargs['initial'].update(dict(
          type=instance and instance.type or DeathCertificate.PROFILE_ZAGS,  
        ))
        super(DeathCertificateForm, self).__init__(*args, **kwargs)
        self.fields['type'] = forms.ChoiceField(choices=DeathCertificate.PROFILE_TYPES, widget=forms.RadioSelect())
        self.fields['type'].label = '' # DeathCertificate._meta.get_field('type').verbose_name
        self.fields['zags'].max_length = Org._meta.get_field('name').max_length
        self.fields['zags'].label = DeathCertificate._meta.get_field('zags').verbose_name
        self.scan_form = DeathCertificateScanForm(request, prefix='dc-scan', instance = scan, files=request.FILES)

    def clean_zags(self):
        zags = None
        type_ = self.cleaned_data.get('type') and self.cleaned_data['type'] or \
                    DeathCertificate.PROFILE_ZAGS
        zags_str = self.cleaned_data.get('zags').strip()
        if zags_str:
            try:
                zags = Org.objects.filter(name=zags_str, type=type_)[0]
            except IndexError:
                raise forms.ValidationError(_('Нет такого ЗАГСа') if type_ == DeathCertificate.PROFILE_ZAGS \
                                            else _('Нет такого мед. учреждения'))
        return zags

    def clean_release_date(self):
        today = datetime.date.today()
        release_date = self.cleaned_data.get('release_date')
        if release_date and release_date > today:
            msg = _('Неверная дата выдачи')
            raise forms.ValidationError(msg)
        return release_date

    def is_valid(self):
        return super(DeathCertificateForm, self).is_valid() and self.scan_form.is_valid()
        
    def save(self, deadPerson=None, commit=True, *args, **kwargs):
        scan_uploaded = scan_clear = False
        if self.scan_form.is_valid():
            self.scan_form.clean()
            bfile = self.scan_form.cleaned_data.get('bfile')
            # FieldFile -- это еще не UploadedFile
            scan_uploaded = bfile and not isinstance(bfile, FieldFile)
            scan_clear = self.request.POST.get(self.scan_form.prefix+'-bfile-clear')
        if deadPerson:
            self.instance.person = deadPerson
        dc = super(DeathCertificateForm, self).save(forceCommit=scan_clear or scan_uploaded,
                                                    commit=commit,
                                                    *args, **kwargs)
        if commit and self.scan_form.is_valid():
            burial = dc.get_burial()
            log_prefix = _("Усопший") + ", " + str(_("СоС")) + " "
            if self.scan_form.instance.pk:
                if scan_clear and not scan_uploaded:
                    self.scan_form.instance.delete()
                    if burial:
                        write_log(self.request, burial, log_prefix + _('скан удален'))
                    return dc
                if scan_clear or scan_uploaded:
                    DeathCertificateScan.objects.get(pk=self.scan_form.instance.pk).delete_from_media()
            if scan_uploaded:
                scan = self.scan_form.save(commit=False)
                scan.deathcertificate = dc
                scan.save()
                if burial:
                    write_log(self.request, burial,  log_prefix + _('прикреплен скан: %s') % scan.original_name)
        return dc

class AlivePersonForm(ValidDataMixin, StrippedStringsMixin, forms.ModelForm):
    class Meta:
        model = AlivePerson
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(AlivePersonForm, self).__init__(*args, **kwargs)
        self.fields['phones'].widget = forms.TextInput()
        # У нас нет случаев, когда живому человеку в форме надо вводить день рождения:
        del self.fields['birth_date']
        # Идентификационный номер вводится только для усопшего:
        del self.fields['ident_number']

    def is_valid_data(self):
        return self.is_valid() and self.cleaned_data.get('last_name') # last name should be present

class DeathCertificateScanForm(CustomUploadModelForm):
    class Meta:
        model = DeathCertificateScan
        fields = ('bfile', )
        widgets = {
            'bfile': CustomClearableFileInput,
        }
        
    def __init__(self, *args, **kwargs):
        super(DeathCertificateScanForm, self).__init__(*args, **kwargs)
        self.init_bfile()
        self.fields['bfile'].label = _('Скан документа о смерти')
        self.MAX_UPLOAD_SIZE_MB = 5
