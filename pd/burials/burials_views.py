# coding=utf-8
import datetime
import json
from django import db

from django.conf import settings
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

from burials.forms import BurialSearchForm, BurialPublicListForm, BurialForm, BurialCommitForm, BurialApproveCloseForm, AddDocTypeForm
from burials.forms import AddAgentForm, AddDoverForm, AddOrgForm, ExhumationForm
from burials.models import Reason, Burial, Burial1, Cemetery, Place, ExhumationRequest
from persons.models import DeathCertificate
from logs.models import write_log
from orders.models import Order
from users.models import Org, Profile, is_cabinet_user
from pd.utils import re_search
from pd.forms import CommentForm
from pd.views import PaginateListView, FormInvalidMixin, get_front_end_url
from reports.models import make_report

class BurialGetOrderMixin:
    """
    Правка, просмотр захоронений пользователем-ЛОРУ производится
    по URL с параметром <order=<номер заказа>. Здесь:
    получение объекта заказа, соответствующего этому номеру.
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
    """
    Здесь фильтр для поиска всех захоронений, которые может видеть лору или угх
    
    В потомках этого класса уточняется, что относительно этого фильтра можно
    править, что видеть в открытых и т.п.
    """

    def get_qs_filter(self):
        qs = Q(pk__isnull=True)
        if self.request.user.is_authenticated():
            if self.request.user.profile.is_loru():
                loru = self.request.user.profile.org
                qs = Q(applicant_organization=loru) | Q(loru=loru) | Q(ugh__loru_list__loru=loru)
                qs = qs & Q(source_type__in=[Burial.SOURCE_FULL, Burial.SOURCE_TRANSFERRED])
            if self.request.user.profile.is_ugh():
                qs |= Q(ugh=self.request.user.profile.org)
        return qs

class DashboardView(BurialsListGenericMixin, TemplateView):
    template_name = 'dashboard.html'

    def get(self, request, *args, **kwargs):
        if is_cabinet_user(request.user):
            if settings.REDIRECT_LOGIN_TO_FRONT_END:
                return redirect(get_front_end_url(request))
            else:
                return render_to_response(
                    'simple_message.html',
                    dict(message=_(u"Рабочее место пользователя кабинета организовано другими средствами"))
                )
        return super(DashboardView, self).get(request, *args, **kwargs)

    def get_qs_filter(self):
      if self.request.user.is_authenticated() and self.request.user.profile.is_loru():
          # лору в открытых может видеть только свои (а не других лору) захоронения
          qs = Q(loru=self.request.user.profile.org)
      else:
        qs = super(DashboardView, self).get_qs_filter()
      return qs

    def get_context_data(self, **kwargs):
        qs = self.get_qs_filter()
        ex_qs = Q(status__in=[Burial.STATUS_CLOSED, Burial.STATUS_EXHUMATED])
        if self.request.user.is_authenticated() and self.request.user.profile.is_ugh():
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
            'fact_date': 'fact_date',
            '-fact_date': '-fact_date',
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
        if not request.user.is_authenticated():
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
            b.account_number = None
            write_log(request, b, _(u'Захоронение отозвано'), reason)
            messages.success(
                request,
                _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> отозвано") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm, pk=b.pk,
            ))
            redirect_to_edit = True

        if request.POST.get('unbind') and order:
            order.burial = None
            order.save()
            write_log(self.request, b, _(u'Захоронение откреплено от заказа %s') % order.pk)
            write_log(self.request, order, _(u'Заказ: откреплено захоронение %s') % b.pk)
            msg = _(u"<a href='%(order_burial)s'>Заказ %(pk)s</a>: откреплено захоронение") % dict(
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
                write_log(request, b, _(u'Захоронение отправлено на обследование'))
                messages.success(
                    request,
                    _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> отправлено на обследование") % dict(
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
                write_log(request, b, _(u'Захоронение согласовано'))
                messages.success(
                    request,
                    _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> согласовано") % dict(
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
                write_log(request, b, _(u'Обследование одобрено. Захоронение на согласовании'))
                messages.success(
                    request,
                    _(u"Обследование одобрено. <a href='%(view_burial)s'>Захоронение %(pk)s</a> на согласовании") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))
                redirect_to_view = True
            
        if request.POST.get('decline') and request.user.profile.is_ugh() and b.can_decline():
            if reason and reason.strip():
                b.status = Burial.STATUS_DECLINED
                b.account_number = None
                msg_declined = u'Захоронение отклонено'
                write_log(request, b, msg_declined, reason)
                messages.success(
                    request,
                    _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> отклонено") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))
            else:
                msg = _(u"Выполнить операцию не удалось: <a href='%(view_burial)s'>захоронение</a> в статусе \"%(status)s\". "
                        u"Не указана причина отказа.") % dict(
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
                write_log(request, b, _(u'Захоронение возвращено в статус черновика'), reason)
                messages.success(
                    request,
                    _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> возвращено в статус черновика") % dict(
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
                    b.close(request=request)
                    messages.success(
                        request,
                        _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> закрыто") % dict(
                            view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                    ))
            else:
                return self.get(request, *args, **kwargs)

        if request.POST.get('annulate') and \
            (request.user.profile.is_ugh() and b.can_ugh_annulate() or \
             request.user.profile.is_loru() and b.can_loru_annulate() \
            ):
            b.grave = None
            b.annulated = True
            write_log(request, b, _(u'Захоронение аннулировано'), reason)
            messages.success(
                request,
                _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> аннулировано") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm, pk=b.pk,
            ))
            redirect_to_view = True

        if request.POST.get('deannulate') and \
           (request.user.profile.is_ugh() and b.can_ugh_deannulate() or \
            request.user.profile.is_loru() and b.can_loru_deannulate()
           ):
            if b.place:
                b.grave = b.place.get_or_create_graves(b.grave_number)
            b.annulated = False
            write_log(request, b, _(u'Захоронение восстановлено после аннулирования'))
            messages.success(
                request,
                _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> восстановлено после аннулирования") % dict(
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
                msg = _(u"Выполнить операцию не удалось: другой пользователь изменил статус "
                        u"<a href='%(view_burial)s'>захоронения</a> на \"%(status)s\"") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm,
                    status=b.get_status_display(),
                )
                messages.error(request, msg)
                redirect_to_edit = b.is_edit()
                redirect_to_view = not redirect_to_edit
        else:
            msg = _(u"Выполнить операцию не удалось: <a href='%(view_burial)s'>захоронение</a> в статусе \"%(status)s\"") % dict(
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
                        _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> было изменено другим пользователем. "
                          u"Страница обновлена") % dict(
                            view_burial=reverse('view_burial', args=[self.b.pk]), pk=self.b.pk,
                    ))
                    refresh = True
                    return burial, refresh
            burial = approve_close_form.save()
            if dc_form and dc_form.changed_data:
                messages.success(
                    self.request,
                    _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a>: свидетельство о смерти сохранено") % dict(
                        view_burial=reverse('view_burial', args=[self.b.pk]), pk=self.b.pk,
            ))
        return burial, refresh

    def get_approve_close_form(self):
        return BurialApproveCloseForm(request=self.request, data=self.request.POST or None, instance=self.get_object())

    def get_object(self, queryset=None):
        if not hasattr(self, '_object'):
            self._object = super(BurialView, self).get_object(queryset=queryset)
        return self._object

    def get_context_data(self, **kwargs):
        b = self.get_object()
        org = self.request.user.profile.org
        return {
            'b': b,
            'reason_typical_back': Reason.objects.filter(org=org, reason_type=Reason.TYPE_BACK),
            'reason_typical_decline': Reason.objects.filter(org=org, reason_type=Reason.TYPE_DECLINE),
            'reason_typical_annulate': Reason.objects.filter(org=org, reason_type=Reason.TYPE_ANNULATE),
            'reason_typical_disapprove': Reason.objects.filter(org=org, reason_type=Reason.TYPE_DISAPPROVE),
            'approve_close_form': self.get_approve_close_form(),
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
            'place': b.get_place(),
        }

view_burial = BurialView.as_view()

class BurialsListView(PaginateListView):
    template_name = 'burial_list.html'
    context_object_name = 'burials'

    def __init__(self, *args, **kwargs):
        super(BurialsListView, self).__init__(*args, **kwargs)
        self.SORT_DEFAULT = '-pk'
        
    def get_queryset(self):
        if not self.request.GET:
            return Burial.objects.none()

        if self.request.user.is_authenticated():
            burials = Burial1.objects.filter(
                Q(applicant_organization=self.request.user.profile.org) | Q(ugh=self.request.user.profile.org),
            ).order_by('-pk')
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
                burials = burials.filter(
                    applicant_organization__name__iregex=re_search(form.cleaned_data['applicant_org']))
            if form.cleaned_data['loru_in_burials']:
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
            if form.cleaned_data['burial_container']:
                burials = burials.filter(burial_container=form.cleaned_data['burial_container'])
            if form.cleaned_data['annulated']:
                burials = burials.filter(annulated=True)
            else:
                burials = burials.filter(annulated=False)

            if form.cleaned_data.get('comment'):
                burials = burials.filter(burial__burialcomment__comment__icontains=form.cleaned_data['comment'])

            if form.cleaned_data.get('status') == Burial.STATUS_EXHUMATED:
                burials = burials.filter(status=Burial.STATUS_EXHUMATED)
            else:
                burials = burials.exclude(status=Burial.STATUS_EXHUMATED)
        else:
            burials = burials.exclude(status=Burial.STATUS_EXHUMATED)

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
            'fact_date': 'fact_date',
            '-fact_date': '-fact_date',
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

        burials_count = burials.count()
        burials = burials.order_by(*s)
        burials.count = lambda: burials_count
        return burials

    def get_template_names(self):
        if self.request.GET.get('print'):
            return 'burial_list_print.html'
        return super(BurialsListView, self).get_template_names()

    def get_form(self):
        return BurialSearchForm(data=self.request.GET or None)

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
            return Burial.objects.none()

        if self.request.user.is_authenticated() and self.request.user.profile.is_loru():
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
                   Q(annulated=False) &
                   Q(status__in=[Burial.STATUS_EXHUMATED, Burial.STATUS_CLOSED, ])
                   )
                   |
                   (
                    Q(annulated=True) &
                    Q(status__in=[Burial.STATUS_BACKED, Burial.STATUS_DRAFT, Burial.STATUS_DECLINED, ])
                   )
                 ).order_by('-pk').distinct()
        else:
            burials = Burial.objects.none()
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
            'fact_date': 'fact_date',
            '-fact_date': '-fact_date',
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
                    grave_number= int(self.request.REQUEST.get('grave_number')) \
                        if self.request.REQUEST.get('grave_number') \
                        else 1,
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

        if self.request.user.profile.is_loru():
            order = self.get_order()
            if order and order.burial and order.burial != self.get_object():
                return redirect(reverse('edit_burial', args=[order.burial.pk]) + '?order=%s' % order.pk)

        return super(CreateBurial, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
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
                write_log(self.request, b, _(u'Захоронение откреплено от заказа %s') % order.pk)
                write_log(self.request, order, _(u'Заказ: откреплено захоронение %s') % b.pk)
                msg = _(u"<a href='%(order_burial)s'>Заказ %(pk)s</a>: откреплено захоронение") % dict(
                    order_burial=reverse('order_burial', args=[order.pk]),
                    pk=order.pk,
                )
                messages.success(self.request, msg)

            if action == 'ready' and self.request.user.profile.is_loru() and b.is_edit() and b.is_full():
                b.status = Burial.STATUS_READY
                write_log(self.request, b, _(u'Захоронение отправлено на согласование'))
                msg = _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> отправлено на согласование") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm, pk=b.pk,
                )
                messages.success(self.request, msg)

            if action == 'annulate' and self.request.user.profile.is_loru() and b.can_loru_annulate():
                b.annulated = True
                write_log(self.request, b, _(u'Захоронение аннулировано'))
                msg = _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> аннулировано") % dict(
                    view_burial=reverse('view_burial', args=[b.pk]) + order_parm, pk=b.pk,
                )
                messages.success(self.request, msg)

            if action == 'approve' and self.request.user.profile.is_ugh() and b.can_approve_ugh():
                b.status = Burial.STATUS_APPROVED
                b.approve(self.request.user)
                write_log(self.request, b, _(u'Захоронение согласовано'))
                messages.success(
                    self.request,
                    _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> согласовано") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))

            if action == 'disapprove' and self.request.user.profile.is_ugh() and b.can_disapprove_ugh():
                b.status = Burial.STATUS_DRAFT
                write_log(self.request, b, _(u'Захоронение возвращено в статус черновика'))
                messages.success(
                    self.request,
                    _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> возвращено в статус черновика") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))

            if action == 'complete' and self.request.user.profile.is_ugh() and b.can_finish() and b.is_ugh():
                b.changed_by = self.request.user
                b.close(request=self.request)
                messages.success(
                    self.request,
                    _(u"<a href='%(view_burial)s'>Захоронение %(pk)s</a> закрыто") % dict(
                        view_burial=reverse('view_burial', args=[b.pk]), pk=b.pk,
                ))
                redirect_to_view = True

            if old_status != b.status or old_annulated != b.annulated:
                b.save()
            elif action != 'unbind':
                msg = _(u"Выполнить операцию не удалось: "
                        u"<a href='%(view_burial)s'>захоронение</a> в статусе \"%(status)s\"") % dict(
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
        if self.request.REQUEST.get('disapprove'):
            action = 'disapprove'
        if self.request.REQUEST.get('ready'):
            action = 'ready'
        if self.request.REQUEST.get('complete'):
            action = 'complete'
        if self.request.REQUEST.get('annulate'):
            action = 'annulate'
        if self.request.REQUEST.get('unbind'):
            action = 'unbind'
        return action

    def get_form_class(self):
        action =  self.get_action()
        if action and action not in ('annulate', 'unbind', 'disapprove'):
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
        if request.user.profile.is_loru():
            b = self.get_object()
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
        try:
            c = Cemetery.objects.get(pk=request.GET.get('cem'))
        except (ValueError, Cemetery.DoesNotExist, ):
            return HttpResponse(json.dumps({}), mimetype='application/json')
        try:
            date = datetime.datetime.strptime(request.GET.get('date'), '%d.%m.%Y').date
        except ValueError:
            # Есть таки возможность пользователю ввести плановую дату типа 30 февраля:
            return HttpResponse(json.dumps({c.pk: []}), mimetype='application/json')
        data = c.get_time_choices(date=date, request=request)
        return HttpResponse(json.dumps({c.pk: data}), mimetype='application/json')

cemetery_times = GetCemeteryTimes.as_view()

class GetCemeteryPersonalData(View):
    def get(self, request, *args, **kwargs):
        pk=request.GET.get('cem')
        if not request.user.is_authenticated() or pk is None:
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
        return HttpResponse(json.dumps({'result': result}), mimetype='application/json')

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
            write_log(self.request, self.get_object(), _(u'Захоронение эксгумировано'))
            messages.success(request, _(u"Эксгумация успешна"))
            if ex.place:
                return redirect(ex.place.url())
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
            return self.place.url()
        else:
            return reverse('dashboard')

    def get_queryset(self):
        qs = Q(burial__ugh=self.request.user.profile.org) | Q(burial__cemetery__ugh=self.request.user.profile.org)
        return ExhumationRequest.objects.filter(qs).distinct()

burial_cancel_exhumation = CancelExhumationView.as_view()

class RemoveResponsible(ArchiveMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            place = Place.objects.get(cemetery__ugh=self.request.user.profile.org, pk=kwargs['pk'])
            resp = place.responsible
            if resp:
                place.remove_responsible()
                write_log(self.request, place, _(u'Ответственный %s откреплен') % resp)
                messages.success(self.request, _(u"Ответственный %s откреплен") % resp)
            return redirect('view_place', place.pk)
        except Place.DoesNotExist:
            raise Http404

rm_responsible = RemoveResponsible.as_view()
