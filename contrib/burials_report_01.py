
# Запуск из ./manage.py shell :
# exec(open('../contrib/burials_report_01.py').read())

import os, datetime

from burials.models import Burial

OUTPUT = os.path.join(os.getenv('HOME'),'report_01.txt')

UGH_PK = 2
DATE_START = datetime.date(2019, 1, 1)
DATE_END = datetime.date(2019, 12, 31)

def main():
    with open(OUTPUT,'wb') as f:
        for b in Burial.objects.filter(
                ugh__pk=UGH_PK,
                status=Burial.STATUS_CLOSED,
                fact_date__gte=DATE_START,
                fact_date__lte=DATE_END,
                annulated=False,
            ).order_by('fact_date').distinct().iterator(chunk_size=100):

            deadman_last_name=''
            deadman_first_name=''
            deadman_middle_name=''
            if b.deadman and b.deadman.last_name:
                if deadman_last_name.lower() == 'резервирование':
                    continue
                deadman_last_name=b.deadman.last_name
                deadman_first_name=b.deadman.first_name
                deadman_middle_name=b.deadman.middle_name

            applicant_last_name=''
            applicant_first_name=''
            applicant_middle_name=''
            applicant_address=''
            applicant_phones=''

            if b.applicant and b.applicant.last_name:
                applicant_last_name=b.applicant.last_name
                applicant_first_name=b.applicant.first_name
                applicant_middle_name=b.applicant.middle_name
                if b.applicant.address and b.applicant.address.city:
                    applicant_address=str(b.applicant.address)
                applicant_phones=b.applicant.phones and b.applicant.phones or ''
                
            f.write(('\t'.join((
                b.fact_date.strftime('%d.%m.%Y'),
                deadman_last_name,
                deadman_first_name,
                deadman_middle_name,
                b.cemetery.name,
                b.area.name,
                b.row,
                b.place_number,
                applicant_last_name,
                applicant_first_name,
                applicant_middle_name,
                applicant_address,
                applicant_phones,
            ))+'\r\n').encode('cp1251'))

main()
