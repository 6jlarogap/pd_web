# coding=utf-8
from burials.models import BurialRequest
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from django.utils.translation import ugettext_lazy as _

from geo.forms import LocationForm
from logs.models import write_log
from persons.forms import DeathCertificateForm, PersonIDForm
from persons.models import DeadPerson


class CreateDeadmanView(CreateView):
    model = DeadPerson
    template_name = 'create_deadman.html'

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated() or not self.request.user.profile.is_loru():
            return redirect('/')
        return super(CreateDeadmanView, self).dispatch(request, *args, **kwargs)

    def create_forms(self):
        dm = self.get_instance()
        self.dc_form = DeathCertificateForm(
            data=self.request.POST or None, prefix='dc', instance=dm and dm.deathcertificate)
        self.addr_form = LocationForm(data=self.request.POST or None, prefix='addr', instance=dm and dm.address)

    def get_br(self):
        return BurialRequest.objects.get(pk=self.kwargs['br_pk'])

    def form_valid(self, form):
        self.create_forms()
        if self.dc_form.is_valid() and self.addr_form.is_valid():
            deadman = form.save(commit=False)
            deadman.address = self.addr_form.save()
            deadman.save()

            dc = self.dc_form.save(commit=False)
            dc.person = deadman
            dc.save()

            br = self.get_br()
            br.deadman = deadman
            br.save()

            write_log(self.request, deadman, _(u'Усопший прикреплен'))
            messages.success(self.request, _(u"Усопший прикреплен"))

            return redirect('edit_request', br.pk)
        else:
            return self.form_invalid(form)

    def get_instance(self):
        br = self.get_br()
        return br.deadman

    def get_form_kwargs(self, **kwargs):
        data = super(CreateDeadmanView, self).get_form_kwargs(**kwargs)
        data['instance'] = self.get_instance()
        return data

    def get_context_data(self, **kwargs):
        data = super(CreateDeadmanView, self).get_context_data(**kwargs)
        self.create_forms()
        data.update(dc_form=self.dc_form, addr_form=self.addr_form, br=self.get_br())
        return data

create_deadman = CreateDeadmanView.as_view()
