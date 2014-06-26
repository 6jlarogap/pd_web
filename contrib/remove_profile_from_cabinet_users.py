# -*- coding: utf-8 -*-

# remove_profile_from_cabinet_users.py,

# Кое-что не учли, и у кабинетчиков, кроме customerprofile,
# появились еще и profiles. Надо исправлять.
#
# Запуск из ./manage.py shell :
# execfile('/path/to/remove_profile_from_cabinet_users.py')

from django.db import IntegrityError
from django.contrib.auth.models import User

from users.models import Profile, CustomerProfile, is_cabinet_user

count_w_profile = count_removed_profile = count_unable_to_remove = 0
for user in User.objects.all():
    if is_cabinet_user(user):
        try:
            user.profile
            count_w_profile += 1 
            try:
                user.profile.delete()
                count_removed_profile += 1
            except IntegrityError:
                count_unable_to_remove += 1
        except (AttributeError, Profile.DoesNotExist,):
            pass
print "%d cabinet users were with a profile" % count_w_profile
print "%d : deprived profile" % count_removed_profile
print "%d : failed to deprive profile" % count_unable_to_remove
