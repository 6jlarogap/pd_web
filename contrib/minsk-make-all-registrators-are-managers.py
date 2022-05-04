# minsk-make-all-registrators-are-managers.py
#
# В Минске были 2 роли, заведущий кладбищем и регистратор.
# Заведующий мог править все комментарии, а регистратор только свои
# Теперь они хотят, чтоб регистраторы могли править все комментарии
#
# Делаем так:
#
# - тех кто имел только роль смотрителя, назначаю заведующим
# - роль смотрителя удаляю
# - роль заведующего переименовываю в "Смотритель"
#
# Запуск из ./manage.py shell :
# exec(open('../contrib/minsk-make-all-registrators-are-managers.py').read())

#
# Искажение во избежание случайного запуска процедуры
#

from django.db import transaction

from users.models import Role, Profile, Org

@transaction.atomic
def main():
    try:
        role_cemetery_manager = Role.objects.get(name=Role.ROLE_CEMETERY_MANAGER)
    except Role.DoesNotExist:
        print('No ROLE_CEMETERY_MANAGER in system. Scram!')
        return

    try:
        role_registrator = Role.objects.get(name=Role.ROLE_REGISTRATOR)
    except Role.DoesNotExist:
        print('No ROLE_REGISTRATOR in system. Scram!')
        return

    for profile in Profile.objects.filter(org__type=Org.PROFILE_UGH):
        roles = profile.get_roles()
        if Role.ROLE_REGISTRATOR in roles:
            if Role.ROLE_CEMETERY_MANAGER not in roles:
                print(profile.user.username, '- add role_cemetery_manager')
                profile.role.add(role_cemetery_manager)
            print(profile.user.username, '- remove role_registrator')
            profile.role.remove(role_registrator)

    print('Remove role_registrator')
    role_registrator.delete()

    print('Change role_cemetery_manager title')
    role_cemetery_manager.title = 'Регистратор или смотритель'
    role_cemetery_manager.save()

main()
