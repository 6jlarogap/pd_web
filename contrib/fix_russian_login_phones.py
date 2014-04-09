# -*- coding: utf-8 -*-

# fix_russian_login_phones.py,
#
# Исправить номера телефонов для входа в кабинет
# ответственного, при условии, что:
#
# !!!   все эти телефоны из России
#
# - телефон типа 9056416023 преобразуется в 79056416023
# - телефон типа 89105161406 преобразуется в 79105161406
#
# Запуск из ./manage.py shell :
# execfile('/path/to/fix_russian_login_phones.py')

from persons.models import AlivePerson

for person in AlivePerson.objects.filter(login_phone__isnull=False)
    login_phone = str(person.login_phone)
    if len(login_phone) == 11 and login_phone.startswith('8'):
        person.login_phone = '7' + login_phone[1:]
        person.save()
    elif len(login_phone) == 10 and login_phone.startswith('9'):
        person.login_phone = '7' + login_phone
        person.save()
