# coding=utf-8
#
# shuffle_pd.py,         shuffle personal data
#                       (перетасовать персональные данные)
#
# Запуск из ./manage.py shell :
#  execfile('/path/to/this/file.py')

from django.db import transaction
from django.db.models import get_model
from django.db.models.query_utils import Q

try:
    from random import SystemRandom
    random = SystemRandom()
except ImportError:
    import random

@transaction.atomic
def shuffle_fields(model, fields, tries=10):
    """ Перетасовать поля fields в модели model

    model   - строка типа 'приложение.модель', например,
                'persons.Baseperson'
    fields  - список имен полей, например,
                ('last_name', 'first_name', 'middle_name', )
               * Название поля может быть таким: 'address:null',
                 тогда оно устанавливается в null во всей
                 таблице-модели.
               * Или таким: 'email:clear', тогда там ставится
                 пустая строка, это для символьных not null-
                 полей.
               * Или таким: 'name:index:Нач строка '
                 Тогда каждая запись в этом поле меняется на 
                 'Нач строка 1', 'Нач строка 2', где 1, 2 -
                 содержимое первичного ключа соответствующих
                 строк.
                 Иначе...
    Проходим по таблице модели model, по полям fields,
    выбираем оттуда только непустые значения соответствующего
    поля (not null, и если поле символьное, еще != '').
    Например, по полю 'last_name': выбираем из модели также все
    distinct last_name's. Делаем tries попыток
    выбрать случайное из них, так чтобы исходная last_name 
    не была равна найденной.
    """

    if tries <= 0:
        tries = 1
    message = u"  {0} non-empty records of {1} procecced, failed to update: {2}"
    
    print u"Shuffling '{0}'".format(model)
    args_model = model.split('.')
    m = get_model(*args_model)
    
    for f in fields:
        try:
            f, action = f.split(":", 1)
        except ValueError:
            action = ''
        print u" field: '{0}'".format(f)
        if action.lower() == 'null':
            print u" - setting to NULL all records"
            kwargs_update = { f: None,}
            m.objects.all().update(**kwargs_update)
            continue
        elif action.lower() == 'clear':
            print u" - setting to '' all records"
            kwargs_update = { f: '',}
            m.objects.all().update(**kwargs_update)
            continue
        elif action.lower().startswith('index:'):
            index = action[6:]
            action = 'index'
            print u" - setting the field values as '{0}<number>'".format(index)
        elif not action:
            pass
        else:
            print u"  Action {0} for field '{1}' is not supported".format(action, f)
            continue

        kwargs = { '{0}__{1}'.format(f, 'isnull'): False, }
        f_type = m._meta.get_field(f).get_internal_type().lower()
        f_id = f
        if f_type in ('foreignkey', ):
            f_id = f + '_id'
        elif f_type in ('charfield', 'textfield', 'emailfield', ):
            kwargs['{0}__{1}'.format(f, 'gt')] = ''
        else:
            print u"  Type {0} of field '{1}' is not supported".format(f_type, f)
            continue
        # last_name__isnull=False, last_name__gt=''
        q = Q(**kwargs)
        distincts = m.objects.only('id', f).filter(q).order_by(f).distinct(f)
        query = m.objects.only('id', f).filter(q)
        query_count = query.count()

        failed_tries_count = 0
        i = 0
        random.seed()
        for rec in query:
            i += 1
            if not i % 200:
                transaction.commit()
                random.seed()
                print message.format(i, query_count, failed_tries_count)

            if action == 'index':
                val_new = index + str(rec.pk)
            else:
                val = rec.__dict__[f_id]
                for tries_ in range(tries):
                    r = random.randrange(distincts.count())
                    val_new = distincts[r].__dict__[f_id]
                    if val_new != val:
                        break
                else:
                    failed_tries_count += 1
                    continue
            kwargs_update = { f: val_new,}
            m.objects.filter(pk=rec.pk).update(**kwargs_update)
        print message.format(i, query_count, failed_tries_count)

@transaction.atomic
def set_pwds_as_names():
    """Установить у всех пользователей пароли, как имена регистрации"""

    message = " {0} passwords of total {1} set"
    print u"Setting passwords as usernames"

    m = get_model("auth", "User")
    query = m.objects.all()
    query_count = query.count()
    i = 0
    for user in query:
        i += 1
        if not i % 200:
            transaction.commit()
            print message.format(i, query_count)
        user.set_password(user.username)
        user.save()
    print message.format(i, query_count)

# --------------------------------------------------------------------

set_pwds_as_names()

shuffle_fields('auth.User',
               ('first_name:clear', 'last_name:clear',
                'email:clear', )
)
shuffle_fields('burials.Cemetery',
               (u'name:index:Кладбище ', 'address:null', )
)
shuffle_fields('users.Profile',
               ('user_first_name', 'user_middle_name',
                'user_last_name',
               )
)
shuffle_fields('users.Org',
               (u'name:index:Организация ',
                u'full_name:index:Организация ',
                'inn:index:00000', 
                'director', 'email:clear', 'phones:clear',
                'off_address:null',
               )
)
shuffle_fields('persons.BasePerson',
               ('last_name', 'first_name', 'middle_name', )
)
shuffle_fields('persons.PersonId',
               ('source', 'series', 'number', )
)
