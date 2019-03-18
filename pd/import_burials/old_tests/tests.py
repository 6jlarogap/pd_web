# coding=utf-8
from burials.models import Burial
from orders.models import Product, Order, OrderItem, CatafalqueData, CoffinData
import os

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils.translation import activate
from django.core.files.base import ContentFile
from persons.models import DeadPerson, PersonID, DeathCertificate

from users.models import Org, Profile, BankAccount
from import_burials.models import do_import_orgs, do_import_burials, do_import_services, do_import_orders, do_import_banks, do_import_dcs, do_import_docs


class FormsTest(TestCase):
    def setUp(self):
        activate('ru')
        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        ugh_org = Org.objects.create(
            type=Org.PROFILE_UGH, name='ugh'
        )
        Profile.objects.create(
            user=self.ugh_user, org=ugh_org,
        )
        self.ugh_client = Client()
        self.ugh_client.login(username='ugh', password='test')

    def test_view(self):
        r = self.ugh_client.get('/import/')
        self.assertEqual(r.status_code, 200)

class OrgsTest(TestCase):
    def setUp(self):
        activate('ru')
        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        ugh_org = Org.objects.create(
            type=Org.PROFILE_UGH, name='ugh'
        )
        Profile.objects.create(
            user=self.ugh_user, org=ugh_org,
            )
        self.ugh_client = Client()
        self.ugh_client.login(username='ugh', password='test')

        self.csv_data = """ИНН,Название,Полное название,Директор,Страна,Регион,Город,Улица,Дом,Корпус,Строение,Офис/квартира,Доп.инфо
4029030735,Больница Циолковского,"НУЗ ""Отделенческая больница имени К. Э. Циолковскго на ст. Калуга ОАО \"\"РЖД\"\"",None,None,None,None,None,None,None,None,None,None
4027001785,БСМП,"МУЗ ""Калужская городская больница скорой медицинской помощи"" имени Шевченко Клеопатры Николаевны",None,None,None,None,None,None,None,None,None,None
4027011007,ГАУЗ КО КОСП,ГАУЗ Калужская Областная стоматологическая поликлиника,None,None,None,None,None,None,None,None,None,None
,"ГБУЗ Калужской области \"\"ОТБ\"\"","ГБУЗ  КО \"\"Областная туберкулезная  больница\"\"",None,None,None,None,None,None,None,None,None,None
4027002884,ГБУЗ КО б-ца №4,ГБУЗ КО калужская городская больница №4 имени Хлюстина Анатолия Семеновича ,None,None,None,None,None,None,None,None,None,None
4027002884,Гор.больница №4,"МУЗ \"\"Калужская городская больница №4 имени Хлюстина Антона Семеновича\"\"",None,None,None,None,None,None,None,None,None,None
4027014752,Гор.больница №5,"МУЗ \"\"Калужская городская больница №5\"\"",None,None,None,None,None,None,None,None,None,None
,Городская больница № 4,МУЗ Калужская гор.больница им. Хлюстина,None,None,None,None,None,None,None,None,None,None
4028004740,Гор.поликлиника №2,"МУЗ ""Городская поликлиника №2№",None,None,None,None,None,None,None,None,None,None
,Гор.поликлиника № 6,"ГБУЗ КО \"\"Городская поликлиника № 6\"\"",None,None,None,None,None,None,None,None,None,None
,Дом инвалидов,"ГБУЗ КО\"\"Дом инвалидов\"\"",None,None,None,None,None,None,None,None,None,None
4027020925,Дом ребенка специализированный,"ГКУЗ \"\"Дом ребенка специализированный\"\"",None,None,None,None,None,None,None,None,None,None"""
        self.csv_path = os.tempnam()

        f = open(self.csv_path, 'w')
        f.write(self.csv_data.encode('utf-8'))
        f.close()

    def tearDown(self):
        os.unlink(self.csv_path)

    def test_import(self):
        self.assertEqual(Org.objects.all().count(), 1)
        do_import_orgs(ContentFile(self.csv_data.encode('utf-8')))
        self.assertEqual(Org.objects.all().count(), 12) # one duplicated INN

    def test_view(self):
        self.assertEqual(Org.objects.all().count(), 1)
        r = self.ugh_client.post('/import/orgs/', data={'orgs-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Org.objects.all().count(), 12) # one duplicated INN

    def test_duplicate(self):
        self.assertEqual(Org.objects.all().count(), 1)
        r = self.ugh_client.post('/import/orgs/', data={'orgs-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Org.objects.all().count(), 12) # one duplicated INN

        self.assertEqual(Org.objects.all().count(), 12)
        r = self.ugh_client.post('/import/orgs/', data={'orgs-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Org.objects.all().count(), 12) # all 12 duplicates

class ServicesTest(TestCase):
    def setUp(self):
        activate('ru')
        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        ugh_org = Org.objects.create(
            type=Org.PROFILE_UGH, name='ugh'
        )
        Profile.objects.create(
            user=self.ugh_user, org=ugh_org,
            )
        self.ugh_client = Client()
        self.ugh_client.login(username='ugh', password='test')

        self.csv_data = """Название,Умолч.,Ед. изм.,Цена,Сортировка
"Благоустройство захоронения (формирование холма, разравнивание грунта)",True,услуга,200.00,2
Работа автокатафалка,True,1 маш/час,660.00,5
Оформление документов для погребения,True,услуга,105.60,0
Установка венков вокруг холма,True,услуга,70.00,3
Намогильная табличка,True,шт.,260.00,4
Погребение ,True,услуга,2362.36,1
Внесение гроба с телом умершего в помещение не выше первого этажа (грузчики),False,услуга,220.00,22
Вызов агента ритуальной службы на дом для оформления заказа,False,услуга,330.00,30
Перенос гроба с телом умершего из помещения морга с заездом к дому и сопровождение к месту захоронения (грузчики),False,услуга,1760.00,22
Разовая услуга по уходу за могилой в зимнее время,False,услуга,200.00,25
"Доставка гроба и других предметов, необходимых для погребения (0,5м/ч)",False,услуга,224.00,14
"Перевозка тела (останков) умершего на кладбище (1,5м/ч)",False,услуга,672.00,12"""
        self.csv_path = os.tempnam()

        f = open(self.csv_path, 'w')
        f.write(self.csv_data.encode('utf-8'))
        f.close()

    def tearDown(self):
        os.unlink(self.csv_path)

    def test_import(self):
        self.assertEqual(Product.objects.all().count(), 0)
        do_import_services(ContentFile(self.csv_data.encode('utf-8')))
        self.assertEqual(Product.objects.all().count(), 12) # one duplicated INN

    def test_view(self):
        self.assertEqual(Product.objects.all().count(), 0)
        r = self.ugh_client.post('/import/services/', data={'services-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Product.objects.all().count(), 12) # one duplicated INN

    def test_duplicate(self):
        self.assertEqual(Product.objects.all().count(), 0)
        r = self.ugh_client.post('/import/services/', data={'services-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Product.objects.all().count(), 12) # one duplicated INN

        self.assertEqual(Product.objects.all().count(), 12)
        r = self.ugh_client.post('/import/services/', data={'services-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Product.objects.all().count(), 12) # all 12 duplicates

class BankAccountTest(TestCase):
    def setUp(self):
        activate('ru')
        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        ugh_org = Org.objects.create(
            type=Org.PROFILE_UGH, name='ugh'
        )
        Profile.objects.create(
            user=self.ugh_user, org=ugh_org,
            )
        self.ugh_client = Client()
        self.ugh_client.login(username='ugh', password='test')

        self.csv_data = """ИНН,Организация,РС,КС,БИК,Банк,ЛС
4029030735,МБУ Калугаблагоустройство,111111,222222222,333333333,ТестБанк,4444444444"""
        self.csv_path = os.tempnam()

        f = open(self.csv_path, 'w')
        f.write(self.csv_data.encode('utf-8'))
        f.close()

    def tearDown(self):
        os.unlink(self.csv_path)

    def test_import(self):
        self.assertEqual(BankAccount.objects.all().count(), 0)
        do_import_banks(ContentFile(self.csv_data.encode('utf-8')))
        self.assertEqual(BankAccount.objects.all().count(), 1)

    def test_view(self):
        self.assertEqual(BankAccount.objects.all().count(), 0)
        r = self.ugh_client.post('/import/banks/', data={'banks-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(BankAccount.objects.all().count(), 1)

    def test_duplicate(self):
        self.assertEqual(BankAccount.objects.all().count(), 0)
        r = self.ugh_client.post('/import/banks/', data={'banks-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(BankAccount.objects.all().count(), 1)

        self.assertEqual(BankAccount.objects.all().count(), 1)
        r = self.ugh_client.post('/import/banks/', data={'banks-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(BankAccount.objects.all().count(), 1)


class PassportsTest(TestCase):
    def setUp(self):
        activate('ru')
        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        ugh_org = Org.objects.create(
            type=Org.PROFILE_UGH, name='ugh'
        )
        Profile.objects.create(
            user=self.ugh_user, org=ugh_org,
            )
        self.ugh_client = Client()
        self.ugh_client.login(username='ugh', password='test')

        self.csv_data = """Ф,И,О,Тип,Серия,Номер,Кем выдан,Когда выдан
Копцев,Игорь,Вадимович,паспорт гражданина РФ,45 09,380942,ОТДЕЛЕНИЕМ ПО РАЙОНУ АЭРОПОРТ ОУФМС РОССИИ ПО Г. МОСКВА В САО ,2008-02-08
Бутина,Валентина,Тимофеевна,паспорт гражданина РФ,2901,295080,ОВД ЛЕНИНСКОГО ОКРУГА,None"""
        self.csv_path = os.tempnam()

        f = open(self.csv_path, 'w')
        f.write(self.csv_data.encode('utf-8'))
        f.close()

    def tearDown(self):
        os.unlink(self.csv_path)

    def test_import(self):
        self.assertEqual(PersonID.objects.all().count(), 0)
        do_import_docs(ContentFile(self.csv_data.encode('utf-8')))
        self.assertEqual(PersonID.objects.all().count(), 2)

    def test_view(self):
        self.assertEqual(PersonID.objects.all().count(), 0)
        r = self.ugh_client.post('/import/docs/', data={'docs-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(PersonID.objects.all().count(), 2)

    def test_duplicate(self):
        self.assertEqual(PersonID.objects.all().count(), 0)
        r = self.ugh_client.post('/import/docs/', data={'docs-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(PersonID.objects.all().count(), 2)

        self.assertEqual(PersonID.objects.all().count(), 2)
        r = self.ugh_client.post('/import/docs/', data={'docs-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(PersonID.objects.all().count(), 2)

class DeathCertsTest(TestCase):
    def setUp(self):
        activate('ru')
        self.ugh_user = User.objects.create_user(username='ugh', email='test@example.com', password='test')
        ugh_org = Org.objects.create(
            type=Org.PROFILE_UGH, name='ugh'
        )
        Profile.objects.create(
            user=self.ugh_user, org=ugh_org,
            )
        self.ugh_client = Client()
        self.ugh_client.login(username='ugh', password='test')

        self.csv_data = """Ф,И,О,Серия,Номер,Когда выдан,ЗАГС
Конин,Виктор,Кузьмич,796967/101,1-НК,2013-01-08,Управление ЗАГС г. Калуги
Минкина,Мария,Максимовна,796975/109,I-HK,2013-01-08,Управление ЗАГС г. Калуги
Зубрилина,Людмила,Николаевна,796974/108,1-НК,2013-01-08,Управление ЗАГС г. Калуги
Корначев,Михаил,Ильич,796976/110,I-HK,2013-01-08,Управление ЗАГС г. Калуги
Лопатин,Захар,Никитович,796961/96,1-НК,2013-01-08,Управление ЗАГС г. Калуги
Гришечкин,Афанасий,Афанасьевич,796960/95,1-НК,2013-01-08,Управление ЗАГС г. Калуги
Потехина,Антонина,Афанасьевна,796971\105,1-НК,2013-01-06,Управление ЗАГС г. Калуги
Чуриков,Евгений,Валентинович,796973/107,1-НК,2013-01-08,Управление ЗАГС г. Калуги"""
        self.csv_path = os.tempnam()

        f = open(self.csv_path, 'w')
        f.write(self.csv_data.encode('utf-8'))
        f.close()

    def tearDown(self):
        os.unlink(self.csv_path)

    def test_import(self):
        self.assertEqual(DeathCertificate.objects.all().count(), 0)
        do_import_dcs(ContentFile(self.csv_data.encode('utf-8')))
        self.assertEqual(DeathCertificate.objects.all().count(), 8)

    def test_view(self):
        self.assertEqual(DeathCertificate.objects.all().count(), 0)
        r = self.ugh_client.post('/import/dcs/', data={'dcs-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(DeathCertificate.objects.all().count(), 8)

    def test_duplicate(self):
        self.assertEqual(DeathCertificate.objects.all().count(), 0)
        r = self.ugh_client.post('/import/dcs/', data={'dcs-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(DeathCertificate.objects.all().count(), 8)

        self.assertEqual(DeathCertificate.objects.all().count(), 8)
        r = self.ugh_client.post('/import/dcs/', data={'dcs-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(DeathCertificate.objects.all().count(), 8)



from big_data_tests import *