import datetime, base64, os, tempfile
from urllib.parse import parse_qs

from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.views.generic.edit import UpdateView
from django.http import Http404, HttpResponseForbidden
from django.contrib import messages
from django.urls import reverse
from django.utils import formats
from django.utils.translation import gettext as _
from django.utils.formats import date_format

from django.conf import settings

from halls.forms import HallFormset, HallTimeTableForm, HallTimeForm, HallWeeklyFormset, HallsExportForm

from logs.models import write_log
from halls.models import Hall, HallTimeTable, HallWeekly
from users.models import Org, Profile, is_ugh_user, is_loru_user
from users.views import UghOrLoruRequiredMixin

from pd.views import FormInvalidMixin, ManualEncodedCsvMixin

class HallsEdit(UghOrLoruRequiredMixin, View):
    template_name = 'halls.html'

    def get_formset(self, instance=None):
        if not instance:
            instance=self.get_object()
        return HallFormset(request=self.request, data=self.request.POST or None, instance=instance)

    def get_object(self):
        return self.request.user.profile.org

    def get_context_data(self, *args, **kwargs):
        formset = self.get_formset()
        for f in formset.forms:
            if f.instance.pk:
                time_schedule = f.instance.time_schedule()
            else:
                h = Hall()
                time_schedule = h.time_schedule()
            f.time_schedule = time_schedule
        return dict(formset=formset)

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

class HallsTimeEdit(UghOrLoruRequiredMixin, View):
    template_name = 'halls_time_edit.html'

    def get_formset(self, instance=None):
        if not instance:
            instance=self.get_object()
        return HallWeeklyFormset(request=self.request, data=self.request.POST or None, instance=instance)

    def get_object(self):
        try:
            return Hall.objects.get(pk=self.instance_pk, org=self.request.user.profile.org)
        except Hall.DoesNotExist:
            raise Http404

    def get_context_data(self,  *args, **kwargs):
        formset = self.get_formset()
        return dict(formset=formset)

    def get(self, request, pk, *args, **kwargs):
        self.instance_pk = pk
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, pk, *args, **kwargs):
        self.instance_pk = pk
        if not (request.user.profile.is_loru() or request.user.profile.is_admin()):
            return HttpResponseForbidden()
        formset = self.get_formset()
        if formset.is_valid():
            for f in formset.forms:
                if f.instance.pk:
                        f.save()
            return redirect(reverse('halls_time_edit', kwargs=dict(pk=pk)))
        else:
            messages.error(request, _("Обнаружены ошибки"))
            return self.get(request, pk, *args, **kwargs)

