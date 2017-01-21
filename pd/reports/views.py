from django.http import HttpResponse, Http404
from django.views.generic.detail import DetailView
from django.shortcuts import get_object_or_404

from users.models import Profile
from reports.models import Report


class ReportView(DetailView):
    model = Report

    def get(self, request, pk, *args, **kwargs):
        report = get_object_or_404(Report, pk=pk)
        try:
            if request.user.profile.org != report.user.profile.org:
                raise Http404
        except (AttributeError, Profile.DoesNotExist,):
            raise Http404
        return super(ReportView, self).get(request, pk, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        return HttpResponse(context['object'].html)

report_view = ReportView.as_view()