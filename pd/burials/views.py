# coding=utf-8
import datetime
from burials.forms import BurialRequestCreateForm
from django.contrib import messages
from django.db.models.query_utils import Q
from django.shortcuts import redirect
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _

from burials.models import BurialRequest, Cemetery
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from logs.models import write_log


class BurialsListGenericMixin:
    def get_qs_filter(self):
        qs = Q(pk__isnull=True)
        if self.request.user.is_authenticated():
            if self.request.user.profile.is_loru():
                qs = Q(creator=self.request.user)
            if self.request.user.profile.is_ugh():
                qs = Q(creator__profile__org__ugh_list__ugh=self.request.user.profile.org)
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
                qs &= Q(ready_loru__isnull=True) | Q(approved_ugh__isnull=False, processed_loru__isnull=True)
            if profile.is_ugh():
                qs &= Q(ready_loru__isnull=False, approved_ugh__isnull=True) | Q(processed_loru__isnull=False, completed_ugh__isnull=True)
        return {'burials': BurialRequest.objects.filter(qs).distinct()}

    def get(self, request, *args, **kwargs):
        if not request.GET:
            return redirect('archive')
        else:
            return super(DashboardView, self).get(request, *args, **kwargs)

dashboard = DashboardView.as_view()

class ArchiveView(BurialsListGenericMixin, TemplateView):
    template_name = 'archive.html'

    def get_qs_filter(self):
        qs = Q(pk__isnull=True)
        if self.request.user.is_authenticated():
            if self.request.user.profile.is_loru():
                qs = Q(creator=self.request.user)
            if self.request.user.profile.is_ugh():
                qs = Q(connected_ug=self.request.user.profile.org)
        return qs

    def get_context_data(self, **kwargs):
        qs = self.get_qs_filter()
        return {'burials': BurialRequest.objects.filter(qs).distinct()}

archive = ArchiveView.as_view()

class RequestView(BurialsListGenericMixin, DetailView):
    template_name = 'view_request.html'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return BurialRequest.objects.filter(qs).distinct()

    def get(self, request, *args, **kwargs):
        b = self.get_object()
        if request.GET.get('ready') and request.user.profile.is_loru():
            b.ready_loru = datetime.datetime.now()
            b.save()
            write_log(request, b, _(u'Заявка отправлена на согласование'))
            messages.success(request, _(u"Заявка отправлена на согласование"))
            return redirect('dashboard')
        if request.GET.get('approve') and request.user.profile.is_ugh():
            b.approved_ugh = datetime.datetime.now()
            b.save()
            write_log(request, b, _(u'Заявка одобрена и передана ЛОРУ'))
            messages.success(request, _(u"Заявка одобрена и передана ЛОРУ"))
            return redirect('dashboard')
        if request.GET.get('execute') and request.user.profile.is_loru():
            b.processed_loru = datetime.datetime.now()
            b.save()
            write_log(request, b, _(u'Захоронение произведено'))
            messages.success(request, _(u"Захоронение произведено, заявка передана УГХ для проверки"))
            return redirect('dashboard')
        if request.GET.get('complete') and request.user.profile.is_ugh():
            b.completed_ugh = datetime.datetime.now()
            b.number = b.pk
            b.save()
            write_log(request, b, _(u'Заявка закрыта'))
            messages.success(request, _(u"Заявка закрыта"))
            return redirect('dashboard')
        if request.GET:
            return redirect('view_request', b.pk)
        return super(RequestView, self).get(request, *args, **kwargs)

view_request = RequestView.as_view()

class CreateRequestView(CreateView):
    template_name = 'create_request.html'
    form_class = BurialRequestCreateForm

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
        if self.request.REQUEST.get('ready'):
            self.object.ready_loru = datetime.datetime.now()
        self.object.save()
        write_log(self.request, self.object, _(u'Создана заявка'))
        messages.success(self.request, _(u"Заявка создана и отправлена на согласование в УГХ"))
        return redirect('dashboard')

create_request = CreateRequestView.as_view()

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
        return Cemetery.objects.filter(Q(creator__isnull=True) | Q(creator=self.request.user))

manage_cemeteries = CemeteryList.as_view()

class CemeteryCreate(UGHRequiredMixin, CreateView):
    template_name = 'cemetery_create.html'
    model = Cemetery

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        messages.success(self.request, _(u"Кладбище создано"))
        return redirect('manage_cemeteries')

manage_cemeteries_create = CemeteryCreate.as_view()