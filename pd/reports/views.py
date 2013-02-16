from django.http import HttpResponse
from django.views.generic.detail import DetailView

from reports.models import Report


class ReportView(DetailView):
    model = Report

    def render_to_response(self, context, **response_kwargs):
        return HttpResponse(context['object'].html)

report_view = ReportView.as_view()