import datetime, time, os, csv, re, tempfile, zipfile
import json
from django import db

from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.db.models.query_utils import Q
from django.http import Http404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.generic.base import TemplateView, View
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from burials.forms import BurialSearchForm, BurialPublicListForm, BurialForm, BurialCommitForm, \
                          BurialApproveCloseForm, AddDocTypeForm, AddGravesForm, SpravkaForm, \
                          RegistryForm
from burials.forms import AddAgentForm, AddDoverForm, AddOrgForm, ExhumationForm
from burials.models import Reason, Burial, Burial1, Cemetery, Area, Place, ExhumationRequest, OrderPlace, Debitor
from persons.models import DeathCertificate, OrderDeadPerson, DeadPerson, AlivePerson
from logs.models import write_log
from orders.models import Order
from users.models import Org, Profile, is_cabinet_user, is_ugh_user, is_loru_user
from pd.utils import re_search, host_country_code
from pd.forms import CommentForm
from pd.views import PaginateListView, FormInvalidMixin, get_front_end_url, ManualEncodedCsvMixin
from reports.models import make_report

class BurialGetOrderMixin:
    """
    Правка, просмотр захоронений пользователем-ЛОРУ производится
    по URL с параметром <order=<номер заказа>. Здесь:
    получение объекта заказа, соответствующего этому номеру.
    """
    def get_order(self):
        order = None
        order_pk = self.request.GET.get('order') or self.request.POST.get('order')
        if order_pk:
            try:
                order = Order.objects.get(pk=order_pk, loru=self.request.user.profile.org)
            except Order.DoesNotExist:
                pass
        return order

    def get_funeral_order(self):
        order = None
        funeral_order_pk = self.request.GET.get('funeral_order') or self.request.POST.get('funeral_order')
        if funeral_order_pk and self.request.user.profile.is_ugh():
            try:
                order = Order.objects.filter(
                    type=Order.TYPE_FUNERAL,
                    pk=funeral_order_pk,
                    loru__ugh_list__ugh=self.request.user.profile.org,
                    status=Order.STATUS_PAID,
                )[0]
            except IndexError:
                pass
        return order

class BurialsListGenericMixin:
    """
    Здесь фильтр для поиска всех захоронений, которые может видеть лору или угх
    
    В потомках этого класса уточняется, что относительно этого фильтра можно
    править, что видеть в открытых и т.п.
    """

    def get_qs_filter(self):
        qs = Q(pk__isnull=True)
        if self.request.user.is_authenticated:
            if self.request.user.profile.is_loru():
                loru = self.request.user.profile.org
                qs = Q(applicant_organization=loru) | Q(loru=loru) | Q(ugh__loru_list__loru=loru)
                qs = qs & Q(source_type__in=[Burial.SOURCE_FULL, Burial.SOURCE_TRANSFERRED])
            if self.request.user.profile.is_ugh():
                qs |= Q(ugh=self.request.user.profile.org)
        return qs

class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get(self, request, *args, **kwargs):
        if is_cabinet_user(request.user):
            if settings.REDIRECT_LOGIN_TO_FRONT_END:
                return redirect(get_front_end_url(request))
            else:
                return render(
                    request,
                    'simple_message.html',
                    dict(message=_("Рабочее место пользователя кабинета организовано другими средствами"))
                )
        elif request.user.profile.is_ugh():
            if request.user.profile.is_registrator_or_caretaker() and request.user.profile.cemeteries.count():
                return super(DashboardView, self).get(request, *args, **kwargs)
            else:
                return redirect(reverse('burial_list'))
        elif request.user.profile.is_loru():
            return super(DashboardView, self).get(request, *args, **kwargs)
        else:
            raise Http404

    def get_qs_filter(self):
        if self.request.user.profile.is_loru():
          # лору в открытых может видеть только свои (а не других лору) захоронения
            qs = Q(loru=self.request.user.profile.org)
        elif self.request.user.profile.is_ugh():
            qs = Q(cemetery__in=Cemetery.editable_ugh_cemeteries(self.request.user)) | \
                 Q(cemetery__isnull=True, ugh=self.request.user.profile.org)
        return qs

    def get_context_data(self, **kwargs):
        data = super(DashboardView, self).get_context_data(**kwargs)
        qs = self.get_qs_filter()
        ex_qs = Q(status__in=[Burial.STATUS_CLOSED, Burial.STATUS_EXHUMATED])
        if self.request.user.is_authenticated and self.request.user.profile.is_ugh():
            ex_qs |= Q(source_type=Burial.SOURCE_FULL, status=Burial.STATUS_DRAFT)
        ex_qs |= Q(annulated=True)

        sort = self.request.GET.get('sort', '-pk')
        SORT_FIELDS = {
            'pk': 'pk',
            '-pk': '-pk',
            'account_number':  ['account_number_s1', 'account_number_s2', 'account_number_s3'],
            '-account_number':  ['-account_number_s1', '-account_number_s2', '-account_number_s3'],
            'cemetery': 'cemetery__name',
            '-cemetery': '-cemetery__name',
            'place': ['place_number_s1', 'place_number_s2', 'place_number_s3'],
            '-place': ['-place_number_s1', '-place_number_s2', '-place_number_s3'],
            'fio': 'deadman__last_name',
            '-fio': '-deadman__last_name',
            'fact_date': 'plan_date',
            '-fact_date': '-plan_date',
            'plan_date': 'plan_date',
            '-plan_date': '-plan_date',
            'source': 'source_type',
            '-source': '-source_type',
            'applicant': ['applicant__last_name', 'applicant_organization__name'],
            '-applicant': ['-applicant__last_name', '-applicant_organization__name'],
            'status': 'status',
            '-status': '-status',
        }
        s = SORT_FIELDS[sort]
        if not isinstance(s, list):
            s = [s]

        burials_clean = Burial1.objects.filter(qs).exclude(ex_qs).distinct()
        burials_count = burials_clean.count()
        burials = burials_clean.order_by(*s)
        burials.count = lambda: burials_count
        # Оплаченные заказы похорон, у ОМС
        orders = []
        if self.request.user.is_authenticated and self.request.user.profile.is_ugh():
            q_o = Q(
                type=Order.TYPE_FUNERAL,
                loru__ugh_list__ugh=self.request.user.profile.org,
                status=Order.STATUS_PAID,
                burial__isnull=True,
            )
            days_to_stay = self.request.user.profile.org.plan_date_days_before
            if not days_to_stay or days_to_stay <= 0:
                days_to_stay = 3
            date_to = datetime.date.today() - datetime.timedelta(days=days_to_stay)
            q_o &=  Q(dt_due__isnull=True) & Q(dt__gte=date_to) | \
                    Q(dt_due__isnull=False) & Q(dt_due__gte=date_to)
            orders = Order.objects.filter(q_o).order_by('-dt').distinct()
        data.update({
            'burials': burials,
            'orders': orders,
            'sort': sort,
            'editable_ugh_cemeteries': Cemetery.editable_ugh_cemeteries(self.request.user),
        })
        return data

dashboard = DashboardView.as_view()

