# coding=utf-8
#
# fix_unknown_applicant_w_address
#
# При импорте кладбищ Минска заявитель в захоронении формировался
# лишь если у него была указана фамилия. Но много случаев, когда
# в набивалке вводили заявителей без фамилии, но с адресом и/или
# с телефоном
#
# Запуск из ./manage.py shell :
# execfile('/path/to/fix_unknown_applicant_w_address.py')
#
# Заполнить здесь название кладбища и путь к csv-экспорту кладбищ

CEMETERY_NAME = u'Кальварийское'

CSV_PATH = '/home/suprune20/musor/export-nabivalka'
#
# Искажение во избежание случайного запуска процедуры
#
UGH_PK = -2

import csv

from django.db import transaction
from django.db.models.query_utils import Q

from import_burials.models import UnicodeReader, make_name, make_date

from burials.models import Cemetery, Burial

csv.register_dialect("4minsk", escapechar="\\", quoting=csv.QUOTE_ALL, doublequote=False)

@transaction.commit_on_success
def main():
    
    cemetery = Cemetery.objects.get(ugh__pk=UGH_PK, name=CEMETERY_NAME)
    csvfile = open(u'%s/%s.csv' % (CSV_PATH, CEMETERY_NAME), 'rb')
    csvreader = UnicodeReader(csvfile, dialect="4minsk")

    (
        musor_str_id,
        account_number,
        deadman_ln, deadman_fn, deadman_mn,
        musor_initials,
        fact_date,
        area_name, row_name, place_number,
        applicant_ln, applicant_fn, applicant_mn,
        musor_cust_initials,
        city_name, street_name, house, block, flat,
        comments,
        country_name,
        region_name,
        phone,
        file_names, file_comments,
        post_index, building,
        op_type,
     ) = range(28)

    q_base = Q(
        source_type=Burial.SOURCE_TRANSFERRED,
        cemetery=cemetery,
        applicant_organization__isnull=True,
    )

    count = count_fixed = count_replaced = count_not_found = 0
    for i, row in enumerate(csvreader):
        count += 1
        if count % 1000 == 0:
            transaction.commit()
            print u"Csv recs: %s, fixed: %s, replaced: %s, not found: %s" % (
                count,
                count_fixed,
                count_replaced,
                count_not_found,
            )
        if not make_name(row[applicant_ln]):
            phones = row[phone].strip().replace("\n", "; ")
            row[city_name] = row[city_name].strip()
            if row[city_name] or phones:

                deadman_last_name = make_name(row[deadman_ln])
                deadman_first_name = make_name(row[deadman_fn])
                deadman_middle_name = make_name(row[deadman_mn])

                row[area_name] = row[area_name].strip()
                if not row[area_name]:
                    row[area_name] = u'Без имени'
                row[row_name] = row[row_name].strip()
                row[place_number] = row[place_number].strip()
                
                q_place = Q(
                    area__name=row[area_name],
                    row=row[row_name],
                    place_number=row[place_number],
                )
                row[fact_date] = row[fact_date][:10]
                fact_date_ = make_date(row[fact_date])
                if fact_date_:
                    q_fact_date = Q(
                        fact_date__year=fact_date_.year,
                        fact_date__month=fact_date_.month,
                        fact_date__day=fact_date_.day,
                        fact_date_no_month=fact_date_.no_month,
                        fact_date_no_day=fact_date_.no_day,
                    )
                else:
                    q_fact_date = Q(fact_date__isnull=True)

                if deadman_last_name:
                    q_deadman = Q(
                        deadman__last_name=deadman_last_name,
                        deadman__first_name=deadman_first_name,
                        deadman__middle_name=deadman_middle_name,
                    )
                else:
                    q_deadman = Q(deadman__isnull=True) | Q(deadman__last_name='')

                q_account_number = Q(account_number=row[account_number].strip())
                burial = None
                try:
                    burial = Burial.objects.get(
                        q_base & \
                        q_account_number & \
                        q_fact_date & \
                        q_deadman & \
                        q_place
                    )
                    if burial.applicant and burial.applicant.last_name.strip():
                        continue
                except Burial.MultipleObjectsReturned:
                    for b in Burial.objects.filter(
                            q_base & \
                            q_account_number & \
                            q_fact_date & \
                            q_deadman & \
                            q_place
                        ).order_by('pk'):
                        if b.applicant and b.applicant.last_name.strip():
                            continue
                        burial = b
                        break
                except Burial.DoesNotExist:
                    # Переместили в другое место? Изменили или ввели фамилию?
                    try:
                        burial = Burial.objects.get(
                            q_base & \
                            q_account_number & \
                            q_fact_date
                        )
                        if burial.applicant and burial.applicant.last_name.strip():
                            continue
                        count_replaced +=1
                    except (Burial.DoesNotExist, Burial.MultipleObjectsReturned):
                        print u'Not found(!), %s: %s, %s:%s' % (
                            CEMETERY_NAME,
                            i+1,
                            row[account_number],
                            row[deadman_ln]
                        )
                        count_not_found += 1
                if burial:
                    row[country_name] = row[country_name].strip()
                    if not row[country_name] or row[country_name].lower() == u'неизвестен':
                        row[country_name] = u'Беларусь'

                    row[region_name] = row[region_name].strip()
                    if not row[region_name] or row[region_name].lower() == u'неизвестен':
                        row[region_name] = u'Минская обл.'

                    if not row[city_name] or row[city_name].lower() == u'неизвестен':
                        row[city_name] = u'Минск'

                    count_fixed += 1


    if count % 1000 != 0:
        transaction.commit()
        print u"Csv recs: %s, fixed: %s, replaced: %s, not found: %s" % (
            count,
            count_fixed,
            count_replaced,
            count_not_found,
        )
    csvfile.close()

main()
