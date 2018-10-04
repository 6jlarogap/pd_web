# -*- coding: utf-8 -*-

# Статистика по кладбищам по фото.
# Исключая колумбарии

# Запуск из ./manage.py shell :
# execfile('/path/to/script_name.py')

UGH_PK = 2

from burials.models import Cemetery, Place, PlacePhoto
from django.db.models.query_utils import Q

q = Q(ugh__pk=UGH_PK) & ~Q(name__icontains=u'колумбари')

for c in Cemetery.objects.filter(q).order_by('name'):
    places = Place.objects.filter(cemetery=c)
    count_places = places.distinct().count()
    count_places_with_photos = places.filter(placephoto__isnull=False).distinct().count()
    count_photos = PlacePhoto.objects.filter(place__cemetery=c).count()
    # percent = round(1.0*count_places_with_photos/count_places, 2)
    print u"%s, всего участков: %s, участков с фото: %s, всего фото участков: %s" % (
        c.name,
        count_places,
        count_places_with_photos,
        count_photos,
    )
