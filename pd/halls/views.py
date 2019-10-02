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

from halls.forms import HallFormset, HallTimeTableForm, HallTimeForm

from logs.models import write_log
from halls.models import Hall, HallTimeTable, HallWeekly
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
                    if f['title'].data.strip():
                        hall = Hall.objects.create(
                            org=org,
                            title=f['title'].data.strip(),
                            is_active=f['is_active'].data,
                        )
                        for d in HallWeekly.get_defaults():
                            hw = HallWeekly(hall=hall)
                            for attr in d:
                                setattr(hw, attr, d[attr])
                            hw.save(force_insert=True)
                        write_log(request, org, _("Создан зал c расписанием по умолчанию: %s") % hall)
            return redirect(reverse('halls_edit'))
        else:
            messages.error(request, _("Обнаружены ошибки"))
            return self.get(request, *args, **kwargs)

halls_edit_view = HallsEdit.as_view()

class HallsTimeTableMixin(object):
    # Так записываются начальные id input'ов в форме, в таблицах залов
    #
    DT_ID_FORMAT = "%Y%m%d%H%M"

    def hhmms_from_dts(self, dt_start, dt_end):
        """
        Вернуть HH:MM от dt_start, dt_end, с учетом dt_end == 24:00
        """
        s_start = datetime.datetime.strftime(dt_start, '%H:%M')
        if dt_end.date() > dt_start.date():
            s_end = '24:00'
        else:
            s_end = datetime.datetime.strftime(dt_end, '%H:%M')
        return s_start, s_end

    def make_html_name_prefix(self, hall, dt_start, dt_end):
        """
        Префикс id html элементов

        name html элемента будет таким:
            <hall.pk>__hhmm__hhmm__{text_details,text_details_old,cb_free,cb_book}
        id html элемента будет:
            id__<html_name_prefix>
        """
        start = datetime.datetime.strftime(dt_start, self.DT_ID_FORMAT)
        end = datetime.datetime.strftime(dt_end, self.DT_ID_FORMAT)
        return "%s__%s__%s" % (hall.pk, start, end,)

    def mk_interval(self, t_start, t_end):
        """
        datetimes начала и окончания интервала, если времена заданы в self.DT_ID_FORMAT
        """
        dt_start = datetime.datetime.strptime(t_start, self.DT_ID_FORMAT)
        dt_end = datetime.datetime.strptime(t_end, self.DT_ID_FORMAT)
        return dt_start, dt_end

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
            if hall.time_end == '24:00':
                hall_end = date_end
            else:
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
                dt_start_str, dt_end_str = self.hhmms_from_dts(dt_start, dt_end)
                date_free_sessions.append(dict(
                    dt_start=dt_start,
                    dt_end=dt_end,
                    dt_start_str=dt_start_str,
                    dt_end_str=dt_end_str,
                ))
                dt_start = dt_end

            to_delete_from_date_free_sessions = []

            hall_timetable=dict(hall=hall)

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
                    dt_start__lt=date_end,
                ).order_by('dt_start'):
                dt_start_str, dt_end_str = self.hhmms_from_dts(tt.dt_start, tt.dt_end)
                tt_item = dict(
                    free = False,
                    dt_start=tt.dt_start,
                    dt_end=tt.dt_end,
                    dt_start_str=dt_start_str,
                    dt_end_str=dt_end_str,
                    details=tt.details,
                    creator=tt.creator,
                    html_name_prefix=self.make_html_name_prefix(hall, tt.dt_start, tt.dt_end),
                    dt_created=tt.dt_created,
                )
                if tt.dt_end <= dt_border:
                    tt_item.update(editable=False, past=True)
                    past_sessions.append(tt_item)
                else:
                    editable = bool(
                        user.profile.is_hall_manager() and user == tt.creator or \
                        user.profile.is_hall_admin()
                    )
                    if editable:
                        have_smth_to_edit = True
                    tt_item.update(editable=editable, past=False)
                    future_sessions.append(tt_item)
                    for i, s in enumerate(date_free_sessions):
                       if tt.dt_end <= s['dt_start'] or tt.dt_start >= s['dt_end']:
                           # Конец интервала из базы до начала рассматриваемого: не пересекает
                           # Начало интервала из базы после  рассматриваемого: не пересекает
                           pass
                       else:
                           # Во всех остальных случаях как-то пересекает
                            to_delete_from_date_free_sessions.append(i)

            updated_date_free_sessions = []
            for i, s in enumerate(date_free_sessions):
                if i not in to_delete_from_date_free_sessions:
                    updated_date_free_sessions.append(s)
            editable = bool(user.profile.is_hall_manager() and updated_date_free_sessions)
            if editable:
                have_smth_to_edit = True
            for tt_item in updated_date_free_sessions:
                tt_item.update(
                    free = True,
                    details='',
                    creator=None,
                    html_name_prefix=self.make_html_name_prefix(hall, tt_item['dt_start'], tt_item['dt_end']),
                    editable=editable,
                    dt_created=None,
                )
            future_sessions += updated_date_free_sessions
            future_sessions.sort(key=lambda k: k['dt_start'])

            hall_timetable.update(timetable=past_sessions + future_sessions)            
            hall_timetables.append(hall_timetable)

        # Подсчитать число пустых строк, которые надо добавить в таблицы,
        # чтоб они не налазили друг на друга при уменьшении ширины экрана
        #
        # Вычислим максимум строк в залах. Минимально хотя бы одна будет (ничего не было)
        #
        max_rows = 1
        for hall in hall_timetables:
            cur_len = len(hall['timetable'])
            if cur_len > max_rows:
                max_rows = cur_len
        for hall in hall_timetables:
            cur_len = len(hall['timetable']) or 1
            num_added_rows = max_rows - cur_len
            empty_rows = ''
            for i in range(num_added_rows):
                empty_rows += '*'
            hall.update(empty_rows=empty_rows)
        result = dict(
            have_smth_to_edit=have_smth_to_edit,
            hall_timetables=hall_timetables,
        )
        return result

