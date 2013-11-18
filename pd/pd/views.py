# -*- coding: utf-8 -*-
import os
import re
import mimetypes

from django.http import Http404, HttpResponse
from django.views.generic.list import ListView
from django.views.generic.edit import BaseFormView
from django.shortcuts import get_object_or_404
from django.db.models.loading import get_model

from django.conf import settings

class PaginateListView(ListView):
    """
    Общий класс для постраничного табличного просмотра
    
    * В классе-потомке должны быть определены методы:
        def get_form(self)
    
    * В классе-потомке могут быть переопределены переменные, см. ниже:
    """
    DISPLAY_OPTIONS = ['page', 'print']
    
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

def media_xsendfile(request, path, document_root):
    filename = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(filename):
        raise Http404

    server_software = request.META.get('SERVER_SOFTWARE')
    if server_software and re.search(r'apache', server_software, flags=re.I):
        # Нижеследующее отработает только под сервером Apache с mod_xsendfile
        #
        # Например: death-certificates/2013/11/06/5998/1376137215179.jpg
        # Должны получить две группы: 'death-certificates' и  '5998'
        #
        m= re.search(r'^/?([^/]+).*/(\d+)/[^/]+$',path)
        if not m:
            raise Http404
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
        # Файлы остальных обхъектов пока отдаем без проверки, имеет ли к ним доступ
        # пользователь request.user
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
