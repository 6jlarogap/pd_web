# -*- coding: utf-8 -*-
#
# gora_default_counter.py
#
# Положить в index.html, файл, заданный параметром, значение счетчика по умолчанию
# поблагодаривших персону с token, заданным другим параметром
# Поиск текущего значения счетчика -- по регулярному выражению REGEX

import re

from django.core.management.base import BaseCommand

from persons.models import CustomPerson
from users.models import Thank

REGEX = r'^(.+)\<script\>window\.defaultUsersCount\s*=\s*(\d+)\;\<\/script\>(.+)$'
LINE = u'<script>window.defaultUsersCount = %s;</script>'

class Command(BaseCommand):
    args = '<index.html location> <thank token>'
    help = 'Fill index.html with default count of thanked person with token'
    
    def handle(self, *args, **options):
        try:
            index_html=args[0]
            token = args[1]
        except IndexError:
            quit()
        try:
            with open(index_html, "r") as f:
                data = f.read().decode('utf-8')
        except IOError:
            quit()
        m = re.match(REGEX, data, flags=re.DOTALL | re.I)
        if not m:
            quit()
        file_counter = int(m.group(2))
        try:
            cp = CustomPerson.objects.get(token=token)
        except (
                CustomPerson.DoesNotExist,
                CustomPerson.MultipleObjectsReturned,
               ):
            quit()
        current_counter = Thank.objects.filter(customperson=cp).count()
        if current_counter != file_counter:
            data_new = u"%s%s%s" % (
                m.group(1),
                LINE % current_counter,
                m.group(3),
            )
            with open(index_html, "w") as f:
                f.write(data_new.encode('utf-8'))
 