halls_time_edit_view = HallsTimeEdit.as_view()

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
        dow = date.isoweekday()
        date_start = datetime.datetime(
            date.year, date.month, date.day, 0, 0
        )
        date_end = date_start + datetime.timedelta(days=1)

        for hall_pk in halls_pks:
            hall = Hall.objects.get(pk=hall_pk)
            try:
                hall_weekly = HallWeekly.objects.get(hall=hall, dow=dow)
                is_dayoff = hall_weekly.is_dayoff
            except HallWeekly.DoesNotExist:
                is_dayoff = True
            hall_interval_timedelta = datetime.timedelta(seconds=hall_weekly.interval * 60)
            hall_time_start_str = hall_weekly.time_start
            hall_start = datetime.datetime.strptime(hall_time_start_str, "%H:%M")
            hall_start = datetime.datetime(
                year=date.year, month=date.month, day=date.day,
                hour=hall_start.hour, minute=hall_start.minute,
            )
            hall_time_end_str = hall_weekly.time_end
            if hall_time_end_str == '24:00':
                hall_end = date_end
            else:
                hall_end = datetime.datetime.strptime(hall_time_end_str, "%H:%M")
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
            if not is_dayoff:
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

            hall_timetable=dict(
                hall=hall,
                is_dayoff=is_dayoff,
                hall_time_start_str=hall_time_start_str,
                hall_time_end_str=hall_time_end_str,
            )

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
                    kind_burn=tt.kind == HallTimeTable.BOOK_BURN,
                    kind_move=tt.kind == HallTimeTable.BOOK_MOVE,
                    kind_display = tt.get_kind_display(),
                )
                if tt.dt_end <= dt_border:
                    tt_item.update(
                        editable=False,
                        deletable=False,
                        editable_or_deletable=False,
                        past=True,
                    )
                    past_sessions.append(tt_item)
                else:
                    editable = bool(
                        user.profile.is_hall_manager() and user == tt.creator or \
                        user.profile.is_hall_admin()
                    )
                    deletable = user.profile.is_hall_manager()
                    if editable or deletable:
                        have_smth_to_edit = True
                    tt_item.update(
                        editable=editable,
                        deletable=deletable,
                        editable_or_deletable=editable or deletable,
                        past=False,
                    )
                    future_sessions.append(tt_item)
                    for i, s in enumerate(date_free_sessions):
                       if tt.dt_end <= s['dt_start'] or tt.dt_start >= s['dt_end']:
                           # Конец интервала из базы до начала рассматриваемого: не пересекает
                           # Начало интервала из базы после  рассматриваемого: не пересекает
                           pass
                       else:
                           # Во всех остальных случаях как-то пересекает
                            to_delete_from_date_free_sessions.append(i)

            # Есть ли что-то по залу редактировать: бронировать
            # или убирать бронирование? В date_free_sessions
            # находятся все промежутки, которые после текущего времени можно назначить
            # или снять. Если такие есть, а есть что-то назначенное, даже после окончания
            # времени работы или в выходной (future_sessions), то пусть редактируют
            #
            editable = bool(user.profile.is_hall_manager() and (date_free_sessions or future_sessions))
            if editable:
                have_smth_to_edit = True
            updated_date_free_sessions = []
            for i, s in enumerate(date_free_sessions):
                if i not in to_delete_from_date_free_sessions:
                    updated_date_free_sessions.append(s)
            for tt_item in updated_date_free_sessions:
                tt_item.update(
                    free = True,
                    details='',
                    creator=None,
                    html_name_prefix=self.make_html_name_prefix(hall, tt_item['dt_start'], tt_item['dt_end']),
                    editable=editable,
                    deletable=False,
                    editable_or_deletable=editable,
                    dt_created=None,
                )
            future_sessions += updated_date_free_sessions
            future_sessions.sort(key=lambda k: k['dt_start'])

            hall_timetable.update(
                have_smth_to_edit=editable,
                timetable=past_sessions + future_sessions,
            )
            hall_timetables.append(hall_timetable)

        # Подсчитать число пустых строк, которые надо добавить в таблицы,
        # чтоб они не налазили друг на друга при уменьшении ширины экрана
        #
        # Вычислим максимум строк в залах. Минимально хотя бы одна будет (ничего не было или выходной)
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
        BOOK_BURN= HallTimeTable.BOOK_BURN,
        BOOK_MOVE= HallTimeTable.BOOK_MOVE,
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

        booked_all = [
            p[0:-len(S['BOOK_BURN'])-2] for p in request.POST \
                if p.endswith(S['BOOK_BURN']) or p.endswith(S['BOOK_MOVE'])
        ]
        booked_with_kind = []
        booked_with_kind.extend([
            (p[0:-len(S['BOOK_BURN'])-2], S['BOOK_BURN']) for p in request.POST \
                if p.endswith(S['BOOK_BURN'])
        ])
        booked_with_kind.extend([
            (p[0:-len(S['BOOK_MOVE'])-2], S['BOOK_MOVE']) for p in request.POST \
                if p.endswith(S['BOOK_MOVE'])
        ])

        for tt_item_kind in booked_with_kind:
            tt_item = tt_item_kind[0]
            kind = tt_item_kind[1]
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
                    kind=kind,
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
            if tt_item in free_s or tt_item in booked_all:
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