class HallsTimeTableView(UghOrLoruRequiredMixin, HallsTimeTableMixin, View):
    template_name = 'hall_timetable.html'

    # После этого выводим расчет на завтра по умолчанию
    #
    TOMORROW_BEGINS_AT = '13:00'

    # Чтоб в template & view были одни и те же обозначения для имен html
    # элементов и действий по ним
    #
    S = dict(
        FREE="free",
        BOOK="book",
        DETAILS="details",
        DETAILS_OLD="details_old",
    )

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
            S=self.S,
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
        format_date = formats.get_format("SHORT_DATE_FORMAT", lang=settings.LANGUAGE_CODE)
        if not self.request.GET and self.all_halls_pks:
            # Сразу выведем все залы за self.get_default_date()
            #
            date = self.get_default_date()
            date_str = date_format(date, format=format_date)
            get_params = '?hall_date_from=%s&%s' % (
                date_str,
                '&'.join(['halls=%s' %  pk for pk in self.all_halls_pks])
            )
            return redirect(reverse('halls_timetable') + get_params)
        date = context_data.get('date')
        if date:
            context_data.update(
                date_str=date_format(date, format=format_date),
            )
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        if not self.request.user.profile.is_hall_manager():
            return HttpResponseForbidden()
        post_errors = []

        S = self.S
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

        booked_s = [p[0:-len(S['BOOK'])-2] for p in request.POST if p.endswith(S['BOOK'])]
        for tt_item in booked_s:
            try:
                hall_pk, t_start, t_end = tt_item.split('__')
                hall = Hall.objects.get(pk=hall_pk)
                dt_start, dt_end = self.mk_interval(t_start, t_end)
            except (ValueError, Hall.DoesNotExist,):
                raise Http404
            details = request.POST.get("%s__%s" % (tt_item, S['DETAILS'],), '')
            htt, created_ = HallTimeTable.objects.get_or_create(
                hall=hall,
                dt_start=dt_start,
                dt_end=dt_end,
                defaults=dict(
                    creator=request.user,
                    details=details,
            ))
            s_start, s_end = self.hhmms_from_dts(dt_start, dt_end)
            if created_:
                write_log(self.request, hall, _("Назначено время, %s - %s%s") % (
                    s_start,
                    s_end,
                    '. %s' % details if details else '',
                ))
            else:
                post_errors.append(
                    _("%s, %s - %s : кто-то до вас уже забронировал это время" % (
                    hall.title,
                    s_start,
                    s_end,
                )))

        free_s = [p[0:-len(S['FREE'])-2] for p in request.POST if p.endswith(S['FREE'])]
        for tt_item in free_s:
            try:
                hall_pk, t_start, t_end = tt_item.split('__')
                hall = Hall.objects.get(pk=hall_pk)
                dt_start, dt_end = self.mk_interval(t_start, t_end)
            except (ValueError, Hall.DoesNotExist,):
                raise Http404
            HallTimeTable.objects.filter(
                hall=hall,
                dt_start=dt_start,
                dt_end=dt_end,
            ).delete()
            s_start, s_end = self.hhmms_from_dts(dt_start, dt_end)
            write_log(self.request, hall, _("Отменено время, %s - %s") % (
                s_start,
                s_end,
            ))

        details_s = [p[0:-len(S['DETAILS'])-2] for p in request.POST if p.endswith(S['DETAILS'])]
        for tt_item in details_s:
            if tt_item in free_s or tt_item in booked_s:
                continue
            details_old = request.POST.get("%s__%s" % (tt_item, S['DETAILS_OLD'],))
            details_new = request.POST.get("%s__%s" % (tt_item, S['DETAILS'],))
            if details_old is not None and details_new is not None and \
               details_new != details_old:
                try:
                    hall_pk, t_start, t_end = tt_item.split('__')
                    hall = Hall.objects.get(pk=hall_pk)
                    dt_start, dt_end = self.mk_interval(t_start, t_end)
                except (ValueError, Hall.DoesNotExist,):
                    raise Http404
                htt_qs = HallTimeTable.objects.filter(
                    hall=hall,
                    dt_start=dt_start,
                    dt_end=dt_end,
                )
                s_start, s_end = self.hhmms_from_dts(dt_start, dt_end)
                try:
                    htt = htt_qs[0]
                    if htt.details != details_old:
                        post_errors.append(
                            _("%s, %s - %s : кто-то до вас уже изменил примечание, которое подправили и вы" % (
                            hall.title,
                            s_start,
                            s_end,
                        )))
                        continue
                    htt_qs.update(details=details_new)
                    s_start = datetime.datetime.strftime(dt_start, '%H:%M')
                    s_end = datetime.datetime.strftime(dt_end, '%H:%M')
                    write_log(self.request, hall, _("Назначенное время, %s - %s, изменено описание") % (
                        s_start,
                        s_end,
                    ))
                except IndexError:
                    post_errors.append(
                        _("%s, %s - %s : кто-то до вас уже удалил время, в котором вы изменили примечание" % (
                        hall.title,
                        s_start,
                        s_end,
                    )))
                    continue

        get_params = '?' + get_params
        if post_errors:
            post_errors = '~'.join(post_errors)
            post_errors = base64.urlsafe_b64encode(post_errors.encode('utf8')).decode('utf8')
            post_errors = post_errors.replace('=', '%3D')
            get_params += '&post_errors=%s' % post_errors
        return redirect(reverse('halls_timetable') + get_params)

