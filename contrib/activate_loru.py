# -*- coding: utf-8 -*-

# acivate_loru.py,      подключить нового пользователя,
#                       сделав его активным к существующему
#                       ЛОРУ
#
# Запуск из ./manage.py shell :
# execfile('/path/to/acivate_loru.py')

LORU_NAME = u'Рит_комп19'

LOGIN_NAME = u'ivanov'
PASSWORD = u'SECRET'

USER_LAST_NAME = u'Иванов'
USER_FIRST_NAME = u'Иван'
USER_MIDDLE_NAME = u'Иванович'

from users.models import Profile, Org
from django.contrib.auth.models import User
from django.db import IntegrityError

try:
    loru = Org.objects.get(
        type=Org.PROFILE_LORU,
        name=LORU_NAME,
    )
    user = User.objects.create(
        username=LOGIN_NAME,
        is_active=True,
    )
    user.set_password(PASSWORD)
    user.save()
    profile = Profile.objects.create(
        user=user,
        org=loru,
        user_last_name=USER_LAST_NAME,
        user_first_name=USER_FIRST_NAME,
        user_middle_name=USER_MIDDLE_NAME,
    )
    print 'SUCCESS'
except Org.DoesNotExist:
    print u'ERROR: no such LORU'
except Org.MultipleObjectsReturned:
    print u'ERROR: multiple lorus with this name'
except IntegrityError:
    print u'ERROR: username %s already exists' % LOGIN_NAME
