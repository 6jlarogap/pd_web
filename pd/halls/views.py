import datetime, base64
from urllib.parse import parse_qs

from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.http import Http404, HttpResponseForbidden
from django.contrib import messages
from django.urls import reverse
from django.utils import formats
from django.utils.translation import ugettext as _
from django.utils.formats import date_format

from django.conf import settings

from halls.forms import HallFormset, HallTimeTableForm

from logs.models import write_log
from halls.models import Hall, HallTimeTable
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
                    for k in ('title', 'time_start', 'time_end'):
                        if not f[k].data.strip():
                            do_create = False
                            break
                    if do_create:
                        hall = Hall.objects.create(
                            org=org,
                            title=f['title'].data.strip(),
                            time_start=f['time_start'].data.strip(),
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

    # После этого выводим расчет на завтра по умолчанию
    #
    TOMORROW_BEGINS_AT = '13:00'

    # Так записываются начальные id input'ов в форме, в таблицах залов
    #
    DT_ID_FORMAT = "%Y_%m%_%d_%H_%M"
    
    def make_id_prefix(self, dt_start, dt_end):
        """
        Префикс id html элементов

        id html элемента будет таким:
            id__YYYY_MM_DD_hh_mm__YYYY_MM_DD_hh_mm__{text_details,text_details_old,cb_free,cb_book}
                ----------------  ----------------
                start             end
        """
        start = datetime.datetime.strftime(dt_start, self.DT_ID_FORMAT)
        end = datetime.datetime.strftime(dt_end, self.DT_ID_FORMAT)
        return "id__%s__%s" % (start, end,)

    def get_timetable(self, date, halls_pks):

        # Собственно расчет, т.е. подготовка post формы в шаблоне,
        # за дату date по заказанным залам halls_pks
        #
        user = self.request.user

        # По кажлому залу отдельный словарь,
        # внутри которого массив сеансов
        #
        hall_timetables = []
        
        # Нашлись ли сеансы для редактирования (назначения или отмены назначения)
        #
        have_smth_to_edit = False

        dt_now = datetime.datetime.now()
        today = dt_now.date()
        date_start = datetime.datetime(
            date.year, date.month, date.day, 0, 0
        )
        date_end = date_start + datetime.timedelta(days=1)

        for hall_pk in halls_pks:
            hall = Hall.objects.get(pk=hall_pk)
            hall_interval_timedelta = datetime.timedelta(seconds=hall.interval * 60)
            hall_start = datetime.datetime.strptime(hall.time_start, "%H:%M")
            hall_start = datetime.datetime(
                year=date.year, month=date.month, day=date.day,
                hour=hall_start.hour, minute=hall_start.minute,
            )
            hall_end = datetime.datetime.strptime(hall.time_end, "%H:%M")
            hall_end = datetime.datetime(
                year=date.year, month=date.month, day=date.day,
                hour=hall_end.hour, minute=hall_end.minute,
            )
            # dt_border:
            #   время первого возможного сеанса. Если завтра, то это hall_start,
            #   если сегодня, то время первого свободного сеанса
            #   после текущего времени. Если вчера, то заглушка: полночь на следующий день
            #
            # 
            if date < today:
                dt_border = date_end
            else:
                # сегодня или завтра
                #
                dt_border = datetime.datetime(
                    hall_start.year, hall_start.month, hall_start.day,
                    hall_start.hour, hall_start.minute, 0)
            if date == today:
                while dt_border < hall_end and dt_border < dt_now:
                    dt_border += hall_interval_timedelta

            # Начала и окончания сеансов, которые могут оказаться свободными на дату date.
            # если они окажутся занятыми, при проходе через имеющиеся сеансы
            # будем удалять.
            #
            date_free_sessions = []
            dt_start = dt_border
            while dt_start < hall_end:
                dt_end = dt_start + hall_interval_timedelta
                if dt_end > hall_end:
                    break
                date_free_sessions.append(dict(dt_start=dt_start, dt_end=dt_end))
                dt_start = dt_end

            to_delete_from_date_free_sessions = []

            hall_timetable=dict(title=hall.title)

            # Сеансы до и после dt_border. В те что после dt_border,
            # вставим свободные интервалы, после чего future_sessions
            # отсортируем по времени начала сеанса. Результат -
            # массив timetable = past_sessions + future_sessions
            #
            past_sessions = []
            future_sessions = []
            for tt in HallTimeTable.objects.filter(
                    hall=hall,
                    dt_start__gte=date_start,
                    dt_end__lt=date_end,
                ).order_by('dt_start'):
                tt_item = dict(
                    free = False,
                    dt_start=tt.dt_start,
                    dt_end=tt.dt_end,
                    details=tt.details,
                    creator=tt.user,
                    id_prefix=self.make_id_prefix(tt.dt_start, tt.dt_end),
                )
                if tt.dt_end <= dt_border:
                    tt_item.update(editable=False)
                    past_sessions.append(tt_item)
                else:
                    editable = bool(
                        user.profile.is_hall_manager() and user == tt.user or \
                        user.profile.is_hall_admin()
                    )
                    if editable:
                        have_smth_to_edit = True
                    tt_item.update(editable=editable)
                    future_sessions.append(tt_item)
                    for i, s in enumerate(date_free_sessions):
                       if tt.dt_end <= s.dt_start or tt.dt_start >= s.dt_end:
                           # Конец интервала из базы до начала рассматриваемого: не пересекает
                           # Начало интервала из базы после  рассматриваемого: не пересекает
                           pass
                       else:
                           # Во всех остальных случаях как-то пересекает
                            to_delete_from_date_free_sessions.append[i]

            for i in to_delete_from_date_free_sessions:
                del date_free_sessions[i]
            editable = bool(user.profile.is_hall_manager() and date_free_sessions)
            if editable:
                have_smth_to_edit = True
            for tt_item in date_free_sessions:
                tt_item.update(
                    free = True,
                    details='',
                    creator=user,
                    id_prefix=self.make_id_prefix(tt_item['dt_start'], tt_item['dt_end']),
                    editable=editable,
                )
            future_sessions += date_free_sessions
            future_sessions.sort(key=lambda k: k['dt_start'])

            hall_timetable.update(timetable=past_sessions + future_sessions)            
            hall_timetables.append(hall_timetable)

        result = dict(
            have_smth_to_edit=have_smth_to_edit,
            hall_timetables=hall_timetables,
        )
        return result

    def get_default_date(self):
        """
        Дата по умолчанию. До 13:00 сегодня, после 13:00 - завтра
        """
        result = datetime.date.today()
        now = datetime.datetime.now()
        if datetime.datetime.strftime(now, '%H:%M') > self.TOMORROW_BEGINS_AT:
            result = result + datetime.timedelta(days=1)
        return result

    def get_context_data(self):
        halls = []
        context = dict()

        self.choice_halls = []
        self.all_halls_pks = []
        for hall in Hall.objects.filter(org=self.request.user.profile.org, is_active=True):
            self.all_halls_pks.append(str(hall.pk))
            self.choice_halls.append((hall.pk, hall.title))
        if not self.all_halls_pks:
                context.update(
                    no_halls_in_system=_('В организации нет залов. Обратитесь к администратору'),
                )
                return context

        form=self.get_form()
        date = None
        if form.is_valid() and form.data:
            date = form.cleaned_data.get('hall_date_from')
            halls_pks = form.cleaned_data.get('halls')
            context.update(self.get_timetable(date, halls_pks))

        items = []
        for k in list(self.request.GET.keys()):
            values = self.request.GET.getlist(k)
            for v in values:
                items.append((k,v))
        get_params = '&'.join(['%s=%s' %  (k, v) for k,v in items if k not in ('post_errors', )])

        today_tomorrow = None
        if date:
            today = datetime.date.today()
            if date == today:
                today_tomorrow = _('сегодня')
            elif date - today == datetime.timedelta(days=1):
                today_tomorrow = _('завтра')

        post_errors = self.request.GET.get('post_errors')
        if post_errors:
            try:
                post_errors = base64.urlsafe_b64decode(post_errors).decode('utf8')
                post_errors = post_errors.split('~')
            except:
                post_errors = None

        context.update(
            date=date,
            today_tomorrow=today_tomorrow,
            is_hall_manager = self.request.user.profile.is_hall_manager(),
            post_errors=post_errors,
            GET_PARAMS=get_params,
            form=form,
        )
        return context

    def get_form(self):
        data = self.request.GET
        form = HallTimeTableForm(data=data or None)
        form.fields['halls'].choices = self.choice_halls
        if not data:
            form.initial['hall_date_from'] = self.get_default_date()
            form.initial['halls'] = [ h[0] for h in self.choice_halls ]
        return form

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data()
        if not self.request.GET and self.all_halls_pks:
            # Сразу выведем все залы за self.get_default_date()
            #
            format_date = formats.get_format("SHORT_DATE_FORMAT", lang=settings.LANGUAGE_CODE)
            date = self.get_default_date()
            date_str = date_format(date, format=format_date)
            get_params = '?hall_date_from=%s&%s' % (
                date_str,
                '&'.join(['halls=%s' %  pk for pk in self.all_halls_pks])
            )
            return redirect(reverse('halls_timetable') + get_params)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        if not self.request.user.profile.is_hall_manager():
            return HttpResponseForbidden()
        post_errors = []

        get_params = request.POST.get('GET_PARAMS', '')
        params = parse_qs(get_params)
        try:
            date_str = params['hall_date_from'][0]
            halls_pks = params['halls']
        except (KeyError, IndexError,):
            raise Http404
        org = request.user.profile.org
        halls = []
        for pk in halls_pks:
            try:
                halls.append(Hall.objects.get(pk=pk, org=org))
            except Hall.DoesNotExist:
                return HttpResponseForbidden()
        date_formats = formats.get_format("DATE_INPUT_FORMATS", lang=settings.LANGUAGE_CODE)
        for f in date_formats:
            try:
                date = datetime.datetime.strptime(date_str, f).date()
                break
            except ValueError:
                pass
        if not date:
            raise Http404

        get_params = '?' + get_params
        if post_errors:
            post_errors = '~'.join(post_errors)
            post_errors = base64.urlsafe_b64encode(post_errors.encode('utf8')).decode('utf8')
            post_errors = post_errors.replace('=', '%3D')
            get_params += '&post_errors=%s' % post_errors
        return redirect(reverse('halls_timetable') + get_params)

halls_timetable_view = HallsTimeTableView.as_view()
