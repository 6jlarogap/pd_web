# -*- coding: utf-8 -*-

# create_burial_views.py
# ------------------

# Запуск: : ./manage.py create_burial_views yes
#
# Параметр yes нужен, чтобы сдуру лишний раз не запускали

BURIAL_VIEWS_SQL = """
    CREATE OR REPLACE VIEW burials_burial1 AS
    SELECT *,
    CASE WHEN account_number IS NULL
        THEN ''
        ELSE substring(account_number FROM '([^[:digit:]]*)[[:digit:]]*.*')
    END
        AS account_number_s1,
    CASE WHEN account_number IS NULL
        THEN -1
        ELSE to_number(CASE WHEN trim(both ' ' from substring(account_number FROM '[^[:digit:]]*([[:digit:]]*).*'))=''
                            THEN '99999999999999999999'
                    ELSE substring(account_number FROM '[^[:digit:]]*([[:digit:]]*).*')
                END, '99999999999999999999')
    END
        AS account_number_s2,
    CASE WHEN account_number IS NULL
        THEN ''
        ELSE substring(account_number FROM '[^[:digit:]]*[[:digit:]]*(.*)')
    END
        AS account_number_s3,
    CASE WHEN place_number IS NULL
        THEN ''
        ELSE substring(place_number FROM '([^[:digit:]]*)[[:digit:]]*.*')
    END
        AS place_number_s1,
    CASE WHEN place_number IS NULL
        THEN -1
        ELSE to_number(CASE WHEN trim(both ' ' from substring(place_number FROM '[^[:digit:]]*([[:digit:]]*).*'))=''
                            THEN '99999999999999999999'
                    ELSE substring(place_number FROM '[^[:digit:]]*([[:digit:]]*).*')
                END, '99999999999999999999')
    END
        AS place_number_s2,
    CASE WHEN place_number IS NULL
        THEN ''
        ELSE substring(place_number FROM '[^[:digit:]]*[[:digit:]]*(.*)')
    END
        AS place_number_s3
    FROM burials_burial;
"""

from django.db import connection
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    args = 'yes, if you mean to execute this command'
    help = "Create or replace database view(s) for Burial application"

    def handle(self, *args, **options):
        yes_msg = "Give 'yes' as a single parameter if you mean to create/replace burial view(s)"
        if len(args) < 1 or args[0].decode("utf-8").lower() != u'yes':
            print "Give 'yes' as a single parameter if you mean to create/replace burial view(s)"
            quit()
        cursor = connection.cursor()
        cursor.execute(BURIAL_VIEWS_SQL)
