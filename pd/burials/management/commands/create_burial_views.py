# -*- coding: utf-8 -*-

# create_burial_views.py
# ------------------

# Запуск: : ./manage.py create_burial_views yes
#
# Параметр yes нужен, чтобы сдуру лишний раз не запускали

# Список создаваемых/изменяемых представлений с командами:
#   create_or_replace:  создать или заменить представление
#   drop:               удалить представление
# В случае неудачи с replace view, например, при смене названия поля
# представления, придется предварительно вызвать drop view
#
VIEWS = (
        dict(
            create_or_replace="""
            CREATE OR REPLACE VIEW burials_burial1 AS
            SELECT *,

            CASE
                WHEN account_number IS NULL
                    THEN ''
                ELSE substring(account_number FROM '([^[:digit:]]*)[[:digit:]]*.*')
            END
            AS account_number_s1,

            CASE
                WHEN account_number IS NULL
                    THEN -1
                WHEN trim(both ' ' from account_number)=''
                    THEN -1
                ELSE to_number(
                        CASE WHEN trim(both ' ' from substring(account_number FROM '[^[:digit:]]*([[:digit:]]*).*'))=''
                                THEN '99999999999999999999'
                            ELSE substring(account_number FROM '[^[:digit:]]*([[:digit:]]*).*')
                        END,
                        '99999999999999999999'
                    )
            END
            AS account_number_s2,

            CASE
                WHEN account_number IS NULL
                    THEN ''
                ELSE substring(account_number FROM '[^[:digit:]]*[[:digit:]]*(.*)')
            END
            AS account_number_s3,

            CASE
                WHEN place_number IS NULL
                    THEN ''
                ELSE substring(place_number FROM '([^[:digit:]]*)[[:digit:]]*.*')
            END
            AS place_number_s1,

            CASE
                WHEN place_number IS NULL
                    THEN -1
                WHEN trim(both ' ' from place_number)=''
                    THEN -1
                ELSE to_number(
                        CASE WHEN trim(both ' ' from substring(place_number FROM '[^[:digit:]]*([[:digit:]]*).*'))=''
                                THEN '99999999999999999999'
                            ELSE substring(place_number FROM '[^[:digit:]]*([[:digit:]]*).*')
                        END,
                        '99999999999999999999'
                    )
            END
            AS place_number_s2,

            CASE
                WHEN place_number IS NULL
                    THEN ''
                ELSE substring(place_number FROM '[^[:digit:]]*[[:digit:]]*(.*)')
            END
            AS place_number_s3,

            id AS burial_id

            FROM burials_burial;
        """,

        drop="""
            DROP VIEW burials_burial1;
        """
    ),
)

from django.db import connection
from django.core.management.base import BaseCommand
from django.db.utils import DatabaseError

class Command(BaseCommand):
    args = 'yes, if you mean to execute this command'
    help = "Create or replace database view(s) for Burial application"

    def handle(self, *args, **options):
        yes_msg = "Give 'yes' as a single parameter if you mean to create/replace burial view(s)"
        if len(args) < 1 or args[0].decode("utf-8").lower() != u'yes':
            print "Give 'yes' as a single parameter if you mean to create/replace burial view(s)"
            quit()
        cursor = connection.cursor()
        for view in VIEWS:
            try:
                cursor.execute(view['create_or_replace'])
            except DatabaseError:
                cursor.execute(view['drop'])
                cursor.execute(view['create_or_replace'])
