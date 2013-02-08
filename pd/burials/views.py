# coding=utf-8
import datetime
from burials.forms import BurialCreateForm, CemeteryForm, AreaFormset, BurialSearchForm, BurialForm, PlaceForm
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.shortcuts import redirect
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _

from burials.models import Cemetery, Reason, Burial, Place
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from geo.forms import LocationForm
from logs.models import write_log
from persons.forms import DeadPersonForm, DeathCertificateForm, AlivePersonForm, PersonIDForm


class BurialsListGenericMixin:
    def get_qs_filter(self):
        qs = Q(pk__isnull=True)
        if self.request.user.is_authenticated():
            if self.request.user.profile.is_loru():
                qs = Q(loru=self.request.user.profile.org)
            if self.request.user.profile.is_ugh():
                qs = Q(loru__ugh_list__ugh=self.request.user.profile.org)
        return qs

class DashboardView(BurialsListGenericMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        qs = self.get_qs_filter()
        try:
            profile = self.request.user.profile
        except AttributeError:
            pass
        else:
            if profile.is_loru():
                qs &= Q(status=Burial.STATUS_DRAFT) | \
                      Q(status=Burial.STATUS_BACKED) | \
                      Q(status=Burial.STATUS_DECLINED)
            if profile.is_ugh():
                qs &= Q(status=Burial.STATUS_READY) | Q(status=Burial.STATUS_APPROVED)
        return {'burials': Burial.objects.filter(qs).distinct()}

    def get(self, request, *args, **kwargs):
        if not request.GET:
            return redirect('archive')
        else:
            return super(DashboardView, self).get(request, *args, **kwargs)

dashboard = DashboardView.as_view()

class ArchiveMixin(BurialsListGenericMixin):
    def get_qs_filter(self):
        qs = Q(pk__isnull=True)
        if self.request.user.is_authenticated():
            if self.request.user.profile.is_loru():
                qs = Q(loru=self.request.user.profile.org)
            if self.request.user.profile.is_ugh():
                qs = Q(
                    # Q(ready_loru__isnull=False) | Q(backed_loru__isnull=False),
                    cemetery__ugh=self.request.user.profile.org,
                )
        return qs

class ArchiveView(ArchiveMixin, TemplateView):
    template_name = 'archive.html'

    def get_context_data(self, **kwargs):
        qs = self.get_qs_filter()
        return {'burials': Burial.objects.filter(qs).distinct().order_by('-pk')}

archive = ArchiveView.as_view()

class RequestView(ArchiveMixin, DetailView):
    template_name = 'view_request.html'
    context_object_name = 'b'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return Burial.objects.filter(qs).distinct()

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('dashboard')
        b = self.get_object()
        b.changed = datetime.datetime.now()
        b.changed_by = request.user
        old_status = b.status
        reason = request.POST.get('reason') or request.POST.get('reason_typical')
        if request.POST.get('back') and request.user.profile.is_loru() and not b.is_finished():
            b.status = Burial.STATUS_BACKED
            write_log(request, b, _(u'Заявка отозвана'), reason)
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> отозвана") % (
                reverse('view_request', args=[b.pk]), b.pk,
            ))
        if request.POST.get('ready') and request.user.profile.is_loru() and b.is_edit():
            b.status = Burial.STATUS_READY
            write_log(request, b, _(u'Заявка отправлена на согласование'))
            msg = _(u"<a href='%s'>Заявка %s</a> отправлена на согласование") % (
                reverse('view_request', args=[b.pk]), b.pk,
            )
            messages.success(request, msg)
        if request.POST.get('approve') and request.user.profile.is_ugh() and b.is_ready():
            b.status = Burial.STATUS_APPROVED
            write_log(request, b, _(u'Заявка согласована'))
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> согласована") % (
                reverse('view_request', args=[b.pk]), b.pk,
            ))
        if request.POST.get('decline') and request.user.profile.is_ugh() and b.is_ready():
            b.status = Burial.STATUS_DECLINED
            write_log(request, b, _(u'Заявка отклонена'), reason)
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> отклонена") % (
                reverse('view_request', args=[b.pk]), b.pk,
            ))
        if request.POST.get('complete') and request.user.profile.is_ugh() and b.is_approved():
            b.status = Burial.STATUS_CLOSED
            try:
                burial = b.close()
            except Exception, e:
                messages.error(request, _(u'Ошибка: %s') % e)
                return redirect('view_request', b.pk)
            write_log(request, b, _(u'Заявка закрыта'))
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> закрыта, создано <a href='%s'>захоронение %s</a>") % (
                reverse('view_request', args=[b.pk]), b.pk,
                reverse('view_burial', args=[burial.pk]), burial.pk,
            ))
        if request.POST.get('annulate') and request.user.profile.is_ugh() and b.is_approved():
            b.status = Burial.STATUS_ANNULATED
            write_log(request, b, _(u'Заявка аннулирована'), reason)
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> аннулирована") % (
                reverse('view_request', args=[b.pk]), b.pk,
            ))
        if old_status != b.status:
            b.save()
        else:
            msg = _(u"Выполнить операцию не удалось: <a href='%s'>заявка</a> в статусе \"%s\"") % (
                reverse('view_request', args=[b.pk]),
                b.get_status_display(),
            )
            messages.success(request, msg)
        return redirect('dashboard')

    def get_context_data(self, **kwargs):
        return {
            'b': self.get_object(),
            'reason_typical_back': Reason.objects.filter(reason_type=Reason.TYPE_BACK),
            'reason_typical_decline': Reason.objects.filter(reason_type=Reason.TYPE_DECLINE),
            'reason_typical_annulate': Reason.objects.filter(reason_type=Reason.TYPE_ANNULATE),
            }

