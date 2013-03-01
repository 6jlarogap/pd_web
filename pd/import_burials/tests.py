# coding=utf-8
from burials.models import Burial
import os

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils.translation import activate
from django.core.files.base import ContentFile

from users.models import Org, Profile
from import_burials.models import do_import_orgs, do_import_burials


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

        self.csv_data = u"""ИНН,Название,Полное название,Директор,Страна,Регион,Город,Улица,Дом,Корпус,Строение,Офис/квартира,Доп.инфо
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


class BurialsTest(TestCase):
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

        self.csv_data = u"""Номер,Операция,План дата,Факт дата,Факт время,Эксгум дата,Кладбище,Участок,Ряд,Место,Число мест,Бесхозяйное,Фамилия Ответственного ,Имя Ответственного ,Отчество Ответственного ,Дата рождения Ответственного,Телефоны Ответственного ,Страна Ответственного ,Регион Ответственного ,Город Ответственного ,Улица Ответственного ,Дом Ответственного ,Корпус Ответственного ,Строение Ответственного ,Офис/квартира Ответственного,Доп.инфо Ответственного,Номер могилы,Фамилия Усопшего ,Имя Усопшего ,Отчество Усопшего ,Дата рождения Усопшего ,Дата смерти Усопшего ,Страна Усопшего ,Регион Усопшего ,Город Усопшего ,Улица Усопшего,Дом Усопшего ,Корпус Усопшего ,Строение Усопшего ,Офис/квартира Усопшего,Доп.инфо Усопшего,Фамилия Заказчика,Имя Заказчика,Отчество Заказчика,Дата рождения Заказчика,Телефоны Заказчика,Страна Заказчика,Регион Заказчика,Город Заказчика,Улица Заказчика,Дом Заказчика,Корпус Заказчика,Строение Заказчика,Офис/квартира Заказчика,Доп.инфо Заказчика,ИНН Заказчика-ЮЛ,Полное название Заказчика-ЮЛ,Фамилия Агента,Имя Агента,Отчество Агента,Номер Доверенности,Дата Доверенности,Окончание Доверенности,Данные Заказа,Платеж,Комментарий
