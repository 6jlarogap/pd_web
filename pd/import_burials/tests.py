# coding=utf-8
import os

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils.translation import activate
from django.core.files.base import ContentFile

from users.models import Org, Profile
from import_burials.models import do_import_orgs



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
