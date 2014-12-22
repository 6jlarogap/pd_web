# -*- coding: utf-8 -*-
import os
import re
import mimetypes

from django.http import Http404, HttpResponse, UnreadablePostError
from django.views.generic.list import ListView
from django.views.generic.edit import BaseFormView
from django.shortcuts import get_object_or_404
from django.db.models.loading import get_model
from django.utils.translation import ugettext as _
from django.contrib import messages

from django.conf import settings

from restthumbnails.views import ThumbnailView

def is_user_accessible(request, user):
    """
    Имеет ли доступ request.user к данным user, например, к его фото
    """
    result = False
    if user == request.user:
        result = True
    else:
        Profile = get_model('users', 'Profile')
        try:
            user.profile
            if user.profile.org == request.user.profile.org:
                result = True
        except (AttributeError, Profile.DoesNotExist,):
                pass
    return result

class OurThumbnailView(ThumbnailView):

    def get(self, request, *args, **kwargs):
        from restthumbnails import exceptions

        m= re.search(r'^/?thumb/([^/]+).*/(\d+)/[^/]+/',request.path)
        if m:
            what = m.group(1)
            pk = m.group(2)
            if what == 'place-photos':
                try:
                    place_photo = get_model('burials', 'PlacePhoto').objects.filter(pk=pk)[0]
                    if not place_photo.is_accessible(request.user):
                        raise Http404
                except IndexError:
                    raise Http404
            elif what == 'user-photos':
                # Фото пользователя может смотреть либо он сам, либо любой из его организации
                try:
                    user = get_model('auth', 'User').objects.filter(pk=pk)[0]
                    if not is_user_accessible(request, user):
                        raise Http404
                except IndexError:
                    raise Http404

        elif re.search(settings.ANONYMOUS_URLS_REGEX, request.path):
            pass
        else:
            raise Http404
        try:
            return super(OurThumbnailView, self).get(request, *args, **kwargs)
        except exceptions.SourceDoesNotExist:
            raise Http404

class PaginateListView(ListView):
    """
    Общий класс для постраничного табличного просмотра
    
    * В классе-потомке должны быть определены методы:
        def get_form(self)
    
    * В классе-потомке могут быть переопределены переменные, см. ниже:
    """
    DISPLAY_OPTIONS = ['page', 'print', 'sort']
    
    # Параметр get-запроса для сортировки по умолчанию
    # (именно get-запроса, а поля из таблицы!)
    SORT_DEFAULT = '-dt'
    
    def get_paginate_by(self, queryset):
        if self.request.GET.get('print'):
            return None
        try:
            return int(self.request.GET.get('per_page'))
        except (TypeError, ValueError):
            return 25

    def get_context_data(self, **kwargs):
        data = super(PaginateListView, self).get_context_data(**kwargs)
        get_for_paginator = u'&'.join([u'%s=%s' %  (k, v) for k,v in self.request.GET.items() if k not in self.DISPLAY_OPTIONS])
        sort = self.request.GET.get('sort', self.SORT_DEFAULT)
        data.update(form=self.get_form(), GET_PARAMS=get_for_paginator, sort=sort)
        return data

class RequestToFormMixin(BaseFormView):
    """
    Для view, отсылающего в свою форму request
    
    Форма этого view дожна иметь __init__(self, request, *args, *kwargs)
    и вызывать super(форма, self).__init__((self, *args, *kwargs)
    """

    def get_form_kwargs(self):
        data = super(RequestToFormMixin, self).get_form_kwargs()
        data['request'] = self.request
        return data

def is_url_accessible_anonymous(request):
    """
    Давать ли доступ анонимному пользователю?
    """
    result = False

    # Подходит под:
    # * /media/death-certificates/2013/11/06/5998/1376137215179.jpg
    # * /thumb/place-photos/2014/04/21/101/1398082582212.jpg/500x300~crop~12.jpg
    #
    m= re.search(r'^/?(?:thumb|media)/([^/]+).*/(\d+)/[^/]+/?', request.path)
    if m:
        what = m.group(1)
        pk = m.group(2)
        if what == 'place-photos':
            place_photo = get_model('burials', 'PlacePhoto').objects.filter(pk=pk)[0]
            result = place_photo.is_accessible_anonymous()
    return result

