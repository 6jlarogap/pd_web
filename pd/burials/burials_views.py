# coding=utf-8
import datetime
from django import db

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.query_utils import Q
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from burials.forms import BurialSearchForm, BurialForm, BurialCommitForm
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
            qs = Q(loru=self.request.user.profile.org) | Q(ugh=self.request.user.profile.org)
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
        if request.POST.get('ready') and b.is_edit() and b.is_full():
            return redirect(reverse('edit_burial', args=[b.pk]) + '?action=ready')
        if request.POST.get('approve') and request.user.profile.is_ugh() and b.can_approve():
            if b.is_full():
                b.status = Burial.STATUS_APPROVED
                write_log(request, b, _(u'Заявка согласована'))
                messages.success(request, _(u"<a href='%s'>Заявка %s</a> согласована") % (
                    reverse('view_burial', args=[b.pk]), b.pk,
                ))
            else:
                return redirect(reverse('edit_burial', args=[b.pk]) + '?action=approve')
        if request.POST.get('decline') and request.user.profile.is_ugh() and b.can_decline():
            b.status = Burial.STATUS_DECLINED
            write_log(request, b, _(u'Заявка отклонена'), reason)
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> отклонена") % (
                reverse('view_burial', args=[b.pk]), b.pk,
            ))
        if request.POST.get('complete') and request.user.profile.is_ugh() and b.can_finish():
            if b.is_archive():
                return redirect(reverse('edit_burial', args=[b.pk]) + '?action=complete')
            else:
                b.status = Burial.STATUS_CLOSED
                b.close()
                write_log(request, b, _(u'Заявка закрыта'))
                messages.success(request, _(u"<a href='%s'>Заявка %s</a> закрыта") % (
                    reverse('view_burial', args=[b.pk]), b.pk,
                ))
        if request.POST.get('annulate') and request.user.profile.is_ugh() and b.can_annulate():
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
                Q(loru=self.request.user.profile.org) | Q(ugh=self.request.user.profile.org),
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

class CreateBurial(CreateView):
    template_name = 'create_burial.html'
    form_class = BurialForm

    def get_context_data(self, **kwargs):
        data = super(CreateBurial, self).get_context_data(**kwargs)
        data.update({'b': self.get_object()})
        return data

    def get_object(self, *args, **kwargs):
        return None

    def get_form_kwargs(self, *args, **kwargs):
        data = super(CreateBurial, self).get_form_kwargs(*args, **kwargs)
        data['request'] = self.request
        return data

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated() or (not request.user.profile.can_create_burials()):
            messages.error(request, _(u"У Вас нет прав создавать захоронения вручную"))
            return redirect('/')
        return super(CreateBurial, self).dispatch(request, *args, **kwargs)

    def form_invalid(self, form, *args, **kwargs):
        messages.error(self.request, _(u'Обнаружены ошибки, их необходимо исправить'))
        return super(CreateBurial, self).form_invalid(form, *args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        b = form.save()

        action = self.get_action()
        if action:
            old_status = b.status

            if action == 'ready' and self.request.user.profile.is_loru() and b.is_edit() and b.is_full():
                b.status = Burial.STATUS_READY
                write_log(self.request, b, _(u'Заявка отправлена на согласование'))
                msg = _(u"<a href='%s'>Заявка %s</a> отправлена на согласование") % (
                    reverse('view_burial', args=[b.pk]), b.pk,
                )
                messages.success(self.request, msg)

            if action == 'approve' and self.request.user.profile.is_ugh() and b.can_approve() and b.is_ugh_only():
                b.status = Burial.STATUS_APPROVED
                write_log(self.request, b, _(u'Заявка согласована'))
                messages.success(self.request, _(u"<a href='%s'>Заявка %s</a> согласована") % (
                    reverse('view_burial', args=[b.pk]), b.pk,
                ))

            if action == 'complete' and self.request.user.profile.is_ugh() and b.can_finish() and b.is_archive():
                b.status = Burial.STATUS_CLOSED
                write_log(self.request, b, _(u'Заявка закрыта'))
                messages.success(self.request, _(u"<a href='%s'>Заявка %s</a> закрыта") % (
                    reverse('view_burial', args=[b.pk]), b.pk,
                ))

            if old_status != b.status:
                b.save()
            else:
                msg = _(u"Выполнить операцию не удалось: <a href='%s'>заявка</a> в статусе \"%s\"") % (
                    reverse('view_burial', args=[b.pk]),
                    b.get_status_display(),
                )
                messages.success(self.request, msg)
            return redirect('dashboard')
        else:
            return redirect('view_burial', b.pk)

    def get_action(self):
        action = self.request.REQUEST.get('action')
        if self.request.REQUEST.get('approve'):
            action = 'approve'
        if self.request.REQUEST.get('ready'):
            action = 'ready'
        return action

    def get_form_class(self):
        if self.get_action():
            return BurialCommitForm
        else:
            return BurialForm

    def get(self, request, *args, **kwargs):
        if self.get_action():
            request.POST = request.POST.copy()
            request.method = 'POST'
            return self.post(request, *args, **kwargs)
        else:
            return super(CreateBurial, self).get(request, *args, **kwargs)

create_burial = CreateBurial.as_view()

class EditBurialView(CreateBurial):
    template_name = 'edit_burial.html'
    context_object_name = 'b'

    def get_queryset(self):
        q = Q(status=Burial.STATUS_DRAFT) | \
            Q(status=Burial.STATUS_DECLINED) | \
            Q(status=Burial.STATUS_BACKED)

        if self.request.user.profile.is_loru():
            q2 = Q(source_type=Burial.SOURCE_FULL, loru=self.request.user.profile.org)
        elif self.request.user.profile.is_ugh():
            q2 = Q(source_type__in=[Burial.SOURCE_UGH, Burial.SOURCE_ARCHIVE], ugh=self.request.user.profile.org)
        else:
            return Burial.objects.none()

        return Burial.objects.filter(q, q2)

    def get_object(self):
        try:
            return self.get_queryset().get(pk=self.kwargs['pk'])
        except Burial.DoesNotExist:
            raise Http404

    def get_form_kwargs(self, *args, **kwargs):
        data = super(EditBurialView, self).get_form_kwargs(*args, **kwargs)
        data['instance'] = self.get_object()
        return data

edit_burial = EditBurialView.as_view()
