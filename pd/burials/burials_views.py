# coding=utf-8
import datetime
import json
from django import db

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.query_utils import Q
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render_to_response
from django.template.context import RequestContext
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView

from burials.forms import BurialSearchForm, BurialPublicListForm, BurialForm, BurialCommitForm, BurialCloseForm, AddDocTypeForm
from burials.forms import AddAgentForm, AddDoverForm, AddOrgForm, ExhumationForm
from burials.models import Reason, Burial, Cemetery, Place, ExhumationRequest
from logs.models import write_log
from orders.models import Order
from pd.forms import CommentForm
from reports.models import make_report

class BurialGetOrderMixin:
    """
    Правка, просмотр захоронений пользователем-ЛОРУ производится
    по URL с параметром <order=<номер заказа>. Здесь:
    получение этого номера.
    """
    def get_order(self):
        order = None
        if self.request.REQUEST.get('order'):
            try:
                order = Order.objects.get(pk=self.request.REQUEST.get('order'), loru=self.request.user.profile.org)
            except Order.DoesNotExist:
                pass
        return order

class BurialsListGenericMixin:
    def get_qs_filter(self):
        qs = Q(pk__isnull=True)
        if self.request.user.is_authenticated():
            if self.request.user.profile.is_loru():
                loru = self.request.user.profile.org
                qs = Q(applicant_organization=loru) | Q(loru=loru)
                qs = qs & Q(source_type__in=[Burial.SOURCE_FULL, Burial.SOURCE_TRANSFERRED])
            if self.request.user.profile.is_ugh():
                qs = Q(applicant_organization__ugh_list__ugh=self.request.user.profile.org)
                qs |= Q(loru__ugh_list__ugh=self.request.user.profile.org)
                qs |= Q(ugh=self.request.user.profile.org)
        return qs