def media_xsendfile(request, path, document_root):
    filename = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(filename):
        raise Http404

    server_software = request.META.get('SERVER_SOFTWARE')
    if server_software and re.search(r'apache', server_software, flags=re.I):
        # Нижеследующее отработает только под сервером Apache с mod_xsendfile
        #
        # Например: death-certificates/2013/11/06/5998/1376137215179.jpg
        # Или:      org-data/<org_pk>/org-data.zip
        # Должны получить две группы: 'death-certificates' и  '5998'
        #
        m = re.search(r'^/?([^/]+).*/(\d+)/[^/]+$',path)
        if m:
            what = m.group(1)
            pk = m.group(2)
            if what == 'death-certificates':
                try:
                    burial = get_model('burials', 'Burial').objects.filter(deadman__pk=pk)[0]
                    if not burial.is_accessible(request.user):
                        raise Http404
                except IndexError:
                    raise Http404
            elif what == 'bfiles':
                burial = get_object_or_404(get_model('burials', 'Burial'), pk=pk)
                if not burial.is_accessible(request.user):
                    raise Http404
            elif what == 'place-photos':
                try:
                    place_photo = get_model('burials', 'PlacePhoto').objects.filter(pk=pk)[0]
                    if not place_photo.is_accessible(request.user):
                        raise Http404
                except IndexError:
                    raise Http404
            elif what in ('org-certificates', 'org-contracts', ):
                try:
                    org = get_model('users', 'Org').objects.filter(pk=pk)[0]
                    Profile = get_model('users', 'Profile')
                    if pk != str(request.user.profile.org.pk):
                        raise Http404
                except (IndexError, AttributeError, Profile.DoesNotExist, ):
                    raise Http404
            elif what == 'memory-gallery':
                try:
                    if pk != str(request.user.pk):
                        raise Http404
                except IndexError:
                    raise Http404
            elif what in ('register-profile-scans', 'register-profile-contracts', ):
                try:
                    Profile = get_model('users', 'Profile')
                    if not request.user.profile.is_supervisor():
                        raise Http404
                except (AttributeError, Profile.DoesNotExist, ):
                    raise Http404
            elif what == 'order-results':
                try:
                    order = get_model('orders', 'Order').objects.filter(pk=pk)[0]
                    if not order.is_accessible(request.user):
                        raise Http404
                except IndexError:
                    raise Http404
            elif what == 'user-photos':
                try:
                    user = get_model('auth', 'User').objects.filter(pk=pk)[0]
                    if not is_user_accessible(request, user):
                        raise Http404
                except IndexError:
                    raise Http404
            elif what == 'org-data':
                try:
                    Profile = get_model('users', 'Profile')
                    if pk != str(request.user.profile.org.pk):
                        raise Http404
                except (AttributeError, Profile.DoesNotExist, ):
                    raise Http404
            # Файлы остальных объектов, подпадающих под m, пока отдаем без проверки,
            # имеет ли к ним доступ пользователь request.user
        else:
            # Для товаров, их категорий, поддержки и др.: открыто всем
            if re.search(r'^/?(?:product\-photo|icons|support)/',path):
                pass
            else:
                raise Http404
        response = HttpResponse()
        response['Content-Type'] = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        # Так в любом случае идет предложение или сохранить, или открыть файл, но
        # не открытие его в браузере:
        # response['Content-Disposition']='attachment;filename="%s"' % os.path.basename(filename).encode('utf-8')
        response['X-Sendfile'] = filename
        response['Content-length'] = os.stat(filename).st_size
        return response
    else:
        # А это под ./manage.py, но без всякой проверки доступа к объекту
        #
        from django.views.static import serve
        return serve(request, path, document_root)

class FormInvalidMixin(BaseFormView):
    """
    Типичное сообщение об ошибках, особенно в представлениях с пространными формами
    
    ВНИМАНИЕ: Объект представления должен иметь атрибут self.request !
    """
    def form_invalid(self, form, *args, **kwargs):
        messages.error(self.request, _(u'Обнаружены ошибки, их необходимо исправить'))
        return super(FormInvalidMixin, self).form_invalid(form, *args, **kwargs)

def get_front_end_url(request):
    if settings.FRONT_END_URL:
        result = settings.FRONT_END_URL
        if not result.endswith('/'):
            result += '/'
    else:
        back_end_prefix = settings.BACK_END_PREFIX if settings.BACK_END_PREFIX.endswith('.') \
                                                else settings.BACK_END_PREFIX + '.'
        host = request.get_host()
        result = 'https://' if request.is_secure() else 'http://'
        if host.lower().startswith(back_end_prefix.lower()):
            # ВНИМАНИЕ: заканчиваем на '/'
            result += host[len(back_end_prefix):] + '/'
        else:
            # Затычка. Невозможная ситуация в реальной работе
            result += host + '/'
    return result

def get_host_url(request):
        return u"%s://%s/" % (
            'https' if request.is_secure() else 'http',
            request.get_host(),
        )

class ServiceException(Exception):
    """
    Чтобы не плодить цепочки if (try) else ... if (try) ... else
    
    Пример:
    try:
        if not condition1:
            raise ServiceException('Condition 1 failed')
        try:
            # some code
        except SomeException:
            raise ServiceException('Condition 2 failed')
        # all good, going further
    except ServiceException as excpt:
        print excpt.message
    else:
        # all good
    """
    pass