class ArchiveMixin(BurialsListGenericMixin):
    def get_qs_filter(self):
        qs = Q(pk__isnull=True)
        if self.request.user.is_authenticated:
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
        data['GET_PARAMS'] = '&'.join(['%s=%s' % (k,v) for k,v in list(self.request.GET.items()) if k != 'page'])
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
        self.order = None
        self.order_parm = ''
        if request.user.profile.is_loru():
            b = self.get_object()
            self.order = self.get_order()
            self.order_parm = '?order=%s' % self.order.pk if self.order else ''
            if b and b.pk:
                if b.is_full() and b.loru and b.loru != request.user.profile.org and (b.is_edit() or b.is_ready()):
                    raise Http404
                if self.order and self.order.burial != b:
                    raise Http404
                if b.is_full() and b.is_edit() and not b.annulated:
                    return redirect(reverse('edit_burial', args=[b.pk]) + self.order_parm)
        return super(BurialView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = self.get_qs_filter()
        # Это может вернуть несколько записей
        # одного и того же захоронения, из-за условий поиска
        # Q(loru=loru) | Q(ugh__loru_list__loru=loru),
        # которые могут соответствовать одному захоронению,
        # поэтому distinct()
        burials = Burial.objects.filter(qs).distinct()
        burials = burials.select_related('cemetery', 'place', 'grave', 'applicant_organization', 'ugh', 'deadman', 'deadman__address',)
        return burials

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dashboard')

        b = self.get_object()
        self.b = b
        order = self.order
        order_parm = self.order_parm

        b.changed_by = request.user
        old_status = b.status
        old_annulated = b.annulated
        redirect_to_view = False
        redirect_to_edit = False
        reason = request.POST.get('reason') or request.POST.get('reason_typical')
        if request.POST.get('back') and request.user.profile.is_loru() and b.can_back() and b.loru == request.user.profile.org:
            b.status = Burial.STATUS_BACKED
            b.account_number = ''
            write_log(request, b, _('Захоронение отозвано'), reason)
            messages.success(
                request,
                _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> отозвано") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm, pk=b.pk,
            ))
            redirect_to_edit = True

        if request.POST.get('unbind') and order:
            order.burial = None
            order.save()
            write_log(self.request, b, _('Захоронение откреплено от заказа %s') % order.pk)
            write_log(self.request, order, _('Заказ: откреплено захоронение %s') % b.pk)
            msg = _("<a href='%(order_burial)s'>Заказ %(pk)s</a>: откреплено захоронение") % dict(
                order_burial=reverse('order_burial', args=[order.pk]),
                pk=order.pk,
            )
            messages.success(self.request, msg)

        if request.POST.get('ready') and b.is_edit() and b.is_full():
            return redirect(reverse('edit_burial', args=[b.pk]) + '?action=ready')

        if request.POST.get('inspect') and request.user.profile.is_ugh() and b.can_inspect():
            b, refresh = self.approve_or_check_dc()
            if refresh:
                return redirect(reverse('view_burial', args=[self.b.pk]) + order_parm)
            elif not b:
                return self.get(request, *args, **kwargs)
            else:
                b.status = Burial.STATUS_INSPECTING
                write_log(request, b, _('Захоронение отправлено на обследование'))
                messages.success(
                    request,
                    _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> отправлено на обследование") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))
                redirect_to_view = True

        if request.POST.get('save-dc') and request.user.profile.is_loru() and not b.is_bio() and b.can_approve():
            b, refresh = self.approve_or_check_dc()
            if refresh:
                return redirect(reverse('view_burial', args=[self.b.pk]) + order_parm)
            elif not b:
                return self.get(request, *args, **kwargs)
            else:
                redirect_to_view = True

        if request.POST.get('approve') and request.user.profile.is_ugh() and b.can_approve():
            b, refresh = self.approve_or_check_dc()
            if refresh:
                return redirect(reverse('view_burial', args=[self.b.pk]) + order_parm)
            elif not b:
                return self.get(request, *args, **kwargs)
            else:
                b.status = Burial.STATUS_APPROVED
                b.approve(self.request.user)
                write_log(request, b, _('Захоронение согласовано'))
                messages.success(
                    request,
                    _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> согласовано") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))
                redirect_to_view = True

        if request.POST.get('approve') and request.user.profile.is_ugh() and b.can_approve_ugh():
            approve_close_form = self.get_approve_close_form()
            if approve_close_form.is_valid():
                b = approve_close_form.save()
                return redirect(reverse('edit_burial', args=[b.pk]) + '?action=approve')
            else:
                return self.get(request, *args, **kwargs)

        if request.POST.get('approve-inspect') and request.user.profile.is_ugh() and b.can_approve_inspect():
            b, refresh = self.approve_or_check_dc()
            if refresh:
                return redirect(reverse('view_burial', args=[self.b.pk]) + order_parm)
            elif not b:
                return self.get(request, *args, **kwargs)
            else:
                b.status = Burial.STATUS_READY
                write_log(request, b, _('Обследование одобрено. Захоронение на согласовании'))
                messages.success(
                    request,
                    _("Обследование одобрено. <a href='%(view_burial)s'>Захоронение %(pk)s</a> на согласовании") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))
                redirect_to_view = True
            
        if request.POST.get('decline') and request.user.profile.is_ugh() and b.can_decline():
            if reason and reason.strip():
                b.status = Burial.STATUS_DECLINED
                b.account_number = ''
                msg_declined = 'Захоронение отклонено'
                write_log(request, b, msg_declined, reason)
                messages.success(
                    request,
                    _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> отклонено") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))
            else:
                msg = _("Выполнить операцию не удалось: <a href='%(view_burial)s'>захоронение</a> в статусе \"%(status)s\". "
                        "Не указана причина отказа.") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]),
                    status=b.get_status_display(),
                )
                messages.error(request, msg)
                return redirect(reverse('view_burial', args=[b.pk]))

        if request.POST.get('disapprove') and request.user.profile.is_ugh() and b.can_disapprove_ugh():
            approve_close_form = self.get_approve_close_form()
            if approve_close_form.is_valid():
                b = approve_close_form.save()
                b.status = Burial.STATUS_DRAFT
                b.save()
                write_log(request, b, _('Захоронение возвращено в статус черновика'), reason)
                messages.success(
                    request,
                    _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> возвращено в статус черновика") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))
                redirect_to_view = True
            else:
                return self.get(request, *args, **kwargs)

        if request.POST.get('complete') and request.user.profile.is_ugh() and b.can_finish():
            approve_close_form = self.get_approve_close_form()
            if approve_close_form.is_valid():
                b = approve_close_form.save()
                if b.is_ugh():
                    return redirect(reverse('edit_burial', args=[b.pk]) + '?action=complete')
                else:
                    if b.close(request=request):
                        msg_close = "<a href='%(view_burial)s'>Захоронение %(pk)s</a> закрыто"
                        msg_debitor_to_warn = Debitor.check_debitor_warn(b)
                        if msg_debitor_to_warn:
                            msg_close += '<br />' + msg_debitor_to_warn
                        msg_close = _(msg_close) % dict(
                            view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                        )
                        if msg_debitor_to_warn:
                            messages.warning(request, msg_close)
                        else:
                            messages.success(request, msg_close)
            else:
                return self.get(request, *args, **kwargs)

        if request.POST.get('annulate') and \
            (b.can_ugh_annulate() and \
            (request.user.profile.is_registrator() or \
             request.user.profile.is_caretaker_only() and not b.is_closed() \
            ) \
            or \
            request.user.profile.is_loru() and b.can_loru_annulate()) \
            :
            b.grave = None
            b.annulated = True
            write_log(request, b, _('Захоронение аннулировано'), reason)
            messages.success(
                request,
                _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> аннулировано") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm, pk=b.pk,
            ))
            redirect_to_view = True

        if request.POST.get('deannulate') and \
           (b.can_ugh_deannulate() and \
            (request.user.profile.is_registrator() or \
             request.user.profile.is_caretaker_only() and not b.is_closed() \
            ) \
           or \
           request.user.profile.is_loru() and b.can_loru_deannulate()) \
           :
            if b.place:
                b.grave = b.place.get_or_create_graves(b.grave_number)
            b.annulated = False
            write_log(request, b, _('Захоронение восстановлено после аннулирования'))
            messages.success(
                request,
                _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> восстановлено после аннулирования") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm, pk=b.pk,
            ))
            redirect_to_view = request.user.profile.is_ugh()
            redirect_to_edit = request.user.profile.is_loru()

        if old_status != b.status or old_annulated != b.annulated:
            b.save()
        elif request.POST.get('unbind') and order:
            return redirect(reverse('order_burial', args=[order.pk]))
        elif request.POST.get('save-dc'):
            if not b.can_approve() and request.user.profile.is_loru():
                msg = _("Выполнить операцию не удалось: другой пользователь изменил статус "
                        "<a href='%(view_burial)s'>захоронения</a> на \"%(status)s\"") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm,
                    status=b.get_status_display(),
                )
                messages.error(request, msg)
                redirect_to_edit = b.is_edit()
                redirect_to_view = not redirect_to_edit
        else:
            msg = _("Выполнить операцию не удалось: <a href='%(view_burial)s'>захоронение</a> в статусе \"%(status)s\"") % dict(
                view_burial=reverse('view_burial', args=[b.pk]) + order_parm,
                status=b.get_status_display(),
            )
            messages.error(request, msg)
            
        if redirect_to_view:
            return redirect(reverse('view_burial', args=[b.pk]) + order_parm)
        elif redirect_to_edit:
            return redirect(reverse('edit_burial', args=[b.pk]) + order_parm)
        return redirect('dashboard')

    def approve_or_check_dc(self):
        """
        Одобрить зх или просто подправить СоС
        
        возвращает:
        - burial, захоронение или None, если неверно в форме
        - refresh, надо ли обноновлять страницу при конфликте одновременного
                   редактирования СоС со строноны угх и лору
        """
        burial = None
        refresh = False
        approve_close_form = self.get_approve_close_form()
        if approve_close_form.is_valid():
            dc_form = approve_close_form.dc_form
            if dc_form and dc_form.changed_data:
                timestamp_modified_really = int(DeathCertificate.objects.get(pk=dc_form.instance.pk).\
                                                        dt_modified.strftime("%s"))
                if timestamp_modified_really > dc_form.cleaned_data['dt_modified']:
                    messages.error(
                        self.request,
                        _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> было изменено другим пользователем. "
                          "Страница обновлена") % dict(
                            view_burial=reverse('view_burial', args=[self.b.pk]), pk=self.b.pk,
                    ))
                    refresh = True
                    return burial, refresh
            burial = approve_close_form.save()
            if dc_form and dc_form.changed_data:
                messages.success(
                    self.request,
                    _("<a href='%(view_burial)s'>Захоронение %(pk)s</a>: свидетельство о смерти сохранено") % dict(
                        view_burial=reverse('view_burial', args=[self.b.pk]), pk=self.b.pk,
            ))
        return burial, refresh

    def get_approve_close_form(self):
        return BurialApproveCloseForm(request=self.request, data=self.request.POST or None, instance=self.get_object())

    def get_object(self, queryset=None):
        if not hasattr(self, '_object'):
            self._object = super(BurialView, self).get_object(queryset=queryset)
        return self._object

    def get_spravka_form(self, b):
        form = SpravkaForm()
        if host_country_code(self.request) != 'by':
            del form.fields['spravka0_relative']
        if b.applicant and b.applicant.last_name:
            form.initial['spravka_applicant'] = b.applicant.full_name_complete()
            if b.applicant.address:
                form.initial['spravka_applicant_address'] = "%s" % b.applicant.address
        if self.request.user.profile.title:
            form.initial['spravka_issuer_title'] = self.request.user.profile.title
        if self.request.user.profile.user_last_name:
            form.initial['spravka_issuer'] = self.request.user.profile.last_name_initials()
        return form

    def get_context_data(self, **kwargs):
        data = super(BurialView, self).get_context_data(**kwargs)
        b = self.get_object()
        org = self.request.user.profile.org
        data.update({
            'b': b,
            'reason_typical_back': Reason.objects.filter(org=org, reason_type=Reason.TYPE_BACK),
            'reason_typical_decline': Reason.objects.filter(org=org, reason_type=Reason.TYPE_DECLINE),
            'reason_typical_annulate': Reason.objects.filter(org=org, reason_type=Reason.TYPE_ANNULATE),
            'reason_typical_disapprove': Reason.objects.filter(org=org, reason_type=Reason.TYPE_DISAPPROVE),
            'approve_close_form': self.get_approve_close_form(),
            'spravka_form': self.get_spravka_form(b),
            'comment_form': CommentForm(),
            'zags_form': AddOrgForm(request=self.request, prefix='zags', instance=Org(type=Org.PROFILE_ZAGS)),
            'medic_form': AddOrgForm(request=self.request, prefix='medic', instance=Org(type=Org.PROFILE_MEDIC)),
            'order': self.order,
            'orders': b.get_orders(loru=self.request.user.profile.org) if self.request.user.profile.is_loru() else [],
            # Кому можно смотреть в захоронении ответственного и заявителя:
            'show_private_data': self.request.user.profile.is_ugh() or \
                                 b.is_full() and not b.is_closed() and not b.is_exhumated() and \
                                 b.loru and b.loru == self.request.user.profile.org,
            'can_personal_data': b.can_personal_data(self.request),
            'can_ugh_annulate': b.can_ugh_annulate() and \
                                (self.request.user.profile.is_registrator() or \
                                 self.request.user.profile.is_caretaker_only() and not b.is_closed()),
            'place': b.get_place(),
            'editable_ugh_cemeteries': Cemetery.editable_ugh_cemeteries(self.request.user),
            'ban_close_burial': Debitor.check_debitor_ban_close_burial(self.request),
        })
        return data

