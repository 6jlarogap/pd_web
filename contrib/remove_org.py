# -*- coding: utf-8 -*-

# remove_org.py,        удалить организацию, только что зарегистрированную,
#                       со всеми ее "хвостами".
#                       Если организация уже насоздавала заказы,
#                       захоронения, то эта процедура не пройдет!
#
# Запуск из ./manage.py shell :
# execfile('/path/to/remove_org.py')

ORG_PK=259

from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User

from billing.models import Wallet, Rate
from users.models import Org, BankAccount, Profile, OrgCertificate, OrgContract, \
                         Store
from logs.models import Log

@transaction.atomic
def main(pk=ORG_PK):
    
    def rec_deleted(n):
        print '  %d recs deleted' % n
    
    def clean_logs(model, obj):
        ct = ContentType.objects.get_for_model(model)
        print 'Log recs for %s.%s' % (ct.app_label, ct.model, )
        ll = Log.objects.filter(ct=ct, obj_id=obj.pk)
        for l in ll:
            l.delete()
        rec_deleted(ll.count())
    
    print 'Remove org with pk=%s' % pk
    print ''

    org = Org.objects.get(pk=pk)
    print 'Org name is %s' % org.name
    print ''

    print 'Scanning models'
    print ''

    print 'Rate:'
    rr = Rate.objects.filter(wallet__org=org)
    for r in rr:
        r.delete
    rec_deleted(rr.count())
    
    print 'Wallet:'
    ww = Wallet.objects.filter(org=org)
    for w in ww:
        w.delete
    rec_deleted(ww.count())
    
    print 'OrgCertificate:'
    oo = OrgCertificate.objects.filter(org=org)
    for o in oo:
        o.delete()
    rec_deleted(oo.count())

    print 'OrgContract:'
    oo = OrgContract.objects.filter(org=org)
    for o in oo:
        o.delete()
    rec_deleted(oo.count())

    print 'BankAccount:'
    bb = BankAccount.objects.filter(organization=org)
    for b in bb:
        b.delete()
    rec_deleted(bb.count())
    
    if org.off_address:
        print 'Org.off_address delete'
        addr = org.off_address
        org.off_address = None
        org.save()
        addr.delete()

    print ''
    print 'Stores'
    for s in Store.objects.filter(loru=org):
        print u' Store: %s' % s.name
        if s.address:
            print '  delete its addres'
            addr = s.address
            s.address = None
            addr.delete()
        print ' delete the store'
        s.delete()
    else:
        print ' no stores found'

    print 'Profiles & Users'
    print ''
    for p in Profile.objects.filter(org=org):
        print u'Profile: %s' % p.full_name()
        clean_logs(Profile, p)

        u = p.user
        print 'User: %s' % u.username
        clean_logs(User, u)
        print ' Clean all log records created by %s' % u.username
        ll = Log.objects.filter(user=u)
        for l in ll:
            l.delete()
        print '  %d log recs deleted' % ll.count()
        print ' User %s: delete' % u.username
        u.delete()
        print u' Profile %s: delete' % p.full_name()
        p.delete()
    
    clean_logs(Org, org)
    print 'And FINALLY... deleting the organization'
    org.delete()
    transaction.commit()

main()