view_request = RequestView.as_view()

class BurialView(DetailView):
    template_name = 'view_burial.html'
    context_object_name = 'b'
    model = Burial

view_burial = BurialView.as_view()

class CreateRequestView(CreateView):
    template_name = 'create_request.html'
    form_class = BurialCreateForm

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated() or not self.request.user.profile.is_loru():
            return redirect('/')
        return super(CreateRequestView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        data = super(CreateRequestView, self).get_form_kwargs(*args, **kwargs)
        data.update({'request': self.request})
        return data

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.changed = datetime.datetime.now()
        self.object.changed_by = self.request.user
        self.object.loru = self.request.user.profile.org
        self.object.save()
        messages.success(self.request, _(u"Черновик сохранен"))
        write_log(self.request, self.object, _(u'Создана заявка'))
        return redirect('edit_request', self.object.pk)

create_request = CreateRequestView.as_view()

class EditRequestView(UpdateView):
    template_name = 'edit_request.html'
    form_class = BurialCreateForm

    def get_queryset(self):
        q = Q(status=Burial.STATUS_DRAFT) | \
            Q(status=Burial.STATUS_DECLINED) | \
            Q(status=Burial.STATUS_BACKED)
        return Burial.objects.filter(q, loru=self.request.user.profile.org)

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated() or not self.request.user.profile.is_loru():
            return redirect('/')
        return super(EditRequestView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        data = super(EditRequestView, self).get_form_kwargs(*args, **kwargs)
        data.update({'request': self.request})
        return data

    def form_valid(self, form):
        changed_fields = []
        b = self.get_object()
        for f in form.changed_data:
            old_value = getattr(b, f, None)
            new_value = form.cleaned_data[f]
            if new_value != old_value:
                changed_fields.append([form.fields[f].label, old_value, new_value])

        if changed_fields:
            changed_fields_str = u'\n' + u'\n'.join([u"%s: %s -> %s" % tuple(cf) for cf in changed_fields])
        else:
            changed_fields_str = u''

        self.object = form.save(commit=False)
        if self.request.REQUEST.get('ready'):
            self.object.status = Burial.STATUS_READY
            self.object.changed = datetime.datetime.now()
            self.object.changed_by = self.request.user
            messages.success(self.request, _(u"Заявка сохранена и отправлена на согласование в УГХ"))
        else:
            messages.success(self.request, _(u"Черновик сохранен"))
        self.object.save()
        if changed_fields_str:
            write_log(self.request, self.object, _(u'Изменена заявка %s') % changed_fields_str, code='edit_request')
        if self.request.REQUEST.get('ready'):
            write_log(self.request, self.object, _(u'Заявка отправлена на согласование'))
        return redirect('dashboard')

edit_request = EditRequestView.as_view()

class UGHRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated() or not getattr(self.request.user, 'profile', None) or not self.request.user.profile.is_ugh():
            return redirect('/')
        return View.dispatch(self, request, *args, **kwargs)

class CemeteryList(UGHRequiredMixin, ListView):
    template_name = 'cemetery_list.html'
    model = Cemetery

    def get_queryset(self):
        return Cemetery.objects.filter(Q(creator__isnull=True) | Q(ugh=self.request.user.profile.org))

manage_cemeteries = CemeteryList.as_view()

class CemeteryCreate(UGHRequiredMixin, CreateView):
    template_name = 'cemetery_create.html'
    form_class = CemeteryForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.ugh = self.request.user.profile.org
        self.object.save()
        write_log(self.request, self.object, _(u'Кладбище создано'))
        msg = _(u"<a href='%s'>Кладбище %s</a> создано") % (
            reverse('manage_cemeteries_edit', args=[self.object.pk]),
            self.object.name,
        )
        messages.success(self.request, msg)
        return redirect('manage_cemeteries')

manage_cemeteries_create = CemeteryCreate.as_view()

class CemeteryEdit(UGHRequiredMixin, UpdateView):
    template_name = 'cemetery_edit.html'
    form_class = CemeteryForm

    def get_queryset(self):
        return Cemetery.objects.filter(ugh=self.request.user.profile.org)

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        if request.user.profile.org and request.user.profile.is_ugh():
            self.formset = AreaFormset(data=request.POST or None, instance=self.get_object())
        else:
            self.formset = AreaFormset()
        return super(CemeteryEdit, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(CemeteryEdit, self).get_context_data(**kwargs)
        data['formset'] = self.formset
        return data

    def form_valid(self, form):
        self.formset.save()
        self.object = form.save()
        write_log(self.request, self.object, _(u'Кладбище изменено'))
        msg = _(u"<a href='%s'>Кладбище %s</a> изменено") % (
            reverse('manage_cemeteries_edit', args=[self.object.pk]),
            self.object.name,
        )
        messages.success(self.request, msg)
        return redirect('manage_cemeteries')

manage_cemeteries_edit = CemeteryEdit.as_view()

class BurialsListView(ListView):
    template_name = 'burial_list.html'
    paginate_by = 20
    context_object_name = 'burials'

    def get_queryset(self):
        burials = Burial.objects.filter(status=Burial.STATUS_CLOSED).order_by('-pk')
        form = self.get_form()
        if form.data and form.is_valid():
            if form.cleaned_data['operation']:
                burials = burials.filter(burial_type=form.cleaned_data['operation'])
            if form.cleaned_data['fio']:
                fio = [f.strip('.') for f in form.cleaned_data['fio'].split(' ')]
                q = Q()
                if len(fio) > 2:
                    q &= Q(deadman__middle_name__icontains=fio[2])
                if len(fio) > 1:
                    q &= Q(deadman__first_name__icontains=fio[1])
                if len(fio) > 0:
                    q &= Q(deadman__last_name__icontains=fio[0])
                burials = burials.filter(q)
            if form.cleaned_data['birth_date_from']:
                burials = burials.filter(deadman__birth_date__gte=form.cleaned_data['birth_date_from'])
            if form.cleaned_data['birth_date_to']:
                burials = burials.filter(deadman__birth_date__lte=form.cleaned_data['birth_date_to'])
            if form.cleaned_data['death_date_from']:
                burials = burials.filter(deadman__death_date__gte=form.cleaned_data['death_date_from'])
            if form.cleaned_data['death_date_to']:
                burials = burials.filter(deadman__death_date__lte=form.cleaned_data['death_date_to'])
            if form.cleaned_data['burial_date_from']:
                burials = burials.filter(date_fact__gte=form.cleaned_data['burial_date_from'])
            if form.cleaned_data['burial_date_to']:
                burials = burials.filter(date_fact__lte=form.cleaned_data['burial_date_to'])
            if form.cleaned_data['responsible']:
                burials = burials.filter(place__responsible__last_name__icontains=form.cleaned_data['responsible'])
            if form.cleaned_data['cemetery']:
                burials = burials.filter(place__cemetery=form.cleaned_data['cemetery'])
            if form.cleaned_data['area']:
                burials = burials.filter(place__area=form.cleaned_data['area'])
            if form.cleaned_data['row']:
                burials = burials.filter(place__row=form.cleaned_data['row'])
            if form.cleaned_data['place']:
                burials = burials.filter(place__seat=form.cleaned_data['seat'])
            if form.cleaned_data['no_last_name']:
                burials = burials.filter(Q(deadman__last_name='') | Q(deadman__last_name__isnull=True))
            if form.cleaned_data['no_responsible']:
                burials = burials.filter(place__responsible__isnull=True)

        return burials

    def get_form(self):
        return BurialSearchForm(data=self.request.GET or None)

    def get_context_data(self, **kwargs):
        data = super(BurialsListView, self).get_context_data(**kwargs)
        get_for_paginator = dict([(k, v) for k,v in self.request.GET.items() if k != 'page'])
        data.update(form=self.get_form(), GET_PARAMS=get_for_paginator)
        return data

burial_list = BurialsListView.as_view()

class PlaceView(DetailView):
    template_name = 'view_place.html'
    context_object_name = 'place'
    model = Place

view_place = PlaceView.as_view()

class CreateBurial(TemplateView):
    template_name = 'create_burial.html'

    def get_context_data(self, **kwargs):
        return {
            'burial_form': self.get_burial_form(),
            'deadman_form': self.get_deadman_form(),
            'deadman_address_form': self.get_deadman_address_form(),
            'deadman_dc_form': self.get_deadman_dc_form(),
            'responsible_form': self.get_responsible_form(),
            'responsible_address_form': self.get_responsible_address_form(),
            'responsible_id_form': self.get_responsible_id_form(),
        }

    def get_burial_form(self):
        return BurialForm(data=self.request.POST or None)

    def get_deadman_form(self):
        return DeadPersonForm(data=self.request.POST or None, prefix='deadman')

    def get_deadman_address_form(self):
        return LocationForm(data=self.request.POST or None, prefix='deadman-address')

    def get_deadman_dc_form(self):
        return DeathCertificateForm(data=self.request.POST or None, prefix='deadman-dc')

    def get_responsible_form(self):
        return AlivePersonForm(data=self.request.POST or None, prefix='responsible')

    def get_responsible_address_form(self):
        return LocationForm(data=self.request.POST or None, prefix='responsible-address')

    def get_responsible_id_form(self):
        return PersonIDForm(data=self.request.POST or None, prefix='responsible-personid')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated() or not request.user.profile.is_ugh():
            messages.error(request, _(u"У Вас нет прав создавать захоронения вручную"))
            return redirect('/')
        return super(CreateBurial, self).dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.request = request

        burial_form = self.get_burial_form()
        deadman_form = self.get_deadman_form()
        deadman_address_form = self.get_deadman_address_form()
        deadman_dc_form = self.get_deadman_dc_form()
        responsible_form = self.get_responsible_form()
        responsible_address_form = self.get_responsible_address_form()
        responsible_id_form = self.get_responsible_id_form()

        if burial_form.is_valid() and deadman_form.is_valid() and deadman_dc_form.is_valid():
            burial = burial_form.save(commit=False)

            deadman = deadman_form.save(commit=False)
            if deadman_address_form.is_valid():
                deadman.address = deadman_address_form.save()
            deadman.save()

            dc = deadman_dc_form.save(commit=False)
            dc.person = deadman
            dc.save()

            burial.responsible = responsible_form.save(commit=False)
            if responsible_address_form.is_valid():
                burial.responsible.address = responsible_address_form.save()
            burial.responsible.save()

            if responsible_id_form.is_valid():
                dc = responsible_id_form.save(commit=False)
                dc.person = burial.responsible
                dc.save()

            burial.deadman = deadman

            burial.save()

            write_log(self.request, burial, _(u'Захоронение создано вручную'))
            msg = _(u"<a href='%s'>Захоронение %s</a> создано вручную") % (
                reverse('view_burial', args=[burial.pk]),
                burial.pk,
            )
            messages.success(self.request, msg)

            return redirect('view_burial', burial.pk)

        return self.get(request, *args, **kwargs)

create_burial = CreateBurial.as_view()

