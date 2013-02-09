# coding=utf-8
import datetime

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from burials.forms import BurialSearchForm, BurialForm
from burials.models import Reason, Burial
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
            qs = Q(loru=self.request.user.profile.org) | Q(cemetery__ugh=self.request.user.profile.org) | \
                 Q(creator=self.request.user)
        return qs

class ArchiveView(ArchiveMixin, TemplateView):
    template_name = 'archive.html'

    def get_context_data(self, **kwargs):
        qs = self.get_qs_filter()
        return {'burials': Burial.objects.filter(qs).distinct().order_by('-pk')}

archive = ArchiveView.as_view()

class BurialView(ArchiveMixin, DetailView):
    template_name = 'view_burial.html'
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
        if request.POST.get('back') and request.user.profile.is_loru() and b.can_back():
            b.status = Burial.STATUS_BACKED
            write_log(request, b, _(u'Заявка отозвана'), reason)
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> отозвана") % (
                reverse('view_burial', args=[b.pk]), b.pk,
            ))
        if request.POST.get('ready') and request.user == b.creator and b.is_edit() and b.is_full():
            b.status = Burial.STATUS_READY
            write_log(request, b, _(u'Заявка отправлена на согласование'))
            msg = _(u"<a href='%s'>Заявка %s</a> отправлена на согласование") % (
                reverse('view_burial', args=[b.pk]), b.pk,
            )
            messages.success(request, msg)
        if request.POST.get('approve') and request.user.profile.is_ugh() and b.is_ready_to_approve():
            b.status = Burial.STATUS_APPROVED
            write_log(request, b, _(u'Заявка согласована'))
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> согласована") % (
                reverse('view_burial', args=[b.pk]), b.pk,
            ))
        if request.POST.get('decline') and request.user.profile.is_ugh() and b.is_ready() and b.can_decline():
            b.status = Burial.STATUS_DECLINED
            write_log(request, b, _(u'Заявка отклонена'), reason)
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> отклонена") % (
                reverse('view_burial', args=[b.pk]), b.pk,
            ))
        if request.POST.get('complete') and request.user.profile.is_ugh() and b.is_approved():
            b.status = Burial.STATUS_CLOSED
            b.close()
            write_log(request, b, _(u'Заявка закрыта'))
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> закрыта") % (
                reverse('view_burial', args=[b.pk]), b.pk,
            ))
        if request.POST.get('annulate') and request.user.profile.is_ugh() and b.is_approved():
            b.status = Burial.STATUS_ANNULATED
            write_log(request, b, _(u'Заявка аннулирована'), reason)
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> аннулирована") % (
                reverse('view_burial', args=[b.pk]), b.pk,
            ))
        if old_status != b.status:
            b.save()
        else:
            msg = _(u"Выполнить операцию не удалось: <a href='%s'>заявка</a> в статусе \"%s\"") % (
                reverse('view_burial', args=[b.pk]),
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

view_burial = BurialView.as_view()

class BurialsListView(ListView):
    template_name = 'burial_list.html'
    paginate_by = 20
    context_object_name = 'burials'

    def get_queryset(self):
        if self.request.user.is_authenticated():
            burials = Burial.objects.filter(
                Q(loru=self.request.user.profile.org) |
                Q(cemetery__ugh=self.request.user.profile.org) |
                Q(creator=self.request.user),
                status=Burial.STATUS_CLOSED,
            ).order_by('-pk')
        else:
            burials = Burial.objects.none()
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
        return BurialForm(data=self.request.POST or None, request=self.request)

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
        if not request.user.is_authenticated() or (not request.user.profile.can_create_burials()):
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

        forms = [burial_form, deadman_form, deadman_address_form, deadman_dc_form, responsible_form, responsible_address_form]

        if all([f.is_valid() for f in forms]):
            changed_data = []
            for form in forms:
                for f in form.fields:
                    old_value = form.initial.get(f) or (form.instance and getattr(form.instance, f, None))
                    new_value = form.cleaned_data.get(f)
                    old_value = old_value or ''
                    new_value = new_value or ''
                    try:
                        new_value = new_value.pk
                    except AttributeError:
                        pass
                    if new_value != old_value:
                        changed_data.append((form.fields[f].label, old_value, new_value))

            burial = burial_form.save(commit=False)

            burial.changed = datetime.datetime.now()
            burial.changed_by = request.user

            if not burial.pk:
                burial.creator = request.user
                if self.request.user.profile.is_loru():
                    burial.loru = self.request.user.profile.org
                    burial.source_type = Burial.SOURCE_FULL
                else:
                    burial.source_type = Burial.SOURCE_UGH

            deadman = deadman_form.save(commit=False)
            if deadman_address_form.is_valid_data():
                deadman.address = deadman_address_form.save()
            deadman.save()

            dc = deadman_dc_form.save(commit=False)
            dc.person = deadman
            dc.save()

            burial.responsible = responsible_form.save(commit=False)
            if responsible_address_form.is_valid_data():
                burial.responsible.address = responsible_address_form.save()
            burial.responsible.save()

            if responsible_id_form.is_valid():
                dc = responsible_id_form.save(commit=False)
                dc.person = burial.responsible
                dc.save()

            burial.deadman = deadman

            if self.request.user.profile.is_ugh() and burial.is_ready_to_approve() and self.request.POST.get('approve'):
                burial.status = Burial.STATUS_APPROVED

                write_log(request, burial, _(u'Заявка согласована'))
                messages.success(request, _(u"<a href='%s'>Заявка %s</a> согласована") % (
                    reverse('view_burial', args=[burial.pk]), burial.pk,
                ))

            if self.request.user.profile.is_loru() and burial.is_edit() and self.request.POST.get('ready'):
                burial.status = Burial.STATUS_READY

                write_log(request, burial, _(u'Заявка отправлена на согласование'))
                msg = _(u"<a href='%s'>Заявка %s</a> отправлена на согласование") % (
                    reverse('view_burial', args=[burial.pk]), burial.pk,
                )
                messages.success(request, msg)

            burial.save()

            changed_data_str = u''
            if changed_data:
                changed_data_str = u'\n'.join([u'%s: %s -> %s' % cd for cd in changed_data])

                write_log(self.request, burial, _(u'Заявка сохранена') + changed_data_str)

            msg = _(u"<a href='%s'>Заявка %s</a> сохранена") % (
                reverse('view_burial', args=[burial.pk]),
                burial.pk,
            )
            messages.success(self.request, msg)

            return redirect('view_burial', burial.pk)

        return self.get(request, *args, **kwargs)

create_burial = CreateBurial.as_view()

class EditBurialView(CreateBurial):
    template_name = 'edit_burial.html'
    form_class = BurialForm

    def get_queryset(self):
        q = Q(status=Burial.STATUS_DRAFT) | \
            Q(status=Burial.STATUS_DECLINED) | \
            Q(status=Burial.STATUS_BACKED)

        if self.request.user.profile.is_loru():
            q2 = Q(source_type=Burial.SOURCE_FULL, loru=self.request.user.profile.org)
        elif self.request.user.profile.is_ugh():
            q2 = Q(Q(creator=self.request.user) | Q(cemetery__ugh=self.request.user.profile.org), source_type=Burial.SOURCE_UGH)
        else:
            return Burial.objects.none()

        return Burial.objects.filter(q, q2)

    def get_object(self):
        try:
            return self.get_queryset().get(pk=self.kwargs['pk'])
        except Burial.DoesNotExist:
            raise Http404

    def get_burial_form(self):
        return BurialForm(data=self.request.POST or None, request=self.request, instance=self.get_object())

    def get_deadman_form(self):
        return DeadPersonForm(data=self.request.POST or None, prefix='deadman', instance=self.get_object().deadman)

    def get_deadman_address_form(self):
        addr = self.get_object().deadman and self.get_object().deadman.address
        return LocationForm(data=self.request.POST or None, prefix='deadman-address', instance=addr)

    def get_deadman_dc_form(self):
        dc = self.get_object().deadman and self.get_object().deadman.deathcertificate
        return DeathCertificateForm(data=self.request.POST or None, prefix='deadman-dc', instance=dc)

    def get_responsible_form(self):
        return AlivePersonForm(data=self.request.POST or None, prefix='responsible', instance=self.get_object().responsible)

    def get_responsible_address_form(self):
        addr = self.get_object().responsible and self.get_object().responsible.address
        return LocationForm(data=self.request.POST or None, prefix='responsible-address', instance=addr)

    def get_responsible_id_form(self):
        pid = self.get_object().responsible and self.get_object().responsible.personid
        return PersonIDForm(data=self.request.POST or None, prefix='responsible-personid', instance=pid)

edit_burial = EditBurialView.as_view()

