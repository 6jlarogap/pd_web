# -*- coding: utf-8 -*-

import sys

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from orders.models import ProductCategory

class Command(BaseCommand):
    help = ""

    def handle(self, *args, **kwargs):
        """
        Заполнить категории продуктов по умолчанию
        """
        defaults = (
            _(u'Памятники'),
            _(u'Ограды'),
            _(u'Гробы'),
            _(u'Урны'),
            _(u'Венки'),
            _(u'Цветы искусственные'),
            _(u'Цветы живые'),
            _(u'Цветочницы'),
            _(u'Траурные ленты'),
            _(u'Надмогильные таблички'),
            _(u'Кресты'),
            _(u'Автокатафалки'),
            _(u'Грузчики'),
            _(u'Погребение'),
            _(u'Доставка принадлежностей'),
            _(u'Благоустройство (установка памятника и ограды...)'),
            _(u'Уход/уборка'),
            _(u'Прочие товары'),
            _(u'Прочие услуги'),
        )
        print '*** Filling default Product Categories, if neccessary'
        n_filled = 0
        for c in defaults:
            pc, created_ = ProductCategory.objects.get_or_create(name=c)
            if created_:
                n_filled += 1
        print '*** %d defaults for Product Categories, %d added' % (len(defaults), n_filled, )
