# coding=utf-8

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.shortcuts import redirect
from django.views.generic.base import View
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from burials.forms import CemeteryForm, AreaFormset
from burials.models import Cemetery, Place
from burials.burials_views import *
from logs.models import write_log


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

class PlaceView(DetailView):
    template_name = 'view_place.html'
    context_object_name = 'place'
    model = Place

view_place = PlaceView.as_view()

