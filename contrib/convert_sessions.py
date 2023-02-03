# convert_sessions.py
#
# Преобразовать сессии пользователей из Pickle to Json,
# иначе, если просто при переходе от Pickle to Json удалить:
# psql ... delete from django_session, то
# во всех браузерах клиентов будет запрос на ввод имени пароля,
# а вдруг они его не помнят?!
#
# Запуск из ./manage.py shell :
#   (разумеется, web сервер должен быть выключен)
#   1. exec(open('../contrib/convert_sessions.py').read(), dict(mode_here='get_pickled'))
#       -   чтобы получить файл со всеми сессиями, какими они были в pickled
#       !   в settings.py: SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
#       ->  получим файл OUTPUT_FNAME в текущем каталоге
#
#   2. exec(open('../contrib/convert_sessions.py').read(), dict(mode_here='json_it'))
#       -   чтобы получить файл со всеми сессиями, какими они были в pickled
#       !   в settings.py: SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
#       ->  получим файл OUTPUT_FNAME в текущем каталоге

OUTPUT_FNAME = 'pickled.sessions.json'

import os, json
from importlib import import_module

from django.conf import settings
from django.contrib.sessions.models import Session
SessionStore =import_module(settings.SESSION_ENGINE).SessionStore

mode_here = globals().get('mode_here')
if mode_here not in ('get_pickled', 'json_it'):
    print("FAILED: mode_here not in ('get_pickled', 'json_it')")

elif mode_here == 'get_pickled':
    if os.path.isfile(OUTPUT_FNAME):
        print('FAILED: file %s exists' % OUTPUT_FNAME)
    else:
        if settings.SESSION_SERIALIZER != 'django.contrib.sessions.serializers.PickleSerializer':
            print("FAILED: settings.SESSION_SERIALIZER != 'django.contrib.sessions.serializers.PickleSerializer'")
        else:
            with open(OUTPUT_FNAME, 'w') as f:
                d_sessions = []
                for session in Session.objects.all():
                    d_session = session.get_decoded()
                    d_session.update(session_key=session.session_key)
                    d_sessions.append(d_session)
                f.write(json.dumps(d_sessions))
            print('SUCCESS')
            print("    Now put in settings.py: SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'")
            print("    and ./manage.py shell ...")
            print("    exec(open('../contrib/convert_sessions.py').read(), dict(mode_here='json_it'))")
            exit()

elif mode_here == 'json_it':
    try:
        raw = open(OUTPUT_FNAME).read()
    except OSError:
        raw = ''
    if settings.SESSION_SERIALIZER != 'django.contrib.sessions.serializers.JSONSerializer':
        print("FAILED: settings.SESSION_SERIALIZER != 'django.contrib.sessions.serializers.JSONSerializer'")
    else:
        try:
            d_sessions = json.loads(raw)
            n = n_all = 0
            for d_session in d_sessions:
                n_all += 1
                try:
                    session = Session.objects.get(session_key=d_session['session_key'])
                    s = SessionStore(session_key=session.session_key)
                    del d_session['session_key']
                    session.session_data = s.encode(session_dict=d_session)
                    session.save(update_fields=('session_data',))
                    n += 1
                except Session.DoesNotExist:
                    continue
            print('SUCCESS')
            print('    %s sessions total, %s converted'% (n_all, n))
            print('    Now rm %s' % OUTPUT_FNAME)
        except ValueError:
            print('FAILED: unable to read file %s to a list' % OUTPUT_FNAME)
