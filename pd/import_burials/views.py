# coding=utf-8
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _

from import_burials.forms import ImportCsvForm
from import_burials.models import do_import_orgs, do_import_burials


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
import_burials = ImportBurialsView.as_view()
