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
            _('Памятники'),
            _('Ограды'),
            _('Гробы'),
            _('Урны'),
            _('Венки'),
            _('Цветы искусственные'),
            _('Цветы живые'),
            _('Цветочницы'),
            _('Траурные ленты'),
            _('Надмогильные таблички'),
            _('Кресты'),
            _('Автокатафалки'),
            _('Грузчики'),
            _('Погребение'),
            _('Доставка принадлежностей'),
            _('Благоустройство (установка памятника и ограды...)'),
            _('Уход/уборка'),
            _('Прочие товары'),
            _('Прочие услуги'),
        )
        print('*** Filling default Product Categories, if neccessary')
        n_filled = 0
        for c in defaults:
            pc, created_ = ProductCategory.objects.get_or_create(name=c)
            if created_:
                n_filled += 1
        print('*** %d defaults for Product Categories, %d added' % (len(defaults), n_filled, ))