halls_timetable_view = HallsTimeTableView.as_view()

class HallsTimeView(UghOrLoruRequiredMixin, HallsTimeTableMixin, View):
    template_name = 'hall_time.html'

    def get_default_date(self):
        """
        Дата по умолчанию. Сегодня.
        """
        result = datetime.date.today()
        return result

    def get_context_data(self):
        context = dict()

        self.all_halls_pks = []
        for hall in Hall.objects.filter(org=self.request.user.profile.org, is_active=True):
            self.all_halls_pks.append(str(hall.pk))
        if not self.all_halls_pks:
                context.update(
                    no_halls_in_system=_('В организации нет залов. Обратитесь к администратору'),
                )
                return context

        form=self.get_form()
        date = None
        if form.is_valid() and form.data:
            date = form.cleaned_data.get('hall_date_from')
            context.update(self.get_timetable(date, self.all_halls_pks))

        today_tomorrow = None
        if date:
            today = datetime.date.today()
            if date == today:
                today_tomorrow = _('сегодня')
            elif date - today == datetime.timedelta(days=1):
                today_tomorrow = _('завтра')

        context.update(
            date=date,
            today_tomorrow=today_tomorrow,
            is_hall_manager = self.request.user.profile.is_hall_manager(),
            form=form,
        )
        return context

    def get_form(self):
        data = self.request.GET
        form = HallTimeForm(data=data or None)
        if not data:
            form.initial['hall_date_from'] = self.get_default_date()
        return form

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data()
        format_date = formats.get_format("SHORT_DATE_FORMAT", lang=settings.LANGUAGE_CODE)
        if not self.request.GET and self.all_halls_pks:
            date = self.get_default_date()
            date_str = date_format(date, format=format_date)
            get_params = '?hall_date_from=%s' % (
                date_str,
            )
            return redirect(reverse('halls_time') + get_params)
        date = context_data.get('date')
        if date:
            context_data.update(
                date_str=date_format(date, format=format_date),
            )
        return render(request, self.template_name, context_data)

halls_time_view = HallsTimeView.as_view()
