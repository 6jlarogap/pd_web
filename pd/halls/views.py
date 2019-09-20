import datetime, re

from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.views.generic.list import ListView
from django.http import Http404, HttpResponseForbidden
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import ugettext as _

from halls.forms import HallFormset, HallTimeTableForm

from logs.models import write_log
from halls.models import Hall
from users.models import Org, Profile
from users.views import UghOrLoruRequiredMixin

class HallsEdit(UghOrLoruRequiredMixin, View):
    template_name = 'halls.html'

    def get_formset(self, instance=None):
        if not instance:
            instance=self.get_object()
        return HallFormset(request=self.request, data=self.request.POST or None, instance=instance)

    def get_object(self):
        return self.request.user.profile.org

    def get_context_data(self, **kwargs):
        return {
            'formset': self.get_formset(),
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        org = self.get_object()
        if not (request.user.profile.is_loru() or request.user.profile.is_admin()):
            return HttpResponseForbidden()
        formset = self.get_formset()
        if formset.is_valid():
            for f in formset.forms:
                if f.instance.pk:
                    if f['DELETE'].value():
                        if f.instance.halltimetable_set.exists():
                            messages.error(request, _("Попытка удаления зала с назначенным ему расписанием"))
                            return self.get(request, *args, **kwargs)
                        f.instance.delete()
                        write_log(request, org, _("Удален зал: %s") % f.instance.title)
                    else:
                        f.save()
                else:
                    # fool-proof
                    do_create = True
                    for k in ('title', 'time_begin', 'time_end'):
                        if not f[k].data.strip():
                            do_create = False
                            break
                    if do_create:
                        hall = Hall.objects.create(
                            org=org,
                            title=f['title'].data.strip(),
                            time_begin=f['time_begin'].data.strip(),
                            time_end=f['time_end'].data.strip(),
                            interval=f['interval'].data,
                            is_active=f['is_active'].data,
                        )
                        write_log(request, org, _("Создан зал: %s") % hall)
            return redirect(reverse('halls_edit'))
        else:
            messages.error(request, _("Обнаружены ошибки"))
            return self.get(request, *args, **kwargs)

halls_edit_view = HallsEdit.as_view()

class HallsTimeTableView(UghOrLoruRequiredMixin, ListView):
    template_name = 'hall_timetable.html'
    context_object_name = 'halls'

    def get_queryset(self):
        org=self.request.user.profile.org
        self.date_from = datetime.date.today()
        self.choice_halls = []
        for hall in Hall.objects.filter(org=org, is_active=True):
            self.choice_halls.append((hall.pk, hall.title))

        form = self.get_form()
        if not self.request.GET:
            return []
        halls = []
        return halls

    def get_form(self):
        data = self.request.GET
        form = HallTimeTableForm(data=data or None)
        form.fields['halls'].choices = self.choice_halls
        if not data:
            form.initial['date_from'] = self.date_from
            form.initial['halls'] = [ h[0] for h in self.choice_halls ]
        return form

    def get_context_data(self, **kwargs):
        data = super(HallsTimeTableView, self).get_context_data(**kwargs)
        form = self.get_form()
        data.update(form=form)
        return data

halls_timetable_view = HallsTimeTableView.as_view()
