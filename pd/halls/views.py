from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.http import Http404, HttpResponseForbidden
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import ugettext as _

from halls.forms import HallFormset

from logs.models import write_log
from halls.models import Hall
from users.models import Org, Profile

class HallsEdit(View):
    template_name = 'halls.html'

    def get_formset(self, instance=None):
        if not instance:
            instance=self.get_object()
        return HallFormset(request=self.request, data=self.request.POST or None, instance=instance)

    def get_object(self):
        try:
            return self.request.user.profile.org
        except (AttributeError, Profile.DoesNotExist, ):
            raise Http404

    def get_context_data(self, **kwargs):
        return {
            'formset': self.get_formset(),
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        org = self.get_object()
        if not ( request.user.profile.is_loru() or request.user.profile.is_admin()):
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
                        write_log(request, org, _("Удален зал %s") % f.instance.title)
                    else:
                        f.save()
                else:
                    do_create = True
                    for k in ('title', 'time_begin', 'time_end'):
                        if not f[k].data.strip():
                            do_create = False
                            break
                    if do_create:
                        Hall.objects.create(
                            org=org,
                            title=f['title'].data.strip(),
                            time_begin=f['time_begin'].data.strip(),
                            time_end=f['time_end'].data.strip(),
                            interval=f['interval'].data,
                            is_active=f['is_active'].data,
                        )
            return redirect(reverse('halls'))
        else:
            messages.error(request, _("Обнаружены ошибки"))
            return self.get(request, *args, **kwargs)

halls_view = HallsEdit.as_view()
