# coding=utf-8
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _

from import_burials.forms import ImportCsvForm, ImportCsvMinskForm
from import_burials.models import do_import_orgs, do_import_burials, do_import_services, \
                                  do_import_orders, do_import_banks, do_import_docs, do_import_dcs, \
                                  do_import_burials_minsk

class ImportMinskView(TemplateView):
    template_name = 'import_minsk.html'

    def get_context_data(self, **kwargs):
        data = super(ImportMinskView, self).get_context_data(**kwargs)
        data.update({
            'burials_form': ImportCsvMinskForm(prefix='burials'),
        })
        return data

import_minsk = ImportMinskView.as_view()

class ImportBurialsMinskView(View):
    def post(self, request, *args, **kwargs):
        transaction.set_autocommit(False)
        try:
            total = do_import_burials_minsk(request.FILES['burials-csv'],
                                            request.POST['burials-cemetery'],
                                            user=request.user)
            messages.success(request, _(u"Импорт успешен, %s записей") % total)
        finally:
            transaction.commit()
            transaction.set_autocommit(True)
        return redirect('import_minsk')

import_burials_minsk = ImportBurialsMinskView.as_view()

class ImportFormsView(TemplateView):
    template_name = 'import_forms.html'
    def get_context_data(self, **kwargs):
        data = super(ImportFormsView, self).get_context_data(**kwargs)
        data.update({
            'orgs_form': ImportCsvForm(prefix='orgs'),
            'burials_form': ImportCsvForm(prefix='burials'),
        })
        return data

import_forms = ImportFormsView.as_view()

class ImportOrgsView(View):

    def post(self, request, *args, **kwargs):
        transaction.set_autocommit(False)
        try:
            do_import_orgs(request.FILES['orgs-csv'])
            messages.success(request, _(u"Импорт успешен"))
        finally:
            transaction.commit()
            transaction.set_autocommit(True)
        return redirect('import_forms')

import_orgs = ImportOrgsView.as_view()

class ImportBurialsView(View):
    def post(self, request, *args, **kwargs):
        transaction.set_autocommit(False)
        try:
            real_i, dupes_i = do_import_burials(request.FILES['burials-csv'], user=request.user)
            messages.success(
                request,
                _(u"Импорт успешен, %(real_i)s записей, игнорировано %(dupes_i)s записей") % dict(
                    real_i=real_i, dupes_i=dupes_i
            ))
        finally:
            transaction.commit()
            transaction.set_autocommit(True)
        return redirect('import_forms')

import_burials = ImportBurialsView.as_view()

class ImportKalugaView(TemplateView):
    template_name = 'import_kaluga.html'

    def get_context_data(self, **kwargs):
        data = super(ImportKalugaView, self).get_context_data(**kwargs)
        data.update({
            'services_form': ImportCsvForm(prefix='services'),
            'banks_form': ImportCsvForm(prefix='banks'),
            'orders_form': ImportCsvForm(prefix='orders'),
            'docs_form': ImportCsvForm(prefix='docs'),
            'dcs_form': ImportCsvForm(prefix='dcs'),
        })
        return data

import_kaluga = ImportKalugaView.as_view()

class ImportBanksView(View):
    def post(self, request, *args, **kwargs):
        transaction.set_autocommit(False)
        try:
            do_import_banks(request.FILES['banks-csv'])
            messages.success(request, _(u"Импорт успешен"))
        finally:
            transaction.commit()
            transaction.set_autocommit(True)
        return redirect('import_kaluga')

import_banks = ImportBanksView.as_view()

class ImportServicesView(View):
    def post(self, request, *args, **kwargs):
        transaction.set_autocommit(False)
        try:
            do_import_services(request.FILES['services-csv'])
            messages.success(request, _(u"Импорт успешен"))
        finally:
            transaction.commit()
            transaction.set_autocommit(True)
        return redirect('import_kaluga')

import_services = ImportServicesView.as_view()

class ImportOrdersView(View):
    def post(self, request, *args, **kwargs):
        transaction.set_autocommit(False)
        try:
            real_i, dupes_i = do_import_orders(request.FILES['orders-csv'])
            messages.success(
                request,
                _(u"Импорт успешен, %(real_i)s записей, игнорировано %(dupes_i)s записей") % dict(
                    real_i=real_i, dupes_i=dupes_i
            ))
        finally:
            transaction.commit()
            transaction.set_autocommit(True)
        return redirect('import_kaluga')

import_orders = ImportOrdersView.as_view()

class ImportPersonDocsView(View):
    def post(self, request, *args, **kwargs):
        transaction.set_autocommit(False)
        try:
            do_import_docs(request.FILES['docs-csv'])
            messages.success(request, _(u"Импорт успешен"))
        finally:
            transaction.commit()
            transaction.set_autocommit(True)
        return redirect('import_kaluga')

import_docs = ImportPersonDocsView.as_view()

class ImportDeathCertsView(View):
    def post(self, request, *args, **kwargs):
        transaction.set_autocommit(False)
        try:
            real_i, dupes_i = do_import_dcs(request.FILES['dcs-csv'])
            messages.success(
                request,
                _(u"Импорт успешен, %(real_i)s записей, игнорировано %(dupes_i)s записей") % dict(
                    real_i=real_i, dupes_i=dupes_i
            ))
        finally:
            transaction.commit()
            transaction.set_autocommit(True)
        return redirect('import_kaluga')

import_dcs = ImportDeathCertsView.as_view()