view_burial = BurialView.as_view()

class BurialsListView(PaginateListView):
    template_name = 'burial_list.html'
    context_object_name = 'burials'

    def __init__(self, *args, **kwargs):
        super(BurialsListView, self).__init__(*args, **kwargs)
        self.SORT_DEFAULT = '-pk'

    def get_queryset(self):
        if not self.request.GET:
            # Избегаем предупреждения в paginated views:
            #   UnorderedObjectListWarning:
            #   Pagination may yield inconsistent results with an unordered object_list
            #
            return Burial.objects.none().order_by('-pk')

        if self.request.user.is_authenticated:
            if is_ugh_user(self.request.user):
                q_org = Q(ugh=self.request.user.profile.org)
            elif is_loru_user(self.request.user):
                q_org = Q(applicant_organization=self.request.user.profile.org)
            else:
                raise Http404
            burials = Burial1.objects.filter(q_org).order_by('-pk')
        else:
            burials = Burial.objects.none()
        form = self.get_form()
        if form.data and form.is_valid():
            if form.cleaned_data['operation']:
                burials = burials.filter(burial_type=form.cleaned_data['operation'])
            if form.cleaned_data['fio'] and not form.cleaned_data['no_last_name']:
                fio = [re_search(f) for f in form.cleaned_data['fio'].split()]
                q = Q()
                if len(fio) > 2:
                    q &= Q(deadman__middle_name__iregex=fio[2])
                if len(fio) > 1:
                    q &= Q(deadman__first_name__iregex=fio[1])
                if len(fio) > 0:
                    q &= Q(deadman__last_name__iregex=fio[0])
                    burials = burials.filter(q)
            if settings.DEADMAN_IDENT_NUMBER_ALLOW and \
               form.cleaned_data.get('ident_number_search', '').strip() and \
               not form.cleaned_data['no_last_name']:
                burials = burials.filter(deadman__ident_number__icontains=form.cleaned_data['ident_number_search'])
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
                burials = burials.filter(account_number_s2__gte=form.cleaned_data['account_number_from'])
            if form.cleaned_data['account_number_to']:
                burials = burials.filter(account_number_s2__lte=form.cleaned_data['account_number_to'])
            if form.cleaned_data['responsible']:
                fio = [re_search(f) for f in form.cleaned_data['responsible'].split()]
                q1r = Q(responsible__isnull=False)
                q2r = Q(place__isnull=False)
                if len(fio) > 2:
                    q1r &= Q(responsible__middle_name__iregex=fio[2])
                    q2r &= Q(place__responsible__middle_name__iregex=fio[2])
                if len(fio) > 1:
                    q1r &= Q(responsible__first_name__iregex=fio[1])
                    q2r &= Q(place__responsible__first_name__iregex=fio[1])
                if len(fio) > 0:
                    q1r &= Q(responsible__last_name__iregex=fio[0])
                    q2r &= Q(place__responsible__last_name__iregex=fio[0])
                    qr = Q(q1r | q2r)
                    burials = burials.filter(qr)

            if form.cleaned_data.get('cemeteries_editable'):
                burials = burials.filter(cemetery__in=self.request.user.profile.cemeteries.all())
            elif form.cleaned_data.get('cemetery'):
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
                burials = burials.filter(
                    applicant_organization__name__iregex=re_search(form.cleaned_data['applicant_org']))
            if form.cleaned_data.get('loru_in_burials'):
                burials = burials.filter(
                    loru__name__iregex=re_search(form.cleaned_data['loru_in_burials']))
            if form.cleaned_data['applicant_person']:
                fio = [f.strip('.') for f in form.cleaned_data['applicant_person'].split()]
                qa = Q()
                if len(fio) > 2:
                    qa &= Q(applicant__middle_name__iregex=re_search(fio[2]))
                if len(fio) > 1:
                    qa &= Q(applicant__first_name__iregex=re_search(fio[1]))
                if len(fio) > 0:
                    qa &= Q(applicant__last_name__iregex=re_search(fio[0]))
                    burials = burials.filter(qa)

            burial_container = form.cleaned_data['burial_container']
            if burial_container:
                if burial_container == Burial.CONTAINER_URN_IN_GRAVE:
                    q_container = Q(burial_container=Burial.CONTAINER_URN)
                    q_container &= Q(area__kind=Area.KIND_GRAVES)
                    burials = burials.filter(q_container)
                elif burial_container == Burial.CONTAINER_URN_IN_COLUMBARIUM:
                    q_container = Q(burial_container=Burial.CONTAINER_URN)
                    q_container &= ~Q(area__kind=Area.KIND_GRAVES)
                    burials = burials.filter(q_container)
                else:
                    burials = burials.filter(burial_container=burial_container)

            if form.cleaned_data['annulated']:
                burials = burials.filter(annulated=True)
            else:
                burials = burials.filter(annulated=False)

            if form.cleaned_data.get('comment'):
                burials = burials.filter(burial__burialcomment__comment__icontains=form.cleaned_data['comment'])

            if form.cleaned_data.get('file_comment'):
                burials = burials.filter(burial__burialfiles__comment__icontains=form.cleaned_data['file_comment'])

            if form.cleaned_data.get('status') == Burial.STATUS_EXHUMATED:
                burials = burials.filter(status=Burial.STATUS_EXHUMATED)
            # Зачем?!!!
            #else:
                #burials = burials.exclude(status=Burial.STATUS_EXHUMATED)

            if form.cleaned_data.get('is_inbook') is not None:
                is_inbook = form.cleaned_data['is_inbook']
                q_inbook = Q(responsible__is_inbook=is_inbook) | Q(place__responsible__is_inbook=is_inbook)
                burials = burials.filter(q_inbook)
        # Зачем?!!!
        #else:
            #burials = burials.exclude(status=Burial.STATUS_EXHUMATED)

        sort = self.request.GET.get('sort', self.SORT_DEFAULT)
        SORT_FIELDS = {
            'account_number': ['account_number_s1', 'account_number_s2', 'account_number_s3'],
            '-account_number': ['-account_number_s1', '-account_number_s2', '-account_number_s3'],
            'cemetery': 'cemetery__name',
            '-cemetery': '-cemetery__name',
            'place': ['place_number_s1', 'place_number_s2', 'place_number_s3'],
            '-place': ['-place_number_s1', '-place_number_s2', '-place_number_s3'],
            'fio': 'deadman__last_name',
            '-fio': '-deadman__last_name',
            'fact_date': 'fact_date_s',
            '-fact_date': '-fact_date_s',
            'source': 'source_type',
            '-source': '-source_type',
            'applicant': ['applicant__last_name', 'applicant_organization__name'],
            '-applicant': ['-applicant__last_name', '-applicant_organization__name'],
            'status': 'status',
            '-status': '-status',
        }
        try:
            s = SORT_FIELDS[sort]
        except KeyError:
            s = self.SORT_DEFAULT
        if not isinstance(s, list):
            s = [s]

        burials = burials.order_by(*s)
        return burials

    def get_template_names(self):
        if self.request.GET.get('print'):
            return 'burial_list_print.html'
        return super(BurialsListView, self).get_template_names()

    def get_form(self):
        form = BurialSearchForm(data=self.request.GET or None)
        # Птичка "Свои кладбища" нужна только смотрителю, у кого
        # набор своих кладбищ не совпадает с общим набором кладбищ ОМС
        profile = self.request.user.profile
        cemeteries_count = profile.cemeteries.count()
        if profile.is_ugh() and profile.is_registrator_or_caretaker() and \
           cemeteries_count != Cemetery.objects.filter(ugh=profile.org).count() and \
           cemeteries_count > 0:
            pass
        else:
            del form.fields['cemeteries_editable']
        return form

    def get_context_data(self, **kwargs):
        context = super(BurialsListView, self).get_context_data(**kwargs)
        context['editable_ugh_cemeteries'] = Cemetery.editable_ugh_cemeteries(self.request.user)
        return context

