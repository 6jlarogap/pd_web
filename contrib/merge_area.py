# coding=utf-8

# Перенести участок с одного кладбища на другое,
# удалить этот единственный участок
# с прежнего кладбища

from django.db import models, transaction
from django.contrib.contenttypes.models import ContentType

from users.models import Org, Profile
from logs.models import Log
from burials.models import Burial, Cemetery, Area, Place

@transaction.atomic
def main():
    ugh = Org.objects.get(pk=394)
    print u"OMS: %s" % ugh

    cemetery_old = Cemetery.objects.get(ugh=ugh, name=u'Бездомные люди  кладбище Оползневое')
    print u"Cemetery old: %s" % cemetery_old
    area_old = Area.objects.get(cemetery=cemetery_old, name=u'Бездомные-1')
    print u"Area old: %s" % area_old

    cemetery_new = Cemetery.objects.get(ugh=ugh, name=u'Оползневое')
    print u"Cemetery new: %s" % cemetery_new

    print 'Area.objects.filter(cemetery=cemetery_old).update(cemetery=cemetery_new)'
    n = Area.objects.filter(cemetery=cemetery_old).update(cemetery=cemetery_new)
    print u'%s area updated' % n

    print 'Place.objects.filter(cemetery=cemetery_old).update(cemetery=cemetery_new)'
    n = Place.objects.filter(cemetery=cemetery_old).update(cemetery=cemetery_new)
    print u'%s places updated' % n

    print 'Burial.objects.filter(cemetery=cemetery_old).update(cemetery=cemetery_new)'
    n = Burial.objects.filter(cemetery=cemetery_old).update(cemetery=cemetery_new)
    print u'%s burials updated' % n

    print 'Profile.objects.filter(cemetery=cemetery_old).update(cemetery=cemetery_new)'
    n = Profile.objects.filter(cemetery=cemetery_old).update(cemetery=cemetery_new)
    print u'%s profiles updated' % n
    
    print 'for p in Profile.objects.filter(cemeteries=cemetery_old):'
    print '   p.cemeteries.remove(cemetery)'
    count = 0
    for p in Profile.objects.filter(cemeteries=cemetery_old):
        count +=1
        p.cemeteries.remove(cemetery_old)
    print "%s profiles with assigned cemetery_old updated" % count

    print 'ct = ContentType.objects.get(app_label="burials", model="cemetery")'
    print 'Log.objects.filter(ct=ct, obj_id=cemetery_old.pk).delete()'
    ct = ContentType.objects.get(app_label="burials", model="cemetery")
    log_recs = Log.objects.filter(ct=ct, obj_id=cemetery_old.pk)
    log_recs_count = log_recs.count()
    log_recs.delete()
    print u'%s log records of cemetery_old deleted' % log_recs_count
    
    print u'Removing cemetery_old: %s' % cemetery_old
    cemetery_old.delete()
    print 'OK'

main()
