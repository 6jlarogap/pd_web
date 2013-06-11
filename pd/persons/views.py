import json

from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.views.generic.base import View

from persons.models import DeadPerson, AlivePerson, BasePerson, DocumentSource


class AutocompleteFIO(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']

        fio = [f.strip('.') for f in query.split(' ')]
        q = Q()
        if len(fio) > 2:
            q &= Q(middle_name__istartswith=fio[2])
        if len(fio) > 1:
            q &= Q(first_name__istartswith=fio[1])
        if len(fio) > 0:
            q &= Q(last_name__istartswith=fio[0])

        persons = DeadPerson.objects.filter(q).distinct('last_name', 'first_name', 'middle_name')
        return HttpResponse(json.dumps([{'value': unicode(c)} for c in persons[:20]]), mimetype='text/javascript')

autocomplete_fio = AutocompleteFIO.as_view()

class AutocompleteFirstName(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']
        first_names = BasePerson.objects.filter(first_name__istartswith=query).order_by('first_name').distinct('first_name')
        return HttpResponse(json.dumps([{'value': c.first_name} for c in first_names[:20]]), mimetype='text/javascript')

autocomplete_first_name = AutocompleteFirstName.as_view()

class AutocompleteMiddleName(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']
        middle_names = BasePerson.objects.filter(middle_name__istartswith=query).order_by('middle_name').distinct('middle_name')
        return HttpResponse(json.dumps([{'value': c.middle_name} for c in middle_names[:20]]), mimetype='text/javascript')

autocomplete_middle_name = AutocompleteMiddleName.as_view()

class AutocompleteAlive(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']

        fio = [f.strip('.') for f in query.split(' ')]
        q = Q()
        if len(fio) > 2:
            q &= Q(middle_name__istartswith=fio[2])
        if len(fio) > 1:
            q &= Q(first_name__istartswith=fio[1])
        if len(fio) > 0:
            q &= Q(last_name__istartswith=fio[0])

        persons = AlivePerson.objects.filter(q).distinct('last_name', 'first_name', 'middle_name')
        return HttpResponse(json.dumps([{'value': unicode(c)} for c in persons[:20]]), mimetype='text/javascript')

autocomplete_alive = AutocompleteAlive.as_view()

class AutocompleteDocSources(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']
        dcs = DocumentSource.objects.filter(name__icontains=query)
        return HttpResponse(json.dumps([{'value': unicode(c)} for c in dcs[:20]]), mimetype='text/javascript')

autocomplete_docsources = AutocompleteDocSources.as_view()