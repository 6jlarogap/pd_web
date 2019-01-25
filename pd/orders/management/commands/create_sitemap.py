# -*- coding: utf-8 -*-

import sys, os, codecs, urllib2, json

from django.core.management.base import BaseCommand
from django.template import loader, Context
from django.db.models.query_utils import Q

from django.conf import settings

from orders.models import Product
from users.models import Org
from geo.models import Country, Location

# Получить несколько sitemap.xml: sitemap_ru.xml, sitemap_by.xml,
# тех доменов, что прописаны в DOMAINS_. Sitemap_??.xml пишутся
# в корень MEDIA каталога, а в конфигурации web сервера прописывается,
# что это http....??/sitemap.xml
# В sitemap_XX.sml записываются опубликованные товары лору и сами
# лору из страны XX или из страны DEFAULT_DOMAIN, если страну
# не удалось вычислить.
# Шаблон sitemap_XX.xml -- get_template('sitemap.xml')
#
# Аргументы:
#   1:  сайт, но без доменного окончания, например, https://pohoronnoedelo,
#       по умолчанию https://pohoronnoedelo. Этот сайт, вместе с доменным
#       суффиксом будет фигурировать в вых. sitemap_XX.xml
#   2:  домен, например, ru, by. Если параметр указан, то
#       вся информация будет в вых sitemap_XX, где XX - указанный домен

DOMAINS_ = dict(
    ru=dict(name=u'Россия', obj_country=None,),
    by=dict(name=u'Беларусь', obj_country=None,),
)
YANDEX_GEOCODE_URL = "http://geocode-maps.yandex.ru/1.x/?geocode=%s,%s&format=json&results=1"
    
class Command(BaseCommand):
    help = "Create sitemap.xml for domains"
    
    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='front-end url-WITHOUT-DOMAIN>, e.g. https://pohoronnoedelo')
        parser.add_argument('domain', type=str, help='domain: ru, by, or all (ru and by)')

    def handle(self, *args, **kwargs):
        url = kwargs['url'].lower()
        domain_ = kwargs['domain'].lower()
        if domain_ == 'all':
            DOMAINS = DOMAINS_
        else:
            if domain_ not in DOMAINS_:
                raise Exception("Domain '%s' is not in supported domains" % domain)
            DOMAINS = { domain_ : DOMAINS_[domain_] }

        q_published = Q(is_public_catalog=True)
        q_suppliers = Q(
            type=Org.PROFILE_LORU,
            profile__user__is_active=True,
        )
        
        # Проверим, чтоб у нас были страны из DOMAINS:
        #
        for domain in DOMAINS:
           DOMAINS[domain]['obj_country'], created_ = Country.objects.get_or_create(
               name=DOMAINS[domain]['name']
           )

        # Заполним страны, в которых организации, по возможности
        #
        for s in Org.objects.filter(q_suppliers,
                 off_address__country__isnull=True,
                 off_address__gps_x__isnull=False,
                 off_address__gps_y__isnull=False,
                 ).order_by('slug').distinct():
            try:
                r = urllib2.urlopen(YANDEX_GEOCODE_URL % (
                    s.off_address.gps_x,
                    s.off_address.gps_y,
                ))
                raw_data = r.read().decode(r.info().getparam('charset') or 'utf-8')
            except (urllib2.HTTPError, urllib2.URLError):
                continue
            try:
                data = json.loads(raw_data)
                country = data['response']['GeoObjectCollection']['featureMember'][0]\
                          ['GeoObject']['metaDataProperty']['GeocoderMetaData']\
                          ['AddressDetails']['Country']
                s.off_address.country = DOMAINS[country['CountryNameCode'].lower()]['obj_country']
                s.off_address.save()
            except (KeyError, ValueError, ):
                continue

        all_countries = [DOMAINS[d]['name'] for d in DOMAINS]
        default_domain = 'ru'
        for domain in DOMAINS:
            if len(DOMAINS) > 1:
                q_domain_products = Q(loru__off_address__country__name=DOMAINS[domain]['name'])
                if domain == default_domain:
                    q_domain_products |= ~Q(loru__off_address__country__name__in=all_countries)
                q_domain_suppliers = Q(off_address__country__name=DOMAINS[domain]['name'])
                if domain == default_domain:
                    q_domain_suppliers |= ~Q(off_address__country__name__in=all_countries)
            else:
                q_domain_products = q_domain_suppliers = Q()

            products = Product.objects.filter(q_published & q_domain_products).distinct()
            suppliers = Org.objects.filter(q_suppliers & q_domain_suppliers).order_by('slug').distinct()
            
            t = loader.get_template('sitemap.xml')
            xml = unicode(t.render({
                'products': products,
                'suppliers': suppliers,
                'url': u"%s.%s/" % (url, domain),
            }))
            
            sitemap = os.path.join(settings.MEDIA_ROOT, 'sitemap_%s.xml' % domain)
            with codecs.open(sitemap, 'w', encoding='utf-8') as f:
                f.write(xml)
