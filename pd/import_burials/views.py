# coding=utf-8
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _

from import_burials.forms import ImportCsvForm
from import_burials.models import do_import_orgs, do_import_burials, do_import_services, do_import_orders, do_import_banks


class ImportFormsView(TemplateView):
    template_name = 'import_forms.html'

    def get_context_data(self, **kwargs):
        return {
            'orgs_form': ImportCsvForm(prefix='orgs'),
            'burials_form': ImportCsvForm(prefix='burials'),
        }

import_forms = ImportFormsView.as_view()

class ImportOrgsView(View):
    def post(self, request, *args, **kwargs):
        do_import_orgs(request.FILES['orgs-csv'])
        messages.success(request, _(u"Импорт успешен"))
        return redirect('import_forms')

import_orgs = transaction.commit_on_success(ImportOrgsView.as_view())

class ImportBurialsView(View):
    def post(self, request, *args, **kwargs):
        do_import_burials(request.FILES['burials-csv'], user=request.user)
        messages.success(request, _(u"Импорт успешен"))
        return redirect('import_forms')

import_burials = transaction.commit_on_success(ImportBurialsView.as_view())

class ImportKalugaView(TemplateView):
    template_name = 'import_kaluga.html'

    def get_context_data(self, **kwargs):
        return {
            'services_form': ImportCsvForm(prefix='services'),
            'banks_form': ImportCsvForm(prefix='banks'),
            'orders_form': ImportCsvForm(prefix='orders'),
        }

import_kaluga = ImportKalugaView.as_view()

class ImportBanksView(View):
    def post(self, request, *args, **kwargs):
        do_import_banks(request.FILES['banks-csv'])
        messages.success(request, _(u"Импорт успешен"))
        return redirect('import_kaluga')

import_banks = transaction.commit_on_success(ImportBanksView.as_view())

class ImportServicesView(View):
    def post(self, request, *args, **kwargs):
        do_import_services(request.FILES['services-csv'])
        messages.success(request, _(u"Импорт успешен"))
        return redirect('import_kaluga')

import_services = transaction.commit_on_success(ImportServicesView.as_view())

class ImportOrdersView(View):
    def post(self, request, *args, **kwargs):
        do_import_orders(request.FILES['orders-csv'])
        messages.success(request, _(u"Импорт успешен"))
        return redirect('import_kaluga')

import_orders = transaction.commit_on_success(ImportOrdersView.as_view())