burial_list = BurialsListView.as_view()

# Поиск захоронения для ЛОРУ
#
class BurialsPublicListView(PaginateListView):
    template_name = 'burial_public_list.html'
    context_object_name = 'burials'

    def __init__(self, *args, **kwargs):
        super(BurialsPublicListView, self).__init__(*args, **kwargs)
        self.SORT_DEFAULT = '-pk'
        
    def get_queryset(self):
        if not self.request.GET:
            return Burial.objects.none().order_by('-pk')

        if self.request.user.is_authenticated and self.request.user.profile.is_loru():
            burials = Burial1.objects.filter(
                #Q(
                  #(
                   #Q(ugh__loru_list__loru=self.request.user.profile.org) &
                   #Q(annulated=False) &
                   #Q(status__in=[Burial.STATUS_EXHUMATED, Burial.STATUS_CLOSED, Burial.STATUS_APPROVED, ]) &
                   #~Q(burial_container=Burial.CONTAINER_BIO)
                  #)
                  #|
                  #(
                   #Q(annulated=True) &
                   #Q(loru = self.request.user.profile.org) & 
                   #Q(source_type=Burial.SOURCE_FULL) & 
                   #Q(status__in=[Burial.STATUS_BACKED, Burial.STATUS_DRAFT, Burial.STATUS_DECLINED, ])
                  #)
                 #)
                 #).order_by('-pk').distinct()
                  Q(source_type__in=(Burial.SOURCE_FULL, Burial.SOURCE_TRANSFERRED,)) & 
                  Q(loru = self.request.user.profile.org) &
                  (
                    (
                        Q(annulated=False) &
                        Q(status__in=[Burial.STATUS_EXHUMATED, Burial.STATUS_CLOSED, ])
                    )
                    |
                    (
                        Q(annulated=True) &
                        Q(status__in=[Burial.STATUS_BACKED, Burial.STATUS_DRAFT, Burial.STATUS_DECLINED, ])
                    )
                 )
                 ).order_by('-pk').distinct()
        else:
            burials = Burial.objects.none().order_by('-pk')
        form = self.get_form()
        if form.data and form.is_valid():
            if form.cleaned_data['fio']:
                fio = [re_search(f) for f in form.cleaned_data['fio'].split()]
                q = Q()
                if len(fio) > 2:
                    q &= Q(deadman__middle_name__iregex=fio[2])
                if len(fio) > 1:
                    q &= Q(deadman__first_name__iregex=fio[1])
                if len(fio) > 0:
                    q &= Q(deadman__last_name__iregex=fio[0])
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
                burials = burials.filter(account_number_s2__gte=form.cleaned_data['account_number_from'])
            if form.cleaned_data['account_number_to']:
                burials = burials.filter(account_number_s2__lte=form.cleaned_data['account_number_to'])
            if form.cleaned_data['cemetery']:
                burials = burials.filter(cemetery__name=form.cleaned_data['cemetery'])
            if form.cleaned_data['area']:
                burials = burials.filter(area__name=form.cleaned_data['area'])
            if form.cleaned_data['row']:
                burials = burials.filter(row=form.cleaned_data['row'])
            if form.cleaned_data['place']:
                burials = burials.filter(place_number=form.cleaned_data['place'])
            if form.cleaned_data['annulated']:
                burials = burials.filter(annulated=True)
            else:
                burials = burials.filter(annulated=False)

        sort = self.request.GET.get('sort', self.SORT_DEFAULT)
        SORT_FIELDS = {
            'pk': 'pk',
            '-pk': '-pk',
            'account_number':  ['account_number_s1', 'account_number_s2', 'account_number_s3'],
            '-account_number':  ['-account_number_s1', '-account_number_s2', '-account_number_s3'],
            'cemetery': 'cemetery__name',
            '-cemetery': '-cemetery__name',
            'place': ['place_number_s1', 'place_number_s2', 'place_number_s3'],
            '-place': ['-place_number_s1', '-place_number_s2', '-place_number_s3'],
            'fio': 'deadman__last_name',
            '-fio': '-deadman__last_name',
            'fact_date': 'fact_date_s',
            '-fact_date': '-fact_date_s',
            'status': 'status',
            '-status': '-status',
        }
        s = SORT_FIELDS[sort]
        if not isinstance(s, list):
            s = [s]
        burials = burials.order_by(*s)
        return burials

    def get_form(self):
        return BurialPublicListForm(data=self.request.GET or None)