class HallsExportView(FormInvalidMixin, ManualEncodedCsvMixin, UpdateView):

    template_name = 'halls_export.html'
    model = Profile
    form_class = HallsExportForm

    def get_object(self):
        user = self.request.user
        if not is_ugh_user(user) or is_loru_user(user):
            raise Http404
        return self.request.user.profile

    def get_form(self, *args, **kwargs):
        form = super(HallsExportView, self).get_form(*args, **kwargs)
        halls_qs = Hall.objects.filter(
            org=self.request.user.profile.org,
            is_active=True,
        ).order_by('title')
        choices = list()
        hh = list()
        for h in halls_qs:
            hh.append(h.pk)
            choices.append((h.pk, h.title,))
        form.fields['halls'].choices = choices
        form.fields['halls'].widget.attrs.update({'size': str(min(halls_qs.count()+1, 15))})
        form.initial['halls'] = hh
        form.initial['date_from'] = datetime.date.today()
        return form

    def form_valid(self, form):
        org = self.request.user.profile.org
        date_from = form.cleaned_data['date_from']
        dow = date_from.isoweekday()
        date_from_plus_1 = date_from + datetime.timedelta(days=1)
        halls_pks = form.cleaned_data['halls']

        halls_by_pk = dict()
        n = 0
        for hall in Hall.objects.filter(pk__in=halls_pks).order_by('title'):
            if hall.org != org:
                raise PermissionDenied
            n += 1
            if form.cleaned_data['titleby'] == HallsExportForm.TITLE_BY_NUMBER:
                title = _('Зал № %s') % n
            else:
                title = self.correct_field(hall.title)
            halls_by_pk[str(hall.pk)] = dict(n=n, title=title)

        output = list()
        htt = dict()
        qs_tt = HallTimeTable.objects.filter(
            hall__pk__in=halls_pks,
            dt_start__gte=date_from,
            dt_start__lt=date_from_plus_1,
        ).select_related('hall')
        for halltimetable in qs_tt:
            details = self.correct_field(halltimetable.details)
            if not details:
                details = _('%s: не указано кого') % halltimetable.get_kind_display()
            time_start = halltimetable.dt_start.strftime('%H:%M')
            if halltimetable.dt_start.date() < halltimetable.dt_end.date():
                time_end = '24:00'
            else:
                time_end = halltimetable.dt_end.strftime('%H:%M')
            n_hall = halls_by_pk[str(halltimetable.hall.pk)]['n']
            title = halls_by_pk[str(halltimetable.hall.pk)]['title']
            htt[
                (
                    time_start,
                    n_hall,
                )
            ] = dict(
                details=details,
                time_end=time_end,
                title=title
            )
            output.append((
              time_start,
              time_end,
              n_hall,
              details,
              title
            ))

        qs_weekly = HallWeekly.objects.filter(
            hall__pk__in=halls_pks,
            dow=dow,
            is_dayoff=False,
        ).select_related('hall')

        for hallweekly in qs_weekly:
            hall_interval_timedelta = datetime.timedelta(seconds=hallweekly.interval * 60)
            n_hall = halls_by_pk[str(hallweekly.hall.pk)]['n']

            hall_time_start_str = hallweekly.time_start
            hall_start = datetime.datetime.strptime(hall_time_start_str, "%H:%M")
            hall_start = datetime.datetime(
                year=date_from.year, month=date_from.month, day=date_from.day,
                hour=hall_start.hour, minute=hall_start.minute,
            )
            hall_end_plus_1 = datetime.datetime(
                year=date_from_plus_1.year, month=date_from_plus_1.month, day=date_from_plus_1.day,
                hour=0, minute=0,
            )
            hall_time_end_str = hallweekly.time_end
            if hall_time_end_str == '24:00':
                hall_end = hall_end_plus_1
            else:
                hall_end = datetime.datetime.strptime(hall_time_end_str, "%H:%M")
                hall_end = datetime.datetime(
                    year=date_from.year, month=date_from.month, day=date_from.day,
                    hour=hall_end.hour, minute=hall_end.minute,
                )
            # foolproof
            hall_end = min(hall_end, hall_end_plus_1)
            while hall_start < hall_end:
                h_start = hall_start
                t_start = h_start.strftime('%H:%M')
                h_end = h_start + hall_interval_timedelta
                hall_start = h_end
                if not htt.get((t_start, n_hall, )):
                    if h_end.date() > h_start.date():
                        t_end = '24:00'
                    else:
                        t_end = h_end.strftime('%H:%M')
                    output.append((
                        t_start,
                        t_end,
                        halls_by_pk[str(hallweekly.hall.pk)]['n'],
                        '-',
                        halls_by_pk[str(hallweekly.hall.pk)]['title']
                    ))

        # Порядок элементов в tuple, список которых будем сортировать и
        # потом заносить в выходной файл
        TT_START = 0
        TT_END = 1
        TT_HALL_NUMBER = 2
        TT_DETAILS = 3
        TT_HALL_TITLE = 4
        output.sort(key=lambda x: (x[TT_START], x[TT_END], x[TT_HALL_NUMBER],))

        if output:
            media_path = os.path.join('tmp', 'export', 'halls', '%s' % org.pk, )
            export_path = os.path.join(settings.MEDIA_ROOT, media_path)
            try:
                os.makedirs(export_path)
            except OSError:
                pass
            temp_dir = tempfile.mkdtemp(dir=export_path)
            temp_dir_name = os.path.basename(temp_dir)
            now = datetime.datetime.now()
            dt_now_str = datetime.datetime.strftime(now, '%Y%m%d%H%M%S')
            date_from_str = datetime.datetime.strftime(date_from, '%Y%m%d')
            fname = 'halls-for-%s-got-at-%s.csv' % (date_from_str, dt_now_str, )
            path_fname = os.path.join(temp_dir, fname)
            with open(path_fname, 'wb') as f:
                t_start_prev = output[0][TT_START]
                t_end_prev = output[0][TT_END]
                for s in output:
                    if s[TT_START] != t_start_prev or s[TT_END] != t_end_prev:
                        t_start_prev = s[TT_START]
                        t_end_prev = s[TT_END]
                        f.write(self.LINE_END.encode(self.ENCODING))
                    f.write(self.encode_(self.SEPARATOR.join((
                        '%s - %s' % (s[TT_START], s[TT_END],),
                        s[TT_DETAILS],
                        s[TT_HALL_TITLE],
                    ))))
            return redirect(os.path.join(settings.MEDIA_URL, media_path, temp_dir_name, fname))
        else:
            messages.info(self.request, _('Не найдены данные для экспорта расписаний за указанную дату'))
            return self.get(self.request, *self.args, **self.kwargs)

halls_export_view = HallsExportView.as_view()
