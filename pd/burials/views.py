# coding=utf-8
import datetime
from burials.forms import BurialRequestCreateForm
from django.contrib import messages
from django.db.models.query_utils import Q
from django.shortcuts import redirect
from django.views.generic.base import TemplateView, View

from burials.models import BurialRequest, Cemetery
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView


class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        try:
            profile = self.request.user.profile
        except AttributeError:
            qs = Q()
        else:
            if profile.is_loru():
                qs = Q(approved_ugh__isnull=False, processed_loru__isnull=True)
            if profile.is_ugh():
                qs = Q(approved_ugh__isnull=True) | Q(processed_loru__isnull=False, completed_ugh__isnull=True)
        return {
            'burials': BurialRequest.objects.filter(qs),
            }

dashboard = DashboardView.as_view()

class RequestView(DetailView):
    template_name = 'view_request.html'

    def get_queryset(self):
        try:
            profile = self.request.user.profile
        except AttributeError:
            qs = Q()
        else:
            if profile.is_loru():
                qs = Q(approved_ugh__isnull=False, processed_loru__isnull=True)
            if profile.is_ugh():
                qs = Q(approved_ugh__isnull=True) | Q(processed_loru__isnull=False, completed_ugh__isnull=True)
        return BurialRequest.objects.filter(qs)

    def get(self, request, *args, **kwargs):
        b = self.get_object()
        if request.GET.get('approve') and request.user.profile.is_ugh():
            b.approved_ugh = datetime.datetime.now()
            b.save()
            messages.success(request, u"Заявка одобрена и передана ЛОРУ")
            return redirect('dashboard')
        if request.GET.get('execute') and request.user.profile.is_loru():
            b.processed_loru = datetime.datetime.now()
            b.save()
            messages.success(request, u"Захоронение произведено, заявка передана УГХ для проверки")
            return redirect('dashboard')
        if request.GET.get('complete') and request.user.profile.is_ugh():
            b.completed_ugh = datetime.datetime.now()
            b.number = b.pk
            b.save()
            messages.success(request, u"Заявка закрыта")
            return redirect('dashboard')
        return super(RequestView, self).get(request, *args, **kwargs)

view_request = RequestView.as_view()

class CreateRequestView(CreateView):
    template_name = 'create_request.html'
    form_class = BurialRequestCreateForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated() or not self.request.user.is_loru():
            return redirect('/')
        return super(CreateRequestView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        messages.success(self.request, u"Заявка создана и отправлена на согласование в УГХ")
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
        messages.success(self.request, u"Кладбище создано")
        return redirect('manage_cemeteries')

manage_cemeteries_create = CemeteryCreate.as_view()