# coding=utf-8
#
# create_caretaker.py
#
# Создать роль Profile.Role.ROLE_CARETAKER, если еще нет
#
# Запуск из ./manage.py shell :
# execfile('../contrib/create_caretaker.py')

from users.models import Role

def main():
    role, created = Role.objects.get_or_create(
        name=Role.ROLE_CARETAKER,
        defaults = dict(
            title=u"Смотритель"
    ))
    if created:
        print "Caretaker role created"
    else:
        print "Caretaker role already exists"

    Role.objects.filter(name=Role.ROLE_REGISTRATOR).update(
        title=u"Регистратор"
    )
    print "Registrator role set as 'Registrator' (in Russian)"

main()
