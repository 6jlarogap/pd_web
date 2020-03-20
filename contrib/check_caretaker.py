# check_caretaker.py
#
# Проверить ответственных смотрителей по кладбищам, участкам, местам.
# Где уволенные и т.п., заменить на отсутствие ответственного смотрителя.
#
# Запуск из ./manage.py shell :
# exec(open('../contrib/check_caretaker.py').read())

from burials.models import Cemetery, Area, Place

def check_model(model):
    print('Checking %s' % model.__name__)
    count = 0
    for obj in model.objects.filter(caretaker__isnull=False):
        if model is Cemetery:
            cemetery = obj
        else:
            cemetery = obj.cemetery
        if cemetery not in Cemetery.editable_ugh_cemeteries(obj.caretaker):
            obj.caretaker = None
            obj.save()
            count += 1
    print(' %s object(s) fixed' % count)

for model in (Cemetery, Area, Place, ):
    check_model(model)
