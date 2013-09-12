# -*- coding: utf-8 -*-
from django.views.generic.list import ListView

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
