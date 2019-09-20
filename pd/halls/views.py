import datetime, re

from django.shortcuts import render, redirect
from django.views.generic.base import View
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

class HallsTimeTableView(UghOrLoruRequiredMixin, View):
    template_name = 'hall_timetable.html'

    def get_context_data(self):
        context = dict()
        self.choice_halls = []
        halls_pks = []
        for hall in Hall.objects.filter(org=self.request.user.profile.org, is_active=True):
            halls_pks.append(str(hall.pk))
            self.choice_halls.append((hall.pk, hall.title))
        if not halls_pks:
                context.update(
                    no_halls_in_system=_('В организации нет залов. Обратитесь к администратору'),
                )
                return context
        for h in self.request.GET.getlist('halls'):
            if str(h) not in halls_pks:
                context.update(
                    invalid_hall_got=_('Указан не действующий или неверный зал в запросе'),
                )
                return context
        items = []
        for k in list(self.request.GET.keys()):
            values = self.request.GET.getlist(k)
            for v in values:
                items.append((k,v))
        get_params = '&'.join(['%s=%s' %  (k, v) for k,v in items])

        context.update(
            is_hall_manager = self.request.user.profile.is_hall_manager(),
            GET_PARAMS=get_params,
            form=self.get_form(),
        )
        return context

    def get_form(self):
        data = self.request.GET
        form = HallTimeTableForm(data=data or None)
        form.fields['halls'].choices = self.choice_halls
        if not data:
            form.initial['date_from'] = datetime.date.today()
            form.initial['halls'] = [ h[0] for h in self.choice_halls ]
        return form

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not self.request.user.profile.is_hall_manager():
            return HttpResponseForbidden()
        get_params = request.POST.get('GET_PARAMS', '')
        if get_params:
            get_params = '?' + request.POST['GET_PARAMS']
        return redirect(reverse('halls_timetable') + get_params)

halls_timetable_view = HallsTimeTableView.as_view()
