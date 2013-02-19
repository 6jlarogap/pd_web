# coding=utf-8

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from django.utils.translation import ugettext as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from burials.forms import CemeteryForm, AreaFormset, PlaceEditForm
from burials.models import Cemetery, Place
from burials.burials_views import *
from logs.models import write_log
from users.models import Profile, Org


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

class PlaceView(UpdateView):
    template_name = 'view_place.html'
    context_object_name = 'place'
    model = Place
    form_class = PlaceEditForm

    def get_success_url(self):
        messages.success(self.request, _(u"Данные обновлены"))
        return reverse('view_place', args=[self.get_object().pk])

view_place = PlaceView.as_view()

class AddDoverView(UGHRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        f = AddDoverForm(data=request.POST)
        try:
            agent = Profile.objects.get(pk=request.GET['agent'], is_agent=True)
        except Profile.DoesNotExist:
            return HttpResponse(_(u'Агент не существует'), mimetype='text/plain')
        except KeyError:
            return HttpResponse(_(u'Данные невалидны'), mimetype='text/plain')
        if f.is_valid():
            dover = f.save(commit=False)
            dover.agent = agent
            dover.save()
            return HttpResponse(json.dumps({'pk': dover.pk, 'label': u'%s' % dover}), mimetype='application/json')
        else:
            print f.errors
            return HttpResponse(_(u'Данные невалидны'), mimetype='text/plain')

add_dover = csrf_exempt(AddDoverView.as_view())

class AddAgentView(UGHRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        fa = AddAgentForm(data=request.POST)
        fd = AddDoverForm(data=request.POST)
        try:
            loru = Org.objects.get(pk=request.GET['loru'], type=Org.PROFILE_LORU)
        except Org.DoesNotExist:
            return HttpResponse(_(u'ЛОРУ не существует'), mimetype='text/plain')
        except KeyError:
            return HttpResponse(_(u'Данные невалидны'), mimetype='text/plain')
        if fa.is_valid() and fd.is_valid():
            user = fa.save()
            agent, _created = Profile.objects.get_or_create(user=user, org = loru, is_agent=True)
            dover = fd.save(commit=False)
            dover.agent = agent
            dover.save()
            return HttpResponse(json.dumps({
                'pk': agent.pk, 'label': u'%s' % agent,
                'dover_pk': dover.pk, 'dover_label': u'%s' % dover
            }), mimetype='application/json')
        else:
            errors = '\n'.join([u'%s: %s' % (k,v[0]) for k,v in fa.errors.items()] + [u'%s: %s' % kv for kv in fd.errors.items()])
            return HttpResponse(_(u'Данные невалидны: %s') % errors, mimetype='text/plain')

add_agent = csrf_exempt(AddAgentView.as_view())