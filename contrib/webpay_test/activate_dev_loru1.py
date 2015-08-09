# -*- coding: utf-8 -*-

# acivate_dev_loru1.py,
#
# "подключить" организацию с пользователем loru1 к webpay,
# т.е. заполнить атрибуты таблицы users.OrgWebPay
#
# Запуск из ./manage.py shell :
# execfile('/path/to/acivate_dev_loru1.py')

USERNAME = 'loru1'

from django.contrib.auth.models import User
from users.models import Profile, Org, OrgWebPay

try:
    user = User.objects.get(username=USERNAME)
    org = user.profile.org
    kwargs = dict(
        wsb_storeid='273526623',
        secret='IJ61ZOiMvtJQ',
        wsb_store=u'Похоронное дело',
        wsb_currency_id='BYR',
        wsb_version="2",
        wsb_test=True,
    )
    orgwebpay, created_ = OrgWebPay.objects.get_or_create(
        org=org,
        defaults=kwargs,
    )
    if not created_:
        OrgWebPay.objects.filter(pk=orgwebpay.pk).update(**kwargs)
        print u"FYI: WebPay parms for %s were already issued. Replacing them" % org.name
    print 'SUCCESS'
except User.DoesNotExist:
    print u'ERROR: no such user: %s' % USERNAME
except (AttributeError, Profile.DoesNotExist,):
    print u'ERROR: user: %s has no orgatization' % USERNAME