burial_public_list = BurialsPublicListView.as_view()

class CreateBurial(BurialGetOrderMixin, FormInvalidMixin, CreateView):
    template_name = 'create_burial.html'
    form_class = BurialForm

    def get_context_data(self, **kwargs):
        data = super(CreateBurial, self).get_context_data(**kwargs)
        data.update({
            'b': self.get_object(),
            'agent_form': AddAgentForm(prefix='agent'),
            'loru_agent_form': AddAgentForm(prefix='loru_agent'),
            'agent_dover_form': AddDoverForm(prefix='agent_dover'),
            'loru_agent_dover_form': AddDoverForm(prefix='loru_agent_dover'),
            'dover_form': AddDoverForm(prefix='dover'),
            'loru_dover_form': AddDoverForm(prefix='loru_dover'),
            'org_form': AddOrgForm(request=self.request, prefix='org'),
            'loru_form': AddOrgForm(request=self.request, prefix='loru', instance=Org(type=Org.PROFILE_LORU)),
            'zags_form': AddOrgForm(request=self.request, prefix='zags', instance=Org(type=Org.PROFILE_ZAGS)),
            'medic_form': AddOrgForm(request=self.request, prefix='medic', instance=Org(type=Org.PROFILE_MEDIC)),
            'doc_type_form': AddDocTypeForm(prefix='doctype'),
            'add_graves_form': AddGravesForm(prefix='add_graves'),
            'order': self.get_order(),
            'ban_close_burial': Debitor.check_debitor_ban_close_burial(self.request),
        })
        return data

    def get_object(self, *args, **kwargs):
        return None

    def get_form_kwargs(self, *args, **kwargs):
        data = super(CreateBurial, self).get_form_kwargs(*args, **kwargs)
        place_id = self.request.GET.get('place_id')
        if place_id and not data.get('instance'):
            try:
                place = Place.objects.get(pk=place_id)
                grave_number_max = place.get_graves_count()
                grave_number = 1
                if self.request.GET.get('grave_number') and \
                   not place.area.is_columbarium():
                    try:
                        grave_number = int(self.request.GET.get('grave_number'))
                    except ValueError:
                        pass
                elif self.request.GET.get('burial_add'):
                    grave_number = grave_number_max or 1

                burial_type = Burial._meta.get_field('burial_type').default
                burial_container = Burial._meta.get_field('burial_container').default
                if place.is_columbarium():
                    burial_container = Burial.CONTAINER_URN
                if self.request.GET.get('burial_add'):
                    if place.is_columbarium():
                        burial_type = Burial.BURIAL_OVER
                    else:
                        burial_type = Burial.BURIAL_ADD
                responsible = place.responsible and place.responsible.deep_copy() or None
                data['instance'] = Burial(
                    burial_type=burial_type,
                    burial_container=burial_container,
                    cemetery=place.cemetery,
                    area=place.area,
                    row=place.row,
                    place_number=place.place,
                    responsible=responsible,
                    grave_number=grave_number,
                )
            except Place.DoesNotExist:
                pass
        order = self.get_funeral_order()
        if order and not data.get('instance'):
            try:
                orderplace = OrderPlace.objects.get(order=order)
                row = orderplace.row
                place_number = orderplace.place
            except OrderPlace.DoesNotExist:
                row = ''
                place_number = ''
            try:
                orderdeadperson = OrderDeadPerson.objects.get(order=order)
                deadman = DeadPerson(
                    last_name=orderdeadperson.last_name,
                    first_name=orderdeadperson.first_name,
                    middle_name=orderdeadperson.middle_name,
                    birth_date=orderdeadperson.birth_date,
                    death_date=orderdeadperson.death_date,
                )
            except OrderDeadPerson.DoesNotExist:
                deadman = None
            applicant = responsible = None
            if order.applicant:
                applicant = AlivePerson(
                    last_name=order.applicant.last_name,
                    first_name=order.applicant.first_name,
                    middle_name=order.applicant.middle_name,
                )
                responsible = AlivePerson(
                    last_name=order.applicant.last_name,
                    first_name=order.applicant.first_name,
                    middle_name=order.applicant.middle_name,
                    login_phone=order.applicant.phones,
                )
            data['instance'] = Burial(
                deadman=deadman,
                applicant=applicant,
                responsible=responsible,
                row=row,
                place_number=place_number,
                grave_number=1,
                plan_date=order.dt_due,
            )
        data['request'] = self.request
        return data

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

        if self.request.user.profile.is_loru():
            order = self.get_order()
            if order and order.burial and order.burial != self.get_object():
                return redirect(reverse('edit_burial', args=[order.burial.pk]) + '?order=%s' % order.pk)
        elif self.request.user.profile.is_ugh() and \
             self.request.user.profile.is_registrator_or_caretaker() and \
             self.request.user.profile.cemeteries.count():
            pass
        else:
            messages.error(request, _("У Вас нет прав создавать захоронения. Обратитесь к администратору"))
            return redirect('/')

        return super(CreateBurial, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        old_responsible_info = form.old_responsible_info
        is_existing_burial = form.instance and form.instance.pk or None
        b = form.save()

        order = None
        order_parm = ''
        if self.request.user.profile.is_loru():
            order = self.get_order()
            order_parm = '?order=%s' % order.pk if order else ''

        action = self.get_action()
        if action:
            redirect_to_view = False
            old_status = b.status
            old_annulated = b.annulated

            if action == 'unbind' and b.is_edit() and b.is_full() and order:
                order.burial = None
                order.save()
                write_log(self.request, b, _('Захоронение откреплено от заказа %s') % order.pk)
                write_log(self.request, order, _('Заказ: откреплено захоронение %s') % b.pk)
                msg = _("<a href='%(order_burial)s'>Заказ %(pk)s</a>: откреплено захоронение") % dict(
                    order_burial=reverse('order_burial', args=[order.pk]),
                    pk=order.pk,
                )
                messages.success(self.request, msg)

            if action == 'ready' and self.request.user.profile.is_loru() and b.is_edit() and b.is_full():
                b.status = Burial.STATUS_READY
                write_log(self.request, b, _('Захоронение отправлено на согласование'))
                msg = _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> отправлено на согласование") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm, pk=b.pk,
                )
                messages.success(self.request, msg)

            if action == 'annulate' and \
                 (self.request.user.profile.is_loru() and b.can_loru_annulate() or \
                  self.request.user.profile.is_ugh() and b.can_ugh_annulate()
                 )  :
                b.grave = None
                b.annulated = True
                write_log(self.request, b, _('Захоронение аннулировано'))
                msg = _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> аннулировано") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm, pk=b.pk,
                )
                messages.success(self.request, msg)
                redirect_to_view = True

            if action == 'deannulate' and \
                (self.request.user.profile.is_ugh() and b.can_ugh_deannulate() or \
                self.request.user.profile.is_loru() and b.can_loru_deannulate()
                ):
                if b.place:
                    b.grave = b.place.get_or_create_graves(b.grave_number)
                b.annulated = False
                write_log(self.request, b, _('Захоронение восстановлено после аннулирования'))
                messages.success(
                    self.request,
                    _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> восстановлено после аннулирования") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]) + order_parm, pk=b.pk,
                ))
                redirect_to_view = self.request.user.profile.is_ugh()
                redirect_to_edit = self.request.user.profile.is_loru()

            if action == 'approve' and self.request.user.profile.is_ugh() and b.can_approve_ugh():
                b.status = Burial.STATUS_APPROVED
                b.approve(self.request.user)
                write_log(self.request, b, _('Захоронение согласовано'))
                messages.success(
                    self.request,
                    _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> согласовано") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))

            if action == 'disapprove' and self.request.user.profile.is_ugh() and b.can_disapprove_ugh():
                b.status = Burial.STATUS_DRAFT
                write_log(self.request, b, _('Захоронение возвращено в статус черновика'))
                messages.success(
                    self.request,
                    _("<a href='%(view_burial)s'>Захоронение %(pk)s</a> возвращено в статус черновика") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))

            if action == 'complete' and self.request.user.profile.is_ugh() and b.can_finish() and b.is_ugh():
                b.changed_by = self.request.user
                if b.close(request=self.request):
                    if form.responsible_form.cleaned_data.get('take_from') != form.responsible_form.WHERE_FROM_PLACE:
                        form.compare_responsible_info(
                            request=self.request,
                            old_responsible_info=old_responsible_info,
                            burial=b,
                            is_new_burial=not is_existing_burial,
                        )
                    msg_debitor_to_warn = Debitor.check_debitor_warn(b)
                    msg_close = "<a href='%(view_burial)s'>Захоронение %(pk)s</a> закрыто"
                    if msg_debitor_to_warn:
                        msg_close += '<br />' + msg_debitor_to_warn
                    msg_close = _(msg_close) % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                    )
                    if msg_debitor_to_warn:
                        messages.warning(self.request, msg_close)
                    else:
                        messages.success(self.request, msg_close)
                    redirect_to_view = True

            if old_status != b.status or old_annulated != b.annulated:
                b.save()
            elif action != 'unbind':
                msg = _("Выполнить операцию не удалось: "
                        "<a href='%(view_burial)s'>захоронение</a> в статусе \"%(status)s\"") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm,
                    status=b.get_status_display(),
                )
                messages.success(self.request, msg)
                return redirect('dashboard')

            if self.request.user.profile.is_loru():
                if action == 'unbind' and order:
                    return redirect(reverse('order_burial', args=[order.pk]))
                else:
                    self.request.session['order_burial_saved'] = True
                    if b.is_edit() and not b.annulated:
                        return redirect(reverse('edit_burial', args=[b.pk]) + order_parm)
                    else:
                        redirect_to_view = True

            if redirect_to_view and b.pk:
                return redirect(reverse('view_burial', args=[b.pk]) + order_parm)
            else:
                return redirect('dashboard')
        else:
            if self.request.user.profile.is_loru():
                self.request.session['order_burial_saved'] = True
                if b.is_edit():
                    return redirect(reverse('edit_burial', args=[b.pk]) + order_parm)
                else:
                    return redirect(reverse('view_burial', args=[b.pk]) + order_parm)
            return redirect(reverse('view_burial', args=[b.pk]) + order_parm)

    def get_action(self):
        action = self.request.GET.get('action')
        if self.request.POST.get('approve'):
            action = 'approve'
        if self.request.POST.get('disapprove'):
            action = 'disapprove'
        if self.request.POST.get('ready'):
            action = 'ready'
        if self.request.POST.get('complete'):
            action = 'complete'
        if self.request.POST.get('annulate'):
            action = 'annulate'
        if self.request.POST.get('deannulate'):
            action = 'deannulate'
        if self.request.POST.get('unbind'):
            action = 'unbind'
        return action

    def get_form_class(self):
        action =  self.get_action()
        if action in ('annulate', 'deannulate', 'unbind', 'disapprove',):
            return BurialForm
        if action in ('complete', 'approve', 'ready',):
            return BurialCommitForm
        burial = self.get_object()
        if burial and burial.is_finished() and self.request.user.profile.is_ugh() and not burial.annulated:
            return BurialCommitForm
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
        b = self.get_object()
        if request.user.profile.is_loru():
            if b and b.pk:
                if b.is_full() and b.loru and b.loru != request.user.profile.org:
                    raise Http404
                order = self.get_order()
                if order and order.burial != b:
                    raise Http404
                order_parm = '?order=%s' % order.pk if order else ''
                if b.is_full() and b.is_edit() and not b.annulated:
                    return super(EditBurialView, self).dispatch(request, *args, **kwargs)
                return redirect(reverse('view_burial', args=[b.pk]) + order_parm)
        elif request.user.profile.is_ugh():
            if not b.cemetery or b.cemetery in Cemetery.editable_ugh_cemeteries(request.user):
                if b.is_closed() and request.user.profile.is_caretaker_only():
                    raise PermissionDenied
            else:
                raise PermissionDenied
        else:
            raise PermissionDenied
        return super(EditBurialView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        q = self.get_qs_filter()

        if self.request.user.profile.is_loru():
            # ... это проверяется в self.dispatch():
            # q3 = Q(status__in=[Burial.STATUS_DRAFT, Burial.STATUS_DECLINED, Burial.STATUS_BACKED], annulated=False)
            # ... это учтено в self.get_qs_filter():
            # q3 |= Q(source_type__in=[Burial.SOURCE_TRANSFERRED])
            q2 = q # & q3
        elif self.request.user.profile.is_ugh():
            q3 = Q(source_type__in=[Burial.SOURCE_UGH, Burial.SOURCE_ARCHIVE, Burial.SOURCE_TRANSFERRED])
            q3 |= Q(status__in=[Burial.STATUS_CLOSED, ])
            q2 = q & q3
        else:
            return Burial.objects.none()

        # self.get_qs_filter() может вернуть несколько записей
        # одного и того же захоронения, из-за условий поиска
        # Q(loru=loru) | Q(ugh__loru_list__loru=loru),
        # которые могут соответствовать одному захоронению,
        # поэтому distinct()
        return Burial.objects.filter(q2).distinct()

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
        context['user'] = self.request.user
        template = 'reports/notification.html'
        if self.request.user.profile.is_ugh():
            report = make_report(
                user=self.request.user,
                msg=_("Уведомление"),
                obj=self.get_object(),
                template=template,
                context=context,
            )
        return render(self.request, template, context)

make_notification = MakeNotificationView.as_view()

class MakeExhumateReport(BurialsListGenericMixin, DetailView):
    context_object_name = 'burial'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return Burial.objects.filter(qs).distinct()

    def render_to_response(self, context, **response_kwargs):
        context['user'] = self.request.user
        template = 'simple_message.html'
        if self.request.user.is_authenticated and self.request.user.profile.is_ugh():
            if self.get_object().exhumated:
                template = 'reports/exhumate.html'
            else:
                context['message'] = _("Захоронение не эксгумировано")
        else:
            context['message'] = _("Нет доступа")
        return render(self.request, template, context)

make_exhumate_report = MakeExhumateReport.as_view()

class MakeExhumateNotification(BurialsListGenericMixin, DetailView):
    context_object_name = 'burial'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return Burial.objects.filter(qs).distinct()

    def render_to_response(self, context, **response_kwargs):
        context['user'] = self.request.user
        template = 'simple_message.html'
        if self.request.user.is_authenticated and self.request.user.profile.is_ugh():
            if self.get_object().exhumated:
                template = 'reports/exhumate_notification.html'
            else:
                context['message'] = _("Захоронение не эксгумировано")
        else:
            context['message'] = _("Нет доступа")
        return render(self.request, template, context)

make_exhumate_notification = MakeExhumateNotification.as_view()

class MakeSpravka(BurialsListGenericMixin, DetailView):
    context_object_name = 'burial'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return Burial.objects.filter(qs).distinct()

    def render_to_response(self, context, **response_kwargs):
        for cc in (
            'spravka_applicant',
            'spravka_applicant_address',
            'spravka_issuer_title',
            'spravka_issuer',
            ):
            context[cc] = self.request.GET.get(cc, '')
        context['spravka_relative'] = bool(self.request.GET.get('spravka0_relative', ''))
        context['now'] = datetime.datetime.now()
        template = 'spravka_minsk.html' if host_country_code(self.request) == 'by' else 'spravka.html'
        template = "reports/%s" % template
        context['print_now'] = True
        context['user'] = self.request.user
        report = make_report(
            user=self.request.user,
            msg=_("Справка"),
            obj=self.get_object(),
            template=template,
            context=context,
        )
        return redirect('report_view', report.pk)

make_spravka = MakeSpravka.as_view()

class GetCemeteryTimes(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _("Доступно только для пользователей"))
            return redirect('/')
        try:
            c = Cemetery.objects.get(pk=request.GET.get('cem'))
        except (ValueError, Cemetery.DoesNotExist, ):
            return HttpResponse(json.dumps({}), content_type='application/json')
        try:
            date = datetime.datetime.strptime(request.GET.get('date'), '%d.%m.%Y').date()
        except ValueError:
            # Есть таки возможность пользователю ввести плановую дату типа 30 февраля:
            return HttpResponse(json.dumps({c.pk: []}), content_type='application/json')
        data = c.get_time_choices(date=date, request=request)
        return HttpResponse(json.dumps({c.pk: data}), content_type='application/json')

cemetery_times = GetCemeteryTimes.as_view()

class GetCemeteryPersonalData(View):
    def get(self, request, *args, **kwargs):
        pk=request.GET.get('cem')
        if not request.user.is_authenticated or pk is None:
            return redirect('/')
        result = False
        if pk:
            try:
                c = Cemetery.objects.get(pk=pk)
                result = c.ugh and c.ugh.can_personal_data()
            except (ValueError, AttributeError, Cemetery.DoesNotExist,):
                pass
        else:
            try:
                result = request.user.profile.org.can_personal_data()
            except (AttributeError, Profile.DoesNotExist,):
                pass
        return HttpResponse(json.dumps({'result': result}), content_type='application/json')

cemetery_personal_data = GetCemeteryPersonalData.as_view()

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
        data.update({
            'agent_form': AddAgentForm(prefix='agent'),
            'agent_dover_form': AddDoverForm(prefix='agent_dover'),
            'dover_form': AddDoverForm(prefix='dover'),
            'org_form': AddOrgForm(request=self.request, prefix='org'),
        })
        return data

    def post(self, request, *args, **kwargs):
        self.request = request
        f = self.get_form()
        if f.is_valid():
            ex = f.save()
            write_log(self.request, self.get_object(), _('Захоронение эксгумировано'))
            messages.success(request, _("Эксгумация успешна"))
            if ex.place:
                return redirect(ex.place.url())
            else:
                return redirect('view_burial', ex.burial.pk)
        else:
            messages.error(request, _("Обнаружены ошибки"))
            return self.get(request, *args, **kwargs)

burial_exhumate = ExhumateView.as_view()

class CancelExhumationView(ArchiveMixin, DeleteView):
    def get_success_url(self):
        burial = self.get_object().burial
        place = self.get_object().place or burial.get_place()
        write_log(self.request, burial, _('Эксгумация отменена'))
        messages.success(self.request, _("Эксгумация отменена"))
        if place and place.pk:
            return place.url()
        else:
            return reverse('dashboard')

    def get_queryset(self):
        qs = Q(burial__ugh=self.request.user.profile.org) | Q(burial__cemetery__ugh=self.request.user.profile.org)
        return ExhumationRequest.objects.filter(qs).distinct()

burial_cancel_exhumation = CancelExhumationView.as_view()

class RegistryView(FormInvalidMixin, ManualEncodedCsvMixin, UpdateView):

    DATE_FORMAT='%d.%m.%Y'

    template_name = 'registry.html'
    model = Profile
    form_class = RegistryForm

    def get_object(self):
        if not settings.DEADMAN_IDENT_NUMBER_ALLOW or not is_ugh_user(self.request.user):
            raise Http404
        if not self.request.user.profile.is_registry_handler():
            raise PermissionDenied
        return self.request.user.profile

    def get_form(self, *args, **kwargs):
        form = super(RegistryView, self).get_form(*args, **kwargs)
        cemeteries_qs = Cemetery.objects.filter(ugh=self.request.user.profile.org)
        form.fields['cemeteries'].queryset = cemeteries_qs
        form.fields['cemeteries'].widget.attrs.update({'size': str(min(cemeteries_qs.count()+1, 15))})
        cc = list()
        for c in cemeteries_qs:
            cc.append(c.pk)
        form.initial['cemeteries'] = cc
        form.initial['date_from'] = datetime.date.today()
        form.initial['date_to'] = form.initial['date_from']
        return form

    def check_empty_file(self, temp_dir, fname):
        """
        Пустой экспорт удалить. Возвращает True если экспорт не пустой
        """
        fpath = os.path.join(temp_dir, fname)
        result = False
        try:
            if os.path.getsize(fpath) > 0:
                result = True
            else:
                os.unlink(fpath)
        except OSError:
            pass
        return result

    def check_names(self, deadman):
        """
        Убрать из фио ';'. Пустое отчество -> '-'
        """
        result = None
        last_name = first_name = middle_name = ''
        if deadman:
            last_name = self.correct_field(deadman.last_name)
            if last_name == self.EMPTY_FIELD:
                last_name = ''
            first_name = self.correct_field(deadman.first_name)
            if first_name == self.EMPTY_FIELD:
                first_name = ''
            middle_name = self.correct_field(deadman.middle_name)
            if not middle_name:
                middle_name = self.EMPTY_FIELD
        if last_name and first_name:
            result = (last_name, first_name, middle_name)
        return result

    def form_valid(self, form):

        org = self.request.user.profile.org
        org_pk = org.pk
        media_path = os.path.join('tmp', 'export', 'burials',
            '%s' % org_pk,
        )
        export_path = os.path.join(settings.MEDIA_ROOT, media_path)
        try:
            os.makedirs(export_path)
        except OSError:
            pass
        temp_dir = tempfile.mkdtemp(dir=export_path)
        temp_dir_name = os.path.basename(temp_dir)
        d = datetime.datetime.now()
        dt_now_str = datetime.datetime.strftime(d, '%Y%m%d%H%M%S')
        date_from = form.cleaned_data['date_from']
        date_from_str = datetime.datetime.strftime(date_from, '%Y%m%d')
        date_to = form.cleaned_data['date_to']
        date_to_str = datetime.datetime.strftime(date_to, '%Y%m%d')
        date_to_1 = date_to + datetime.timedelta(days=1)

        selected_cemeteries = list()
        columbariums_list = list()
        for c in form.cleaned_data['cemeteries']:
            if c.ugh != org:
                raise Http404
            selected_cemeteries.append(c)
        if len(selected_cemeteries) == Cemetery.objects.filter(ugh=org).count():
            q_selected_cemeteries = Q(cemetery__ugh=org)
        else:
            q_selected_cemeteries = Q(cemetery__in=selected_cemeteries)

        q_dates = q_selected_cemeteries & Q(
            annulated=False,
            fact_date__isnull=False,
            fact_date_no_day=False,
            fact_date_no_month=False,
            status= Burial.STATUS_CLOSED,
            ugh=org,
            dt_register__gte=date_from,
            dt_register__lt=date_to_1,
            deadman__last_name__gt='',
            deadman__first_name__gt='',
            deadman__ident_number__gt='',
        )
        q_dates &= ~Q(place_number='-')

        select_related = ('area', 'deadman',)

        # Список файлов для архивации
        #
        got_data = list()

        q_graves =  q_dates & \
                        Q(area__kind=Area.KIND_GRAVES) & \
                        Q(place__kind_crypt=False) & \
                        Q(row__gt='') & \
                        ~Q(row='-')

        # Кладбищенские участки, гробы
        #
        q_graves_coffins =  q_graves & Q(burial_container=Burial.CONTAINER_COFFIN)

        qs = Burial.objects.filter(q_graves_coffins).order_by('dt_register'). \
                select_related(*select_related).distinct()
        fname = 'registry-1-from-%s-to-%s-at-%s.csv' % (date_from_str, date_to_str, dt_now_str, )
        with open(os.path.join(temp_dir, fname), 'wb') as f:
            for b in qs.iterator(chunk_size=100):
                full_name = self.check_names(b.deadman)
                if not full_name:
                    pass
                f.write(self.encode_(self.SEPARATOR.join((
                    "1",
                    b.deadman.ident_number,
                    full_name[0], full_name[1], full_name[2],
                    datetime.datetime.strftime(b.fact_date.d, self.DATE_FORMAT),
                    b.cemetery.code,
                    b.area.name,
                    b.row,
                    b.place_number,
                    str(b.grave_number),
                ))))
        if self.check_empty_file(temp_dir, fname):
            got_data.append(fname)

        # Кладбищенские участки, урны
        #
        q_graves_urns =  q_graves & Q(burial_container=Burial.CONTAINER_URN)

        qs = Burial.objects.filter(q_graves_urns).order_by('dt_register'). \
                select_related(*select_related).distinct()
        fname = 'registry-5-from-%s-to-%s-at-%s.csv' % (date_from_str, date_to_str, dt_now_str, )
        with open(os.path.join(temp_dir, fname), 'wb') as f:
            for b in qs.iterator(chunk_size=100):
                full_name = self.check_names(b.deadman)
                if not full_name:
                    pass
                f.write(self.encode_(self.SEPARATOR.join((
                    "5",
                    b.deadman.ident_number,
                    full_name[0], full_name[1], full_name[2],
                    datetime.datetime.strftime(b.fact_date.d, self.DATE_FORMAT),
                    b.cemetery.code,
                    b.area.name,
                    b.row,
                    b.place_number,
                    str(b.grave_number),
                ))))
        if self.check_empty_file(temp_dir, fname):
            got_data.append(fname)

        # Колумбарные стены
        #
        q_vertical_columbariums = q_dates & \
                                    Q(area__kind=Area.KIND_COLUMBARIUM_VERT) & \
                                    Q(place__kind_crypt=False)
        qs = Burial.objects.filter(q_vertical_columbariums).order_by('dt_register'). \
                select_related(*select_related).distinct()
        fname = 'registry-2-from-%s-to-%s-at-%s.csv' % (date_from_str, date_to_str, dt_now_str, )
        with open(os.path.join(temp_dir, fname), 'wb') as f:
            for b in qs.iterator(chunk_size=100):
                full_name = self.check_names(b.deadman)
                if not full_name:
                    pass
                f.write(self.encode_(self.SEPARATOR.join((
                    "2",
                    b.deadman.ident_number,
                    full_name[0], full_name[1], full_name[2],
                    datetime.datetime.strftime(b.fact_date.d, self.DATE_FORMAT),
                    b.cemetery.code,
                    b.area.name,
                    b.row or '-',
                    b.place_number,
                ))))
        if self.check_empty_file(temp_dir, fname):
            got_data.append(fname)

        # Горизонтальные колумбарии
        #
        q_horizontal_columbariums =  q_dates & \
                        Q(area__kind=Area.KIND_COLUMBARIUM_HORZ) & \
                        Q(place__kind_crypt=False) & \
                        Q(row__gt='') & \
                        ~Q(row='-')
        qs = Burial.objects.filter(q_horizontal_columbariums).order_by('dt_register'). \
                select_related(*select_related).distinct()
        fname = 'registry-3-from-%s-to-%s-at-%s.csv' % (date_from_str, date_to_str, dt_now_str, )
        with open(os.path.join(temp_dir, fname), 'wb') as f:
            for b in qs.iterator(chunk_size=100):
                full_name = self.check_names(b.deadman)
                if not full_name:
                    pass
                f.write(self.encode_(self.SEPARATOR.join((
                    "3",
                    b.deadman.ident_number,
                    full_name[0], full_name[1], full_name[2],
                    datetime.datetime.strftime(b.fact_date.d, self.DATE_FORMAT),
                    b.cemetery.code,
                    b.area.name,
                    b.row,
                    b.place_number,
                ))))
        if self.check_empty_file(temp_dir, fname):
            got_data.append(fname)

        # Склепы
        #
        q_crypts =  q_dates & \
                        Q(area__kind=Area.KIND_GRAVES) & \
                        Q(place__kind_crypt=True)
        qs = Burial.objects.filter(q_crypts).order_by('dt_register'). \
                select_related(*select_related).distinct()
        fname = 'registry-4-from-%s-to-%s-at-%s.csv' % (date_from_str, date_to_str, dt_now_str, )
        with open(os.path.join(temp_dir, fname), 'wb') as f:
            for b in qs.iterator(chunk_size=100):
                full_name = self.check_names(b.deadman)
                if not full_name:
                    pass
                f.write(self.encode_(self.SEPARATOR.join((
                    "4",
                    b.deadman.ident_number,
                    full_name[0], full_name[1], full_name[2],
                    datetime.datetime.strftime(b.fact_date.d, self.DATE_FORMAT),
                    b.cemetery.code,
                    b.place_number,
                ))))
        if self.check_empty_file(temp_dir, fname):
            got_data.append(fname)

        if got_data:
            zip_fname = 'registry-from-%s-to-%s-at-%s.zip' % (date_from_str, date_to_str, dt_now_str, )
            with zipfile.ZipFile(os.path.join(temp_dir, zip_fname), 'w') as f:
                for fname in got_data:
                    f.write(os.path.join(temp_dir, fname), fname)
            for fname in got_data:
                os.unlink(os.path.join(temp_dir, fname))
            return redirect(os.path.join(settings.MEDIA_URL, media_path, temp_dir_name, zip_fname))
        else:
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass
            messages.info(self.request, _('Не найдены данные для реестра за указанный интервал дат'))
            return self.get(self.request, *self.args, **self.kwargs)

burials_registry = RegistryView.as_view()

