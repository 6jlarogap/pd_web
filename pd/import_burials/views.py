from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _

from import_burials.forms import ImportCsvMinskForm
from import_burials.models import do_import_burials_minsk

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
            messages.success(request, _("Импорт успешен, %s записей") % total)
        finally:
            transaction.commit()
            transaction.set_autocommit(True)
        return redirect('import_minsk')

import_burials_minsk = ImportBurialsMinskView.as_view()