20120003,Подзахоронение к существ,2012-01-09,2012-01-09,None,None,Карачевское кладбище,,,19952036,1,False,Шленская,Татьяна,Степановна,None,None,Россия,Калужская область,Калуга,Гурьянова ул.,14-б,,,60,,None,Шленский,Сергей,Иванович,29.08.1956,2012-01-08,Россия,Калужская область,Калуга,Черносвитино дер.,8,,,,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,402804077086,Индивидуальный предприниматель Годеев Юрий Васильевич,Гордеев,Иван,Юрьевич,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:24:49.11480220120053,Захоронение,2012-03-24,2012-03-24,None,None,Кладбище д. Рождествено,-,,20120053,3,False,Захарова,Наталья,Владимировна,None,None,Россия,Калужская область,Калуга,Платова ул.,22,,,62,,None,Захаров,Александр,Васильевич,28.08.1952,2012-03-22,Россия,Калужская область,Калуга,Платова ул.,22,,,62,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,402906951176,Индивидуальный предприниматель Васильева Елена Викторовна,Астахова,Светлана,Викторовна,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:26:40.454160
20120014,Захоронение,2012-03-26,2012-03-26,None,None,Карачевское кладбище,,,20120014,3,False,Новикова,Наталия,Валентиновна,None,None,Россия,Калужская область,Калуга,Гурьянова ул.,26,,,83,,None,Таланова,Мария,Сергеевна,01.12.1944,2012-03-23,Россия,Калужская область,Калуга,Московская ул.,303,,,15,,Новикова,Наталия,Валентиновна,None,None,Россия,Калужская область,Калуга,Гурьянова ул.,26,,,83,,None,None,None,None,None,None,None,None,{},nal,Создано: kbm_1 2013-01-08 13:26:40.503000
20120655,Подзахоронение к существ,2012-03-26,2012-03-26,None,None,Литвиновское кладбище,47,,20112428,3,False,Евстифеев,Николай,Аскольдович,None,None,Россия,Калужская область,Калуга,Болдина ул.,21,,,11,,None,Евстифеев,Аскольд,Николаевич,11.07.1936,2012-03-24,Россия,Калужская область,Калуга,Болдина ул.,21,,,11,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,402904778952,Индивидуальный предприниматель Коровенков Александр Юрьевич,Горбачев,Владимир,Викторович,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:26:40.555578
20120088,Захоронение в существующ,2012-03-27,2012-03-27,None,None,Трифоновское кладбище,14,,20120088,1,False,Гинзбург,Борис,Григорьевич,None,None,Россия,Калужская область,Калуга,Вишневского ул.,17,,,59,,None,Гинзбург,Григорий,Наумович,26.04.1929,2012-03-25,Россия,Калужская область,Калуга,Гурьянова ул.,16,1,,8,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,7702185362,"ЗАО ""Военно-мемориальная компания"" Московский филиал",Анисимова,Лидия,Вячеславовна,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:26:40.602829
20120660,Захоронение,2012-03-27,2012-03-27,None,None,Литвиновское кладбище,40,,20120660,3,False,Касинова,Галина,Борисовна,None,None,Россия,Калужская область,Калуга,Московская ул.,217,,,39,,None,Касинов,Василий,Иванович,12.01.1938,2012-03-25,Россия,Калужская область,Калуга,Московская ул.,217,,,39,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,402800813190,Индивидуальный предприниматель Упилков Сергей Борисович,Ефременко,Алексей,Иванович,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:26:40.655258
20120662,Подзахоронение к существ,2012-03-27,2012-03-27,None,None,Литвиновское кладбище,33,,20091564,2,False,Белоногов,Сергей,Геннадиевич,None,None,Россия,Калужская область,Калуга,Мстихинская ул.,8,,,22,,None,Белоногова,Ираида,Александровна,25.10.1940,2012-03-25,Россия,Калужская область,Калуга,Гурьянова ул.,18,,,42,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,402706903908,Индивидуальный предприниматель Войде Денис Георгиевич,Адуев,Алексей,Геннадьевич,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:26:40.711818
20120668,Подзахоронение к существ,2012-03-27,2012-03-27,None,None,Литвиновское кладбище,46,,20111124,3,False,Рыжов,Валерий,Васильевич,None,None,Россия,Калужская область,Калуга,Болдина ул.,9,,,32,,None,Рыжов,Николай,Васильевич,09.06.1964,2012-03-25,Россия,Калужская область,Калуга,Знаменская ул.,4,,,32,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,402906951176,Индивидуальный предприниматель Васильева Елена Викторовна,Астахова,Светлана,Викторовна,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:26:40.761894
20120678,Захоронение,2012-03-28,2012-03-28,None,None,Литвиновское кладбище,48,,20120678,3,False,Соколова,Екатерина,Владимировна,None,None,Россия,Калужская область,Калуга,Малоярославецкая ул.,12,,,21,,None,Соколов,Владимир,Владимирович,28.02.1989,2012-03-25,Россия,Калужская область,Калуга,Малоярославецкая ул.,12,,,21,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,402708843637,Индивидуальный предприниматель Кривопалова Валентина Николаевна,Гуро,Владимир,Николаевич,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:26:40.811883
20120690,Захоронение,2012-03-30,2012-03-30,None,None,Литвиновское кладбище,42,,20120690,1,False,Волков,В,К,None,None,Россия,Калужская область,Калуга,Ст.Разина ул.,,,,,,None,Биоотходы,,,None,2012-03-28,Россия,Калужская область,Калуга,Вишневского ул.,,,,,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,,"ГБУЗ КО \"\"Калужская областная детская больница\"\"",Волков,Виктор,Кириллович,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:26:40.864244
20120090,Подзахоронение к существ,2012-03-31,2012-03-31,None,None,Трифоновское кладбище,17,,20120090,2,False,Васичева,Татьяна,Николаевна,None,None,Россия,Калужская область,Калуга,Колхозная ул.,21а,,,,,None,Мкртычян,Степан,Мушегович,22.07.1938,2012-03-28,Россия,Калужская область,Мстихино пос.,Лесная ул.,26,1,,16,,Васичева,Татьяна,Николаевна,None,None,Россия,Калужская область,Калуга,Колхозная ул.,21а,,,,,None,None,None,None,None,None,None,None,{},nal,Создано: kbm_1 2013-01-08 13:26:40.912203
20120692,Захоронение,2012-03-30,2012-03-30,None,None,Литвиновское кладбище,48,,20120692,3,False,Аржатская,Людмила,Алексеевна,None,None,Россия,Калужская область,Калуга,Степана разина ул.,89,,,70,,None,Бухтин,Алексей,Федорович,08.11.1935,2012-03-28,Россия,Калужская область,Калуга,Ст.Разина ул.,89,,,70,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,402801447772,Индивидуальный предприниматель Карпов Руслан Андреевич,Томашевский,Константин,Иванович,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:26:40.963183
20120699,Захоронение,2012-03-31,2012-03-31,None,None,Литвиновское кладбище,48,,20120699,3,False,Кабанова,Людмила,Ивановна,None,None,Россия,Калужская область,Калуга,Энгельса ул.,89,,,53,,None,Шустиков,Николай,Дмитриевич,05.12.1938,2012-03-29,Россия,Калужская область,Калуга,Энгельса ул,89,,,33,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,402906951176,Индивидуальный предприниматель Васильева Елена Викторовна,Астахова,Светлана,Викторовна,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:26:41.020396
20121859,Захоронение,2012-09-21,2012-09-21,None,None,Литвиновское кладбище,37,,20121859,3,False,Акимова,Галина,Николаевна,None,None,Россия,Калужская область,Калуга,Гурьянова ул.,53,,,25,,None,Шмелева,Мария,Сергеевна,12.02.1925,2012-09-19,Россия,Калужская область,Калуга,Гурьянова ул.,53,,,25,,None,None,None,None,None,None,None,None,None,None,None,None,None,None,7702185362,"ЗАО ""Военно-мемориальная компания""Московский филиал",Анисимова,Лидия,Вячеславовна,None,None,None,{},beznal,Создано: kbm_1 2013-01-08 13:23:28.722180"""
        self.csv_path = os.tempnam()

        f = open(self.csv_path, 'w')
        f.write(self.csv_data.encode('utf-8'))
        f.close()

    def tearDown(self):
        os.unlink(self.csv_path)

    def test_import(self):
        self.assertEqual(Burial.objects.all().count(), 0)
        do_import_burials(ContentFile(self.csv_data.encode('utf-8')), user=self.ugh_user)
        self.assertEqual(Burial.objects.all().count(), 13)

    def test_view(self):
        self.assertEqual(Burial.objects.all().count(), 0)
        r = self.ugh_client.post('/import/burials/', data={'burials-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Burial.objects.all().count(), 13)

    def test_duplicate(self):
        self.assertEqual(Burial.objects.all().count(), 0)
        r = self.ugh_client.post('/import/burials/', data={'burials-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Burial.objects.all().count(), 13)

        self.assertEqual(Burial.objects.all().count(), 13)
        r = self.ugh_client.post('/import/burials/', data={'burials-csv': open(self.csv_path)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Burial.objects.all().count(), 13)
