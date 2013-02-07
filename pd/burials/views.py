# coding=utf-8
import datetime
from burials.forms import BurialRequestCreateForm, CemeteryForm, AreaFormset
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.shortcuts import redirect
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _

from burials.models import BurialRequest, Cemetery, Reason, Burial
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from logs.models import write_log


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
                qs &= Q(status=BurialRequest.STATUS_DRAFT) | \
                      Q(status=BurialRequest.STATUS_BACKED) | \
                      Q(status=BurialRequest.STATUS_DECLINED)
            if profile.is_ugh():
                qs &= Q(status=BurialRequest.STATUS_READY) | Q(status=BurialRequest.STATUS_APPROVED)
        return {'burials': BurialRequest.objects.filter(qs).distinct()}

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
        return {'burials': BurialRequest.objects.filter(qs).distinct().order_by('-pk')}

archive = ArchiveView.as_view()

class RequestView(ArchiveMixin, DetailView):
    template_name = 'view_request.html'
    context_object_name = 'b'

    def get_queryset(self):
        qs = self.get_qs_filter()
        return BurialRequest.objects.filter(qs).distinct()

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('dashboard')
        b = self.get_object()
        b.changed = datetime.datetime.now()
        b.changed_by = request.user
        old_status = b.status
        reason = request.POST.get('reason') or request.POST.get('reason_typical')
        if request.POST.get('back') and request.user.profile.is_loru() and not b.is_finished():
            b.status = BurialRequest.STATUS_BACKED
            write_log(request, b, _(u'Заявка отозвана'), reason)
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> отозвана") % (
                reverse('view_request', args=[b.pk]), b.pk,
            ))
        if request.POST.get('ready') and request.user.profile.is_loru() and b.is_edit():
            b.status = BurialRequest.STATUS_READY
            write_log(request, b, _(u'Заявка отправлена на согласование'))
            msg = _(u"<a href='%s'>Заявка %s</a> отправлена на согласование") % (
                reverse('view_request', args=[b.pk]), b.pk,
            )
            messages.success(request, msg)
        if request.POST.get('approve') and request.user.profile.is_ugh() and b.is_ready():
            b.status = BurialRequest.STATUS_APPROVED
            write_log(request, b, _(u'Заявка согласована'))
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> согласована") % (
                reverse('view_request', args=[b.pk]), b.pk,
            ))
        if request.POST.get('decline') and request.user.profile.is_ugh() and b.is_ready():
            b.status = BurialRequest.STATUS_DECLINED
            write_log(request, b, _(u'Заявка отклонена'), reason)
            messages.success(request, _(u"<a href='%s'>Заявка %s</a> отклонена") % (
                reverse('view_request', args=[b.pk]), b.pk,
            ))
        if request.POST.get('complete') and request.user.profile.is_ugh() and b.is_approved():
            b.status = BurialRequest.STATUS_CLOSED
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
            b.status = BurialRequest.STATUS_ANNULATED
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
    form_class = BurialRequestCreateForm

    def get_queryset(self):
        q = Q(status=BurialRequest.STATUS_DRAFT) | \
            Q(status=BurialRequest.STATUS_DECLINED) | \
            Q(status=BurialRequest.STATUS_BACKED)
        return BurialRequest.objects.filter(q, loru=self.request.user.profile.org)

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
            self.object.status = BurialRequest.STATUS_READY
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
        burials = Burial.objects.all().order_by('-pk')
        return burials

burial_list = BurialsListView.as_view()