class DashboardView(BurialsListGenericMixin, TemplateView):
    template_name = 'dashboard.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated() and request.user.profile.is_loru():
            return redirect('order_dashboard')
        return super(DashboardView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        qs = self.get_qs_filter()
        ex_qs = Q(status__in=[Burial.STATUS_CLOSED, Burial.STATUS_EXHUMATED])
        ex_qs |= Q(source_type=Burial.SOURCE_FULL, status=Burial.STATUS_DRAFT)
        ex_qs |= Q(annulated=True)

        sort = self.request.GET.get('sort', '-pk')
        SORT_FIELDS = {
            'pk': 'pk',
            '-pk': '-pk',
            'account_number': 'account_number',
            '-account_number': '-account_number',
            'cemetery': 'cemetery__name',
            '-cemetery': '-cemetery__name',
            'place': 'place_number',
            '-place': '-place_number',
            'fio': 'deadman__last_name',
            '-fio': '-deadman__last_name',
            'fact_date': 'fact_date',
            '-fact_date': '-fact_date',
            'plan_date': 'plan_date',
            '-plan_date': '-plan_date',
            'type': 'source_type',
            '-type': '-source_type',
            'applicant': ['applicant__last_name', 'applicant_organization__name'],
            '-applicant': ['-applicant__last_name', '-applicant_organization__name'],
            'status': 'status',
            '-status': '-status',
        }
        s = SORT_FIELDS[sort]
        if not isinstance(s, list):
            s = [s]

        burials_clean = Burial.objects.filter(qs).exclude(ex_qs).distinct()
        burials_count = burials_clean.count()
        burials = burials_clean.select_related(
            'ugh', 'place', 'place__cemetery', 'place__area', 'deadman', 'deadman__address', 'cemetery', 'area',
            'applicant_organization', 'applicant', 'changed_by', 'changed_by__profile', 'cemetery__ugh', 'area__purpose'
        ).order_by(*s)
        burials.count = lambda: burials_count
        return {
            'burials': burials,
            'sort': sort,
        }

dashboard = DashboardView.as_view()

class ArchiveMixin(BurialsListGenericMixin):
    def get_qs_filter(self):
        qs = Q(pk__isnull=True)
        if self.request.user.is_authenticated():
            qs = Q(applicant_organization=self.request.user.profile.org) | \
                 Q(ugh=self.request.user.profile.org) | \
                 Q(cemetery__ugh=self.request.user.profile.org)
        return qs

class ArchiveView(ArchiveMixin, ListView):
    template_name = 'archive.html'
    paginate_by = 20
    context_object_name = 'burials'

    def get_context_data(self, **kwargs):
        data = super(ArchiveView, self).get_context_data(**kwargs)
        data['GET_PARAMS'] = u'&'.join([u'%s=%s' % (k,v) for k,v in self.request.GET.items() if k != 'page'])
        return data

    def get_queryset(self, **kwargs):
        qs = self.get_qs_filter()
        return Burial.objects.filter(qs).distinct().order_by('-pk').select_related(
            'ugh', 'place', 'place__cemetery', 'place__area', 'deadman', 'deadman__address', 'cemetery', 'area',
            'applicant_organization', 'applicant', 'changed_by', 'changed_by__profile',
        )

archive = ArchiveView.as_view()

class BurialView(BurialsListGenericMixin, BurialGetOrderMixin, DetailView):
    template_name = 'view_burial.html'
    context_object_name = 'b'

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        order = self.get_order()
        b = self.get_object()
        # Помешаем вставлять абы что в адресную строку браузера
        if request.user.profile.is_loru() and not (order and b and order.burial == b):
                return redirect('/')
        return super(BurialView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = self.get_qs_filter()
        burials = Burial.objects.filter(qs)
        burials = burials.select_related('cemetery', 'applicant_organization', 'ugh', 'deadman', 'deadman__address')
        return burials

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('dashboard')

        b = self.get_object()
        
        order_parm = ''
        if self.request.user.profile.is_loru():
            order = self.get_order()
            # Такое здесь, уже на коммите, возможно при фокусах в адресной строке браузера ???
            if not order:
                return redirect('/')
            order_parm = '?order=%s' % order.pk

        b.changed = datetime.datetime.now()
        b.changed_by = request.user
        old_status = b.status
        old_annulated = b.annulated
        redirect_to_view = False
        redirect_to_edit = False
        reason = request.POST.get('reason') or request.POST.get('reason_typical')
        if request.POST.get('back') and request.user.profile.is_loru() and b.can_back():
            b.status = Burial.STATUS_BACKED
            b.account_number = None
            write_log(request, b, _(u'Захоронение отозвано'), reason)
            messages.success(request, _(u"<a href='%s'>Захоронение %s</a> отозвано") % (
                reverse('view_burial', args=[b.pk]) + order_parm, b.pk,
            ))
            redirect_to_edit = True

        if request.POST.get('ready') and b.is_edit() and b.is_full():
            return redirect(reverse('edit_burial', args=[b.pk]) + '?action=ready')
        if request.POST.get('approve') and request.user.profile.is_ugh() and b.can_approve():
            if b.is_full():
                b.status = Burial.STATUS_APPROVED
                b.approve(self.request.user)
                write_log(request, b, _(u'Захоронение согласовано'))
                messages.success(request, _(u"<a href='%s'>Захоронение %s</a> согласовано") % (
                    reverse('view_burial', args=[b.pk]), b.pk,
                ))
            else:
                return redirect(reverse('edit_burial', args=[b.pk]) + '?action=approve')
        if request.POST.get('decline') and request.user.profile.is_ugh() and b.can_decline():
            b.status = Burial.STATUS_DECLINED
            b.account_number = None
            msg_declined = u'Захоронение отклонено'
            write_log(request, b, msg_declined, reason)
            messages.success(request, _(u"<a href='%s'>Захоронение %s</a> отклонено") % (
                reverse('view_burial', args=[b.pk]), b.pk,
            ))
        if request.POST.get('complete') and request.user.profile.is_ugh() and b.can_finish():
            close_form = self.get_close_form()
            if close_form.is_valid():
                b = close_form.save()
                if b.is_ugh():
                    return redirect(reverse('edit_burial', args=[b.pk]) + '?action=complete')
                else:
                    b.status = Burial.STATUS_CLOSED
                    b.close()
                    write_log(request, b, _(u'Захоронение закрыто'))
                    messages.success(request, _(u"<a href='%s'>Захоронение %s</a> закрыто") % (
                        reverse('view_burial', args=[b.pk]), b.pk,
                    ))
            else:
                return self.get(request, *args, **kwargs)
        if request.POST.get('annulate') and \
            (request.user.profile.is_ugh() and b.can_ugh_annulate() or \
             request.user.profile.is_loru() and b.can_loru_annulate() \
            ):
            b.annulated = True
            write_log(request, b, _(u'Захоронение аннулировано'), reason)
            messages.success(request, _(u"<a href='%s'>Захоронение %s</a> аннулировано") % (
                reverse('view_burial', args=[b.pk]) + order_parm, b.pk,
            ))
            redirect_to_view = True

        if request.POST.get('deannulate') and \
           (request.user.profile.is_ugh() and b.can_ugh_deannulate() or \
            request.user.profile.is_loru() and b.can_loru_deannulate()
           ):
            b.annulated = False
            write_log(request, b, _(u'Захоронение восстановлено после аннулирования'))
            messages.success(request, _(u"<a href='%s'>Захоронение %s</a> восстановлено после аннулирования") % (
                reverse('view_burial', args=[b.pk]) + order_parm, b.pk,
            ))
            redirect_to_view = request.user.profile.is_ugh()
            redirect_to_edit = request.user.profile.is_loru()
        if old_status != b.status or old_annulated != b.annulated:
            b.save()
        else:
            msg = _(u"Выполнить операцию не удалось: <a href='%s'>захоронение в статусе \"%s\"") % (
                reverse('view_burial', args=[b.pk]) + order_parm,
                b.get_status_display(),
            )
            messages.success(request, msg)
            
        if redirect_to_view:
            return redirect(reverse('view_burial', args=[b.pk]) + order_parm)
        elif redirect_to_edit:
            return redirect(reverse('edit_burial', args=[b.pk]) + order_parm)
        return redirect('dashboard')

    def get_close_form(self):
        return BurialCloseForm(request=self.request, data=self.request.POST or None, instance=self.get_object())

    def get_object(self, queryset=None):
        if not hasattr(self, '_object'):
            self._object = super(BurialView, self).get_object(queryset=queryset)
        return self._object

    def get_context_data(self, **kwargs):
        b = self.get_object()
        return {
            'b': b,
            'reason_typical_back': Reason.objects.filter(reason_type=Reason.TYPE_BACK),
            'reason_typical_decline': Reason.objects.filter(reason_type=Reason.TYPE_DECLINE),
            'reason_typical_annulate': Reason.objects.filter(reason_type=Reason.TYPE_ANNULATE),
            'close_form': self.get_close_form(),
            'comment_form': CommentForm(),
            'is_accessible': b.loru and self.request.user.profile.org in b.loru.get_loru_list(),
            'order': self.get_order(),
        }

view_burial = BurialView.as_view()

class BurialsListView(ListView):
    template_name = 'burial_list.html'
    context_object_name = 'burials'

    def get_queryset(self):
        if not self.request.GET:
            return Burial.objects.none()

        if self.request.user.is_authenticated():
            burials = Burial.objects.filter(
                Q(applicant_organization=self.request.user.profile.org) | Q(ugh=self.request.user.profile.org),
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
                    q &= Q(deadman__middle_name__istartswith=fio[2])
                if len(fio) > 1:
                    q &= Q(deadman__first_name__istartswith=fio[1])
                if len(fio) > 0:
                    q &= Q(deadman__last_name__istartswith=fio[0])
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
                burials = burials.filter(fact_date__gte=form.cleaned_data['burial_date_from'])
            if form.cleaned_data['burial_date_to']:
                burials = burials.filter(fact_date__lte=form.cleaned_data['burial_date_to'])
            if form.cleaned_data['account_number_from']:
                burials = burials.filter(account_number__gte=form.cleaned_data['account_number_from'])
            if form.cleaned_data['account_number_to']:
                burials = burials.filter(account_number__lte=form.cleaned_data['account_number_to'])
            if form.cleaned_data['responsible']:
                fio = [f.strip('.') for f in form.cleaned_data['responsible'].split(' ')]
                q1r = Q(responsible__isnull=False)
                q2r = Q(place__isnull=False)
                if len(fio) > 2:
                    q1r &= Q(responsible__middle_name__istartswith=fio[2])
                    q2r &= Q(place__responsible__middle_name__istartswith=fio[2])
                if len(fio) > 1:
                    q1r &= Q(responsible__first_name__istartswith=fio[1])
                    q2r &= Q(place__responsible__first_name__istartswith=fio[1])
                if len(fio) > 0:
                    q1r &= Q(responsible__last_name__istartswith=fio[0])
                    q2r &= Q(place__responsible__last_name__istartswith=fio[0])
                qr = Q(q1r | q2r)
                burials = burials.filter(qr)
            if form.cleaned_data['cemetery']:
                burials = burials.filter(cemetery__name=form.cleaned_data['cemetery'])
            if form.cleaned_data['area']:
                burials = burials.filter(area__name=form.cleaned_data['area'])
            if form.cleaned_data['row']:
                burials = burials.filter(row=form.cleaned_data['row'])
            if form.cleaned_data['place']:
                burials = burials.filter(place_number=form.cleaned_data['place'])
            if form.cleaned_data['no_last_name']:
                burials = burials.filter(Q(deadman__last_name='') | Q(deadman__last_name__isnull=True))
            if form.cleaned_data['no_responsible']:
                burials = burials.filter(place__responsible__isnull=True)
            if form.cleaned_data['source']:
                burials = burials.filter(source_type=form.cleaned_data['source'])
            if form.cleaned_data['status']:
                burials = burials.filter(status=form.cleaned_data['status'])
            if form.cleaned_data['applicant_org']:
                burials = burials.filter(applicant_organization__name__istartswith=form.cleaned_data['applicant_org'])
            if form.cleaned_data['applicant_person']:
                fio = [f.strip('.') for f in form.cleaned_data['applicant_person'].split(' ')]
                qa = Q()
                if len(fio) > 2:
                    qa &= Q(applicant__middle_name__istartswith=fio[2])
                if len(fio) > 1:
                    qa &= Q(applicant__first_name__istartswith=fio[1])
                if len(fio) > 0:
                    qa &= Q(applicant__last_name__istartswith=fio[0])
                burials = burials.filter(qa)
            if form.cleaned_data['burial_container']:
                burials = burials.filter(burial_container=form.cleaned_data['burial_container'])
            if form.cleaned_data['annulated']:
                burials = burials.filter(annulated=True)
            else:
                burials = burials.filter(annulated=False)

            if form.cleaned_data.get('status') == Burial.STATUS_EXHUMATED:
                burials = burials.filter(status=Burial.STATUS_EXHUMATED)
            else:
                burials = burials.exclude(status=Burial.STATUS_EXHUMATED)
        else:
            burials = burials.exclude(status=Burial.STATUS_EXHUMATED)

        sort = self.request.GET.get('sort', '-pk')
        SORT_FIELDS = {
            'pk': 'pk',
            '-pk': '-pk',
            'account_number': 'account_number',
            '-account_number': '-account_number',
            'cemetery': 'cemetery__name',
            '-cemetery': '-cemetery__name',
            'place': 'place_number',
            '-place': '-place_number',
            'fio': 'deadman__last_name',
            '-fio': '-deadman__last_name',
            'fact_date': 'fact_date',
            '-fact_date': '-fact_date',
            'type': 'source_type',
            '-type': '-source_type',
            'applicant': ['applicant__last_name', 'applicant_organization__name'],
            '-applicant': ['-applicant__last_name', '-applicant_organization__name'],
            'status': 'status',
            '-status': '-status',
        }
        s = SORT_FIELDS[sort]
        if not isinstance(s, list):
            s = [s]

        burials_count = burials.count()
        burials = burials.select_related(
            'ugh', 'place', 'place__cemetery', 'place__area', 'deadman', 'deadman__address', 'cemetery', 'area',
            'applicant_organization', 'applicant', 'changed_by', 'changed_by__profile', 'cemetery__ugh',
            'area__purpose', 'responsible',
        ).order_by(*s)
        burials.count = lambda: burials_count
        return burials

    def get_template_names(self):
        if self.request.GET.get('print'):
            return 'burial_list_print.html'
        return super(BurialsListView, self).get_template_names()

    def get_paginate_by(self, queryset):
        if self.request.GET.get('print'):
            return None
        try:
            return int(self.request.GET.get('per_page'))
        except (TypeError, ValueError):
            return 25

    def get_form(self):
        return BurialSearchForm(data=self.request.GET or None)

    def get_context_data(self, **kwargs):
        data = super(BurialsListView, self).get_context_data(**kwargs)
        DISPLAY_OPTIONS = ['page', 'print']
        get_for_paginator = u'&'.join([u'%s=%s' %  (k, v) for k,v in self.request.GET.items() if k not in DISPLAY_OPTIONS])
        sort = self.request.GET.get('sort', '-pk')
        data.update(form=self.get_form(), GET_PARAMS=get_for_paginator, sort=sort)
        return data

burial_list = BurialsListView.as_view()

# Поиск захоронения для ЛОРУ
#
class BurialsPublicListView(ListView):
    template_name = 'burial_public_list.html'
    context_object_name = 'burials'

    def get_queryset(self):
        if not self.request.GET:
            return Burial.objects.none()

        if self.request.user.is_authenticated() and self.request.user.profile.is_loru():
            burials = Burial.objects.filter(
                Q(ugh__loru_list__loru=self.request.user.profile.org) &
                Q(annulated=False) &
                Q(status__in=[Burial.STATUS_EXHUMATED, Burial.STATUS_CLOSED, ])
            ).exclude(burial_container=Burial.CONTAINER_BIO).order_by('-pk')
        else:
            burials = Burial.objects.none()
        form = self.get_form()
        if form.data and form.is_valid():
            if form.cleaned_data['fio']:
                fio = [f.strip('.') for f in form.cleaned_data['fio'].split(' ')]
                q = Q()
                if len(fio) > 2:
                    q &= Q(deadman__middle_name__istartswith=fio[2])
                if len(fio) > 1:
                    q &= Q(deadman__first_name__istartswith=fio[1])
                if len(fio) > 0:
                    q &= Q(deadman__last_name__istartswith=fio[0])
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
                burials = burials.filter(fact_date__gte=form.cleaned_data['burial_date_from'])
            if form.cleaned_data['burial_date_to']:
                burials = burials.filter(fact_date__lte=form.cleaned_data['burial_date_to'])
            if form.cleaned_data['account_number_from']:
                burials = burials.filter(account_number__gte=form.cleaned_data['account_number_from'])
            if form.cleaned_data['account_number_to']:
                burials = burials.filter(account_number__lte=form.cleaned_data['account_number_to'])
            if form.cleaned_data['cemetery']:
                burials = burials.filter(cemetery__name=form.cleaned_data['cemetery'])
            if form.cleaned_data['area']:
                burials = burials.filter(area__name=form.cleaned_data['area'])
            if form.cleaned_data['row']:
                burials = burials.filter(row=form.cleaned_data['row'])
            if form.cleaned_data['place']:
                burials = burials.filter(place_number=form.cleaned_data['place'])

        sort = self.request.GET.get('sort', '-pk')
        SORT_FIELDS = {
            'pk': 'pk',
            '-pk': '-pk',
            'account_number': 'account_number',
            '-account_number': '-account_number',
            'cemetery': 'cemetery__name',
            '-cemetery': '-cemetery__name',
            'place': 'place_number',
            '-place': '-place_number',
            'fio': 'deadman__last_name',
            '-fio': '-deadman__last_name',
            'fact_date': 'fact_date',
            '-fact_date': '-fact_date',
            'status': 'status',
            '-status': '-status',
        }
        s = SORT_FIELDS[sort]
        if not isinstance(s, list):
            s = [s]
        burials = burials.select_related(
            'ugh', 'place', 'place__cemetery', 'place__area', 'deadman', 'cemetery', 'area',
        ).order_by(*s)
        return burials

    def get_paginate_by(self, queryset):
        try:
            return int(self.request.GET.get('per_page'))
        except (TypeError, ValueError):
            return 25

    def get_form(self):
        return BurialPublicListForm(data=self.request.GET or None)

    def get_context_data(self, **kwargs):
        data = super(BurialsPublicListView, self).get_context_data(**kwargs)
        DISPLAY_OPTIONS = ['page', 'print']
        get_for_paginator = u'&'.join([u'%s=%s' %  (k, v) for k,v in self.request.GET.items() if k not in DISPLAY_OPTIONS])
        sort = self.request.GET.get('sort', '-pk')
        data.update(form=self.get_form(), GET_PARAMS=get_for_paginator, sort=sort)
        return data

burial_public_list = BurialsPublicListView.as_view()

class CreateBurial(BurialGetOrderMixin, CreateView):
    template_name = 'create_burial.html'
    form_class = BurialForm

    def get_context_data(self, **kwargs):
        data = super(CreateBurial, self).get_context_data(**kwargs)
        data.update({
            'b': self.get_object(),
            'agent_form': AddAgentForm(prefix='agent'),
            'agent_dover_form': AddDoverForm(prefix='agent_dover'),
            'dover_form': AddDoverForm(prefix='dover'),
            'loru_form': AddOrgForm(request=self.request, prefix='loru'),
            'doc_type_form': AddDocTypeForm(prefix='doctype'),
            'order': self.get_order(),
        })
        return data

    def get_object(self, *args, **kwargs):
        return None

    def get_form_kwargs(self, *args, **kwargs):
        data = super(CreateBurial, self).get_form_kwargs(*args, **kwargs)
        if self.request.REQUEST.get('place_id'):
            place = Place.objects.get(pk=self.request.REQUEST.get('place_id'))
            if not data.get('instance'):
                data['instance'] = Burial(
                    cemetery=place.cemetery,
                    area=place.area,
                    row=place.row,
                    place_number=place.place,
                    responsible=place.responsible,
                )
        data['request'] = self.request
        return data

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

        if not request.user.is_authenticated() or (not request.user.profile.can_create_burials()):
            messages.error(request, _(u"У Вас нет прав создавать захоронения вручную"))
            return redirect('/')

        # Из старого кода (с burial::order). Непонятно.
        #order = self.get_order()
        #if order and order.get_burial() and order.get_burial() != self.get_object():
            #return redirect('edit_burial', order.burial.pk)

        return super(CreateBurial, self).dispatch(request, *args, **kwargs)

    def form_invalid(self, form, *args, **kwargs):
        messages.error(self.request, _(u'Обнаружены ошибки, их необходимо исправить'))
        return super(CreateBurial, self).form_invalid(form, *args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        b = form.save()

        order_parm = ''
        if self.request.user.profile.is_loru():
            order = self.get_order()
            # Такое здесь, уже на коммите, возможно при фокусах в адресной строке браузера ???
            if not order:
                return redirect('/')
            if not order.burial: # or order.burial.pk != b.bk Может ли быть такое ???
                order.burial = b
                order.save()
            order_parm = '?order=%s' % order.pk

        action = self.get_action()
        if action:
            redirect_to_view = False
            old_status = b.status
            old_annulated = b.annulated

            if action == 'ready' and self.request.user.profile.is_loru() and b.is_edit() and b.is_full():
                b.status = Burial.STATUS_READY
                write_log(self.request, b, _(u'Захоронение отправлено на согласование'))
                msg = _(u"<a href='%s'>Захоронение %s</a> отправлено на согласование") % (
                    reverse('view_burial', args=[b.pk]) + order_parm, b.pk,
                )
                messages.success(self.request, msg)

            if action == 'annulate' and self.request.user.profile.is_loru() and b.can_loru_annulate():
                b.annulated = True
                write_log(self.request, b, _(u'Захоронение аннулировано'))
                msg = _(u"<a href='%s'>Захоронение %s</a> аннулировано") % (
                    reverse('view_burial', args=[b.pk]) + order_parm, b.pk,
                )
                messages.success(self.request, msg)

            if action == 'approve' and self.request.user.profile.is_ugh() and b.can_approve() and b.is_ugh_only():
                b.status = Burial.STATUS_APPROVED
                b.approve(self.request.user)
                write_log(self.request, b, _(u'Захоронение согласовано'))
                messages.success(self.request, _(u"<a href='%s'>Захоронение %s</a> согласовано") % (
                    reverse('view_burial', args=[b.pk]), b.pk,
                ))

            if action == 'complete' and self.request.user.profile.is_ugh() and b.can_finish() and b.is_ugh():
                b.status = Burial.STATUS_CLOSED
                b.changed_by = self.request.user
                b.close()
                write_log(self.request, b, _(u'Захоронение закрыто'))
                messages.success(self.request, _(u"<a href='%s'>Захоронение %s</a> закрыто") % (
                    reverse('view_burial', args=[b.pk]), b.pk,
                ))
                redirect_to_view = True

            if old_status != b.status or old_annulated != b.annulated:
                b.save()
            else:
                msg = _(u"Выполнить операцию не удалось: <a href='%s'>захоронение</a> в статусе \"%s\"") % (
                    reverse('view_burial', args=[b.pk]) + order_parm,
                    b.get_status_display(),
                )
                messages.success(self.request, msg)

            if self.request.user.profile.is_loru():
                self.request.session['order_burial_saved'] = True
                if b.is_edit() and not b.annulated:
                    return redirect(reverse('edit_burial', args=[b.pk]) + order_parm)
                else:
                    return redirect(reverse('view_burial', args=[b.pk]) + order_parm)

            if redirect_to_view:
                return redirect(reverse('view_burial', args=[b.pk]) + order_parm)
            else:
                return redirect('dashboard')
        else:
            if self.request.user.profile.is_loru():
                self.request.session['order_burial_saved'] = True
                if b.is_edit():
                    return redirect(reverse('edit_burial', args=[b.pk]) + order_parm)
                else:
                    redirect(reverse('view_burial', args=[b.pk]) + order_parm)
            return redirect(reverse('view_burial', args=[b.pk]) + order_parm)

    def get_action(self):
        action = self.request.REQUEST.get('action')
        if self.request.REQUEST.get('approve'):
            action = 'approve'
        if self.request.REQUEST.get('ready'):
            action = 'ready'
        if self.request.REQUEST.get('complete'):
            action = 'complete'
        if self.request.REQUEST.get('annulate'):
            action = 'annulate'
        return action

    def get_form_class(self):
        action =  self.get_action()
        if action and action != 'annulate':
            return BurialCommitForm
        elif self.get_object() and self.get_object().is_finished() and self.request.user.profile.is_ugh():
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

class EditBurialView(BurialsListGenericMixin, CreateBurial):
    template_name = 'edit_burial.html'
    context_object_name = 'b'

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        # Помешаем вставлять абы что в адресную строку браузера
        order = self.get_order()
        b = self.get_object()
        if request.user.profile.is_loru() and not (order and b and order.burial == b):
            return redirect('/')
        return super(EditBurialView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        q = self.get_qs_filter()

        if self.request.user.profile.is_loru():
            q3 = Q(status__in=[Burial.STATUS_DRAFT, Burial.STATUS_DECLINED, Burial.STATUS_BACKED], annulated=False)
            q3 |= Q(source_type__in=[Burial.SOURCE_TRANSFERRED])
            q2 = q & q3
        elif self.request.user.profile.is_ugh():
            q3 = Q(source_type__in=[Burial.SOURCE_UGH, Burial.SOURCE_ARCHIVE, Burial.SOURCE_TRANSFERRED])
            q3 |= Q(status__in=[Burial.STATUS_CLOSED, ])
            q2 = q & q3
        else:
            return Burial.objects.none()

        return Burial.objects.filter(q2)

    def get_object(self):
        if getattr(self, '_burial', None):
            return self._burial
        try:
            self._burial = self.get_queryset().distinct().get(pk=self.kwargs['pk'])
            return self._burial
        except Burial.DoesNotExist:
            raise Http404

    def get_form_kwargs(self, *args, **kwargs):
        data = super(EditBurialView, self).get_form_kwargs(*args, **kwargs)
        data['instance'] = self.get_object()
        return data

edit_burial = EditBurialView.as_view()

class MakeNotificationView(BurialsListGenericMixin, DetailView):
    context_object_name = 'burial'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return Burial.objects.filter(qs).distinct()

    def render_to_response(self, context, **response_kwargs):
        context['now'] = datetime.datetime.now()
        template = 'reports/notification.html'
        if self.request.user.profile.is_ugh():
            report = make_report(
                user=self.request.user,
                msg=_(u"Уведомление"),
                obj=self.get_object(),
                template=template,
                context=RequestContext(self.request, context),
            )
        context['user'] = self.request.user
        return render_to_response(template, context)

make_notification = MakeNotificationView.as_view()

class MakeExhumateReport(BurialsListGenericMixin, DetailView):
    context_object_name = 'burial'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return Burial.objects.filter(qs).distinct()

    def render_to_response(self, context, **response_kwargs):
        context['user'] = self.request.user
        template = 'simple_message.html'
        if self.request.user.is_authenticated() and self.request.user.profile.is_ugh():
            if self.get_object().exhumated:
                template = 'reports/exhumate.html'
            else:
                context['message'] = _(u"Захоронение не эксгумировано")
        else:
            context['message'] = _(u"Нет доступа")
        return render_to_response(template, context)

make_exhumate_report = MakeExhumateReport.as_view()

class MakeExhumateNotification(BurialsListGenericMixin, DetailView):
    context_object_name = 'burial'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return Burial.objects.filter(qs).distinct()

    def render_to_response(self, context, **response_kwargs):
        context['user'] = self.request.user
        template = 'simple_message.html'
        if self.request.user.is_authenticated() and self.request.user.profile.is_ugh():
            if self.get_object().exhumated:
                template = 'reports/exhumate_notification.html'
            else:
                context['message'] = _(u"Захоронение не эксгумировано")
        else:
            context['message'] = _(u"Нет доступа")
        return render_to_response(template, context)

make_exhumate_notification = MakeExhumateNotification.as_view()

class MakeSpravka(BurialsListGenericMixin, DetailView):
    context_object_name = 'burial'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return Burial.objects.filter(qs).distinct()

    def render_to_response(self, context, **response_kwargs):
        context['now'] = datetime.datetime.now()
        report = make_report(
            user=self.request.user,
            msg=_(u"Справка"),
            obj=self.get_object(),
            template='reports/spravka.html',
            context=RequestContext(self.request, context),
        )
        return redirect('report_view', report.pk)

make_spravka = MakeSpravka.as_view()

class GetCemeteryTimes(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            messages.error(request, _(u"Доступно только для пользователей"))
            return redirect('/')
        c = Cemetery.objects.get(pk=request.GET.get('cem'))
        date = datetime.datetime.strptime(request.GET.get('date'), '%d.%m.%Y').date
        data = c.get_time_choices(date=date, request=request)
        return HttpResponse(json.dumps({c.pk: data}), mimetype='application/json')

cemetery_times = GetCemeteryTimes.as_view()

class ExhumateView(ArchiveMixin, DetailView):
    context_object_name = 'burial'
    template_name = 'exhumate_burial.html'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return Burial.objects.filter(qs).distinct()

    def get_form(self):
        return ExhumationForm(data=self.request.POST or None, request=self.request, burial=self.get_object())

    def get_context_data(self, **kwargs):
        data = super(ExhumateView, self).get_context_data(**kwargs)
        data['form'] = self.get_form()
        if data['form'].data:
            data['form'].is_valid()
        return data

    def post(self, request, *args, **kwargs):
        self.request = request
        f = self.get_form()
        if f.is_valid():
            ex = f.save()
            write_log(self.request, self.get_object(), _(u'Захоронение эксгумировано'))
            messages.success(request, _(u"Эксгумация успешна"))
            if ex.place:
                return redirect('view_place', ex.place.pk)
            else:
                return redirect('view_burial', ex.burial.pk)
        else:
            messages.error(request, _(u"Обнаружены ошибки"))
            return self.get(request, *args, **kwargs)

burial_exhumate = ExhumateView.as_view()

class CancelExhumationView(ArchiveMixin, DeleteView):
    def delete(self, *args, **kwargs):
        self.burial = self.get_object().burial
        self.place = self.get_object().place or self.burial.get_place()
        return super(CancelExhumationView, self).delete(*args, **kwargs)

    def get_success_url(self):
        write_log(self.request, self.burial, _(u'Эксгумация отменена'))
        messages.success(self.request, _(u"Эксгумация отменена"))
        if self.place and self.place.pk:
            return reverse('view_place', args=[self.place.pk])
        else:
            return reverse('dashboard')

    def get_queryset(self):
        qs = Q(burial__ugh=self.request.user.profile.org) | Q(burial__cemetery__ugh=self.request.user.profile.org)
        return ExhumationRequest.objects.filter(qs).distinct()

burial_cancel_exhumation = CancelExhumationView.as_view()

class RemoveResponsible(ArchiveMixin, View):
    def post(self, request, *args, **kwargs):
        qs = Q(burial__ugh=self.request.user.profile.org) | Q(cemetery__ugh=self.request.user.profile.org)
        place = Place.objects.get(qs, pk=kwargs['pk'])
        resp = place.responsible
        if resp:
            place.remove_responsible()
            write_log(self.request, place, _(u'Ответственный %s откреплен') % resp)
            messages.success(self.request, _(u"Ответственный %s откреплен") % resp)
        return redirect('view_place', place.pk)

rm_responsible = RemoveResponsible.as_view()