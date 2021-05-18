import copy
from django.db import models, IntegrityError
from django.utils.translation import gettext as _
from django.db.models.deletion import ProtectedError
from django.apps import apps
get_model = apps.get_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

import datetime
from geo.models import Location, LocationMixin
from pd.models import UnclearDate, UnclearDateModelField, BaseModel, Files, \
                      PhotoModel, validate_phone_as_number
from pd.utils import utcisoformat, capitalize
from users.models import Org, PhonesMixin

class IDDocumentType(models.Model):
    name = models.CharField(_("Тип документа"), max_length=255, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = (_("тип документа"))
        verbose_name_plural = (_("типы документов"))
        ordering = ('name', )

class PersonMixin(object):

    def __str__(self):
        if self.last_name.strip():
            result = self.last_name
            if self.first_name:
                result += " %s" % self.first_name
                if self.middle_name:
                    result += " %s" % self.middle_name
        else:
            result = _("Неизвестный")
        return result

    def full_human_name(self):
        return ' '.join((self.last_name, self.first_name, self.middle_name)).strip()

    def get_initials(self):
        initials = ""
        if self.first_name:
            initials = "%s." % self.first_name[:1].upper()
            if self.middle_name:
                initials = "%s%s." % (initials, self.middle_name[:1].upper())
        return initials

    def full_name(self):
        if self.last_name:
            fio = "%s %s" % (self.last_name, self.get_initials())
        else:
            fio = _("Неизвестный")
        return fio.strip()

    def full_name_complete(self):
        fio = "%s %s %s" % (self.last_name, self.first_name, self.middle_name)
        return fio.strip() or _("Неизвестный")

class BasePerson(PersonMixin, models.Model):
    """
    Физическое лицо
    """
    last_name = models.CharField(_("Фамилия"), max_length=255, blank=True)
    first_name = models.CharField(_("Имя"), max_length=255, blank=True)
    middle_name = models.CharField(_("Отчество"), max_length=255, blank=True)
    birth_date = UnclearDateModelField(_("Дата рождения"), serialize=False, blank=True, null=True)
    ident_number = models.CharField(_("Идентификационный номер"),max_length=255, blank=True)

    address = models.ForeignKey(Location, editable=False, null=True, on_delete=models.PROTECT)

    def age(self):
        start = self.birth_date
        finish = (self.death_date or datetime.date.today())
        return int((finish - start).days / 365.25)

    def delete(self):
        try:
            self.personid.delete()
        except (AttributeError, PersonID.DoesNotExist, ProtectedError):
            pass
        try:
            super(BasePerson, self).delete()
        except ProtectedError:
            # При смене усопшего на биоотходы мы пытаемся удалить усопшего.
            # Если при этом он был привязан к Custom(Dead)Person,
            # то удаление не пройдет, а данные "усопшего"-биоотходов
            # могут быть где-то продемонстрированы
            #
            if self.last_name or self.first_name or self.middle_name or self.birth_date:
                self.last_name = ''
                self.first_name = ''
                self.middle_name = ''
                self.birth_date = None
                self.save()
            try:
                deadperson = self.deadperson
                if deadperson.death_date:
                    deadperson.death_date = None
                    deadperson.save()
            except DeadPerson.DoesNotExist:
                pass
        else:
            try:
                self.address.delete()
            except (AttributeError, ProtectedError):
                pass

    def deep_copy(self):
        new_person_addr = None
        if self.address:
            new_person_addr = copy.deepcopy(self.address)
            new_person_addr.id = None
            new_person_addr.save(force_insert=True)
        new_person = copy.deepcopy(self)
        new_person.id = None
        try:
            new_person.baseperson_ptr_id = None
        except AttributeError:
            pass
        new_person.address = new_person_addr
        new_person.save(force_insert=True)
        try:
            new_person_pid = copy.deepcopy(self.personid)
            new_person_pid.id = None
            new_person_pid.person = new_person
            new_person_pid.save(force_insert=True)
        except PersonID.DoesNotExist:
            pass
        return new_person

    def save(self, *args, **kwargs):
        self.first_name = capitalize(self.first_name).strip('*')
        self.last_name = capitalize(self.last_name).strip('*')
        self.middle_name = capitalize(self.middle_name).strip('*')
        super(BasePerson, self).save(*args, **kwargs)

    def get_birth_date(self):
        if not self.birth_date:
            return None
        birth_date = UnclearDate(self.birth_date.year, self.birth_date.month, self.birth_date.day)
        if self.birth_date_no_day:
            birth_date.day = None
        if self.birth_date_no_month:
            birth_date.month = None
        return birth_date

    def set_birth_date(self, ubd):
        self.birth_date = ubd
        if ubd:
            if ubd.no_day:
                self.birth_date_no_day = True
            if ubd.no_month:
                self.birth_date_no_month = True

    unclear_birth_date = property(get_birth_date, set_birth_date)

    def unclear_birth_date_str(self):
        return self.unclear_birth_date and self.unclear_birth_date.strftime('%d.%m.%Y') or ''

    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name', ]
        verbose_name = _("физ. лицо")
        verbose_name_plural = _("физ. лица")

class DeadPersonMixin(object):

    def get_death_date(self):
        if not self.death_date:
            return None
        death_date = UnclearDate(self.death_date.year, self.death_date.month, self.death_date.day)
        if self.death_date_no_day:
            death_date.day = None
        if self.death_date_no_month:
            death_date.month = None
        return death_date

    def set_death_date(self, ubd):
        self.death_date = ubd
        if ubd:
            if ubd.no_day:
                self.death_date_no_day = True
            if ubd.no_month:
                self.death_date_no_month = True

    unclear_death_date = property(get_death_date, set_death_date)

class DeadPerson(DeadPersonMixin, BasePerson):
    """
    Мертвое ФЛ
    """
    # serialize=False - не выгружать значение поля в фикстуры. Для этого типа поля не описан сериализатор
    death_date = UnclearDateModelField(_("Дата смерти"), serialize=False, blank=True, null=True)

    def delete(self):
        try:
            self.deathcertificate.delete()
        except (AttributeError, DeathCertificate.DoesNotExist, ProtectedError):
            pass
        try:
            super(DeadPerson, self).delete()
        except (ProtectedError, BasePerson.DoesNotExist,):
            pass

class OrderDeadPerson(DeadPersonMixin, BasePerson):
    """
    Усопший, указываемый при заказе, для которого еще не сделано захоронение
    """
    # serialize=False - не выгружать значение поля в фикстуры. Для этого типа поля не описан сериализатор
    order = models.OneToOneField('orders.Order', verbose_name=_("Заказ"), on_delete=models.CASCADE)
    death_date = UnclearDateModelField(_("Дата смерти"), serialize=False, blank=True, null=True)

class AlivePerson(BasePerson, PhonesMixin):
    """
    Живое ФЛ с телефоном
    """
    phones = models.TextField(_("Телефоны (если несколько, то через ; или ,)"), blank=True, null=True)
    user = models.ForeignKey('auth.User', verbose_name=_("Ответственный за место или пользователь- физ. лицо"),
           null=True, editable=False, on_delete=models.CASCADE)
    # Оставляем здесь login_phone как хранилище для телефона логина ответственного,
    # для сохранения черновиков захоронений, а также для удобства отображения в формах.
    # Реальный телефон логина ответственного см. в self.user and self.user.customerprofile.login_phone.
    # Если пользователь меняет login_phone, то копия его попадет и сюда, т.е. будет поддерживаться:
    # self.login_phone == self.user.customerprofile.login_phone
    #
    login_phone = models.DecimalField(_("Мобильный телефон для входа в кабинет"), max_digits=15, decimal_places=0,
                  blank=True, null=True, db_index=True,
                  help_text=_('В международном формате, начиная с кода страны, без "+", например 79101234567'),
                  validators = [validate_phone_as_number, ],
                  editable=False)
    # phones: могут быть разных типов, пользуемся моделью persons.Phone
    # Для ответственных, сделана ли запись в журнале 
    is_inbook = models.BooleanField(_("Сделана отметка об ответственном в журнале захоронений (бумажном!)"), default=False, editable=False)

    def delete(self):
        self.phone_set.delete()
        try:
            super(AlivePerson, self).delete()
        except (ProtectedError, BasePerson.DoesNotExist,):
            pass

class DocumentSource(models.Model):
    name = models.CharField(_("Наименование органа"), max_length=255, unique=True)

    def __str__(self):
        return self.name

class PersonID(models.Model):
    """
    Удостоверение личности
    """

    person = models.OneToOneField(BasePerson, on_delete=models.CASCADE)
    id_type = models.ForeignKey(IDDocumentType, verbose_name=_("Тип документа"), blank=True, null=True, on_delete=models.CASCADE)
    series = models.CharField(_("Серия"), max_length=255, blank=True, default='')
    number = models.CharField(_("Номер"), max_length=255, blank=True, default='')
    source = models.ForeignKey(DocumentSource, verbose_name=_("Кем выдан"), blank=True, null=True, on_delete=models.CASCADE)
    date = models.DateField(_("Дата выдачи"), blank=True, null=True)
    date_expire = models.DateField(_("Срок действия"), blank=True, null=True)

    class Meta:
        verbose_name = _("Удостоверение личности")
        verbose_name_plural = _("Удостоверения личности")

    def __str__(self):
        return "%s %s %s" % (self.id_type, self.series, self.number)

    def save(self, *args, **kwargs):
        self.series = self.series.upper()
        super(PersonID, self).save(*args, **kwargs)

class DeathCertificate(BaseModel):
    """
    Свидетельство о смерти. Или медицинская справка
    """
    PROFILE_ZAGS = 'zags'
    PROFILE_MEDIC = 'medic'
    PROFILE_TYPES = (
        (PROFILE_ZAGS, _("Свидетельство о смерти")),
        (PROFILE_MEDIC, _("Медицинская справка")),
    )

    person = models.OneToOneField(DeadPerson, on_delete=models.CASCADE)

    type = models.CharField(_("Тип"), max_length=255, choices=PROFILE_TYPES, default=PROFILE_ZAGS)
    s_number = models.CharField(_("Номер"), max_length=255, blank=True, default='')
    series = models.CharField(_("Серия"), max_length=255, blank=True, default='')
    release_date = models.DateField(_("Дата выдачи"), null=True, blank=True)
    zags = models.ForeignKey(Org, verbose_name=_("ЗАГС"), null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("свидетельство о смерти")
        verbose_name_plural = _("свидетельства о смерти")

    def __str__(self):
        return _("Свид. о смерти (%s)") % str(self.person)

    def save(self, *args, **kwargs):
        self.series = self.series.upper()
        super(DeathCertificate, self).save(*args, **kwargs)

    def delete(self):
        try:
            self.deathcertificatescan.delete()
        except (AttributeError, DeathCertificateScan.DoesNotExist, ProtectedError):
            pass
        try:
            super(DeathCertificate, self).delete()
        except ProtectedError:
            pass

    def get_burial(self):
        """
        Получить захоронение, в котором усопший с этим СоС
        
        Имеется недостатки в проектировании таблиц б.д.:
        - теоретически может быть один усопший на несколько
          захоронений (Burial.deadman is a ForeignKey)
        - может быть усопший, но не "привязан" ни к какому
          захоронению
        Посему теоретически функция может вернуть или
        первого из нескольких захоронений этого усопшего,
        или вообще ничего не вернуть.
        """
        burial = None
        if self.pk:
            try:
                burial = self.person.burial_set.all()[0]
            except IndexError:
                pass
        return burial
        
class DeathCertificateScan(Files):
    """
    Файлы-сканы свидетельства о смерти, по одному на СоС
    """
    deathcertificate = models.OneToOneField(DeathCertificate, on_delete=models.CASCADE)


class Phone(BaseModel):
    PHONE_TYPE_MOBILE = 0
    PHONE_TYPE_CITY = 1
    PHONE_TYPE_FAX = 2
    PHONE_TYPE_OTHER = 3

    PHONE_TYPE_CHOICES = (
        (PHONE_TYPE_MOBILE, _("Мобильный")),
        (PHONE_TYPE_CITY, _("Городской")),
        (PHONE_TYPE_FAX, _("Факс")),
        (PHONE_TYPE_OTHER, _("Иной"))
    )

    ct = models.ForeignKey('contenttypes.ContentType', null=True, blank=True, editable=False, verbose_name=_("Тип"), on_delete=models.CASCADE)
    obj_id = models.PositiveIntegerField(null=True, blank=True, editable=False, verbose_name=_("ID объекта"), db_index=True)
    obj = GenericForeignKey(ct_field='ct', fk_field='obj_id')
    number = models.CharField(_("Номер"), max_length=50, blank=True)
    phonetype = models.SmallIntegerField(_("Тип телефона"), choices=PHONE_TYPE_CHOICES, default=PHONE_TYPE_CITY)

    class Meta:
        verbose_name = _("телефон")
        verbose_name_plural = _("Телефоны")

    def __str__(self):
         for k, v in self.PHONE_TYPE_CHOICES:  
             if k == self.phonetype:  
                 return "%s: %s" % (v, self.number)

    @classmethod
    def create_default_phones(cls, instance, phones):
        """
        Создать массив телефонов с типом по умолчанию
        """
        instance.phone_set.delete()
        ct = ContentType.objects.get_for_model(instance)
        for phone in phones:
            cls.objects.create(
                ct=ct,
                obj_id=instance.pk,
                number=phone.lstrip('+'),
            )

class CustomPlace(LocationMixin, BaseModel):
    name = models.CharField(_("Название"), max_length=255, blank=True)
    address = models.ForeignKey(Location, verbose_name=_("Адрес"), null=True, on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', verbose_name=_("Ответственный за место или указавший место"), on_delete=models.CASCADE)
    place = models.ForeignKey('burials.Place', verbose_name=_("Место"), null=True, on_delete=models.CASCADE)
    # Основное фото места. Оно не грузится от клиента, а копируется из PlacePhoto
    # или из результатов выполнения заказа, как только появляется новое фото места или
    # новый результат заказа, привязанного к этому customPlace. Параметр upload_to
    # указывается, потому что обязателен
    #
    title_photo = models.ImageField(_("Основное Фото"), upload_to='.', null=True)
    favorite_performer = models.ForeignKey(Org, verbose_name=_("Предпочтительный исполнитель"),
                                           null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField(_("Комментарий"), null=True)


    class Meta:
        unique_together = ('user', 'place', )

    @classmethod
    def get_or_create_from_place(cls, user, place):
        customplace, created_ = CustomPlace.objects.get_or_create(user=user, place=place)
        if created_ and place.lat is not None and place.lng is not None:
            address = Location.objects.create(gps_x=place.lng, gps_y=place.lat)
            customplace.address = address
            customplace.save()
        return customplace, created_

    def add_custom_deadman(self, burial):
        """
        Добавить копию усопшего (CustomPerson) из Burial
        """
        deadman = burial.deadman
        if deadman:
            customperson, created_ = CustomPerson.objects.get_or_create(
                customplace=self,
                person=deadman.baseperson_ptr,
                defaults=dict(
                    user=self.user,
                    last_name=deadman.last_name,
                    first_name=deadman.first_name,
                    middle_name=deadman.middle_name,
                    is_dead=True,
                    birth_date=deadman.birth_date,
                    death_date=deadman.death_date,
            ))

    def fill_custom_deadmen(self):
        """
        Заполнить место, привязанное к place от омс копиями усопших (CustomPersons)
        """
        if self.place:
            for burial in self.place.burials_available_closed():
                self.add_custom_deadman(burial)

    def save(self, *args, **kwargs):
        # При создании нового CustomPlace, если к нему привязано Place
        # от ОМС, заполнить title_photo самой свежей из PlacePhoto
        if not self.pk and self.place:
            PlacePhoto = get_model('burials', 'PlacePhoto')
            try:
                self.title_photo = PlacePhoto.objects.filter(place=self.place). \
                                   order_by('-date_of_creation')[0].bfile
            except IndexError:
                pass
        return super(CustomPlace, self).save(*args, **kwargs)

    def update_title_photo(self, photo):
        self.title_photo = photo
        self.save()

    def oms_data(self):
        place = self.place
        if place:
            return dict(
                address=place.address(),
                location=place.location_dict(),
            )
        else:
            return None

    def delete(self):
        for customperson in CustomPerson.objects.filter(customplace=self):
            customperson.customplace = None
            customperson.save()

        Order = get_model('orders', 'Order')
        OrderComment = get_model('orders', 'OrderComment')
        for order in Order.objects.filter(customplace=self):
            user = order.applicant and order.applicant.user or None
            if user:
                comment = _('Место, относящееся к заказу, удалено.')
                if self.address:
                    comment += "\n" + _('Адрес: %s.') % self.address
                    if self.address.gps_x is not None and self.address.gps_y is not None:
                        comment += "\n" + _('Координаты: широта: %s, долгота: %s.') % (
                            self.address.gps_y,
                            self.address.gps_x,
                        )
                OrderComment.objects.create(
                    order=order,
                    user=user,
                    comment=comment,
                )
            order.customplace = None
            order.save()

        super(CustomPlace, self).delete()
        try:
            self.address.delete()
        except (AttributeError, IntegrityError):
            pass

    def location(self):
        """
        Координаты, а если не заданы, то ОМС-места, если есть привязка
        """
        if self.address and \
           self.address.gps_y is not None and \
           self.address.gps_x is not None:
            return dict(
                latitude=self.address.gps_y,
                longitude=self.address.gps_x,
            )
        elif self.place:
            return self.place.location()
        else:
            return None

class CustomPerson(PersonMixin, PhotoModel, BaseModel):
    """
    Человек, чаще усопший, но возможно живой
    """

    PERMISSION_PRIVATE = 'private'
    PERMISSION_PUBLIC = 'public'
    PERMISSION_SELECTED = 'selected'
    PERMISSION_CHOICES = (
        (PERMISSION_PRIVATE, _("Личное")),
        (PERMISSION_PUBLIC, _("В публичном доступе")),
        (PERMISSION_SELECTED, _("Выборочно"))
    )

    class Meta:
        ordering = ('last_name', 'first_name', 'middle_name', )

    # Регистрируемые в ОМС усопшие получают копию в этой таблице.
    # Поскольку предполагается здесь хранить и живых лиц, то
    # ссылку делаем на Person, как живое, так и мертвое.
    #
    user = models.ForeignKey('auth.User', verbose_name=_("Владелец или указавший захороненного"), on_delete=models.CASCADE)
    customplace = models.ForeignKey(CustomPlace, verbose_name=_("Место захоронения"), blank=True, null=True, on_delete=models.CASCADE)
    person = models.ForeignKey(BasePerson, verbose_name=_("Лицо"), null=True, on_delete=models.CASCADE)
    last_name = models.CharField(_("Фамилия"), max_length=255, blank=True)
    first_name = models.CharField(_("Имя"), max_length=255, blank=True)
    middle_name = models.CharField(_("Отчество"), max_length=255, blank=True)
    birth_date = UnclearDateModelField(_("Дата рождения"), blank=True, null=True)
    death_date = UnclearDateModelField(_("Дата смерти"), blank=True, null=True)
    is_dead = models.BooleanField(_("Уcопший"), default=True)
    memory_text = models.TextField(_("Памятный текст"), null=True)
    permission = models.CharField(_("Разрешение"), max_length=255,
                                  choices=PERMISSION_CHOICES, default=PERMISSION_PRIVATE)
    # Для сайта с благодарностями от пользователей:
    token = models.CharField(_("Токен"), max_length=255, null=True, editable=False, unique=True)
    thank_site = models.URLField(_("Сайт для благодарностей"), null=True, editable=False)

    def delete(self):
        for memorygallery in MemoryGallery.objects.filter(customperson=self):
            memorygallery.delete()
        for permission in CustomPersonPermission.objects.filter(customperson=self):
            permission.delete()
        return super(CustomPerson, self).delete()

    def oms_data(self):
        try:
            deadman = self.person.deadperson
            burial = deadman.burial_set.all()[0]
        except (AttributeError, DeadPerson.DoesNotExist, IndexError,):
            return None
        return dict(
            lastName=deadman.last_name,
            firstName=deadman.first_name,
            middleName=deadman.middle_name,
            birthDate = deadman.birth_date and deadman.birth_date.str_safe() or None,
            deathDate = deadman.death_date and deadman.death_date.str_safe() or None,
            grave = burial.grave_number,
        )

class MemoryGallery(Files):
    """
    Страницы памяти у CustomPerson
    """
    TYPE_IMAGE = 'image'
    TYPE_VIDEO = 'video'
    TYPE_TEXT = 'text'
    TYPE_LINK = 'link'
    TYPE_CHOICES = (
        (TYPE_IMAGE, _("Фото")),
        (TYPE_VIDEO, _("Видео")),
        (TYPE_TEXT, _("Текст")),
        (TYPE_LINK, _("Ссылка")),
    )

    PERMISSION_PRIVATE = 'private'
    PERMISSION_PUBLIC = 'public'
    PERMISSION_SELECTED = 'selected'
    PERMISSION_CHOICES = (
        (PERMISSION_PRIVATE, _("Личное")),
        (PERMISSION_PUBLIC, _("В публичном доступе")),
        (PERMISSION_SELECTED, _("Выборочно"))
    )

    # Мегабайт:
    MAX_IMAGE_SIZE = 10

    customperson = models.ForeignKey(CustomPerson, on_delete=models.CASCADE)
    type = models.CharField(_("Тип"), max_length=255, choices=TYPE_CHOICES)
    text = models.TextField(_("Текст"), null=True)
    event_date = UnclearDateModelField(_("Дата события"), null=True)
    permission = models.CharField(_("Разрешение"), max_length=255,
                                  choices=PERMISSION_CHOICES, default=PERMISSION_PRIVATE)

    def delete(self):
        MemoryGalleryPermission.objects.filter(memorygallery=self).delete()
        return super(MemoryGallery, self).delete()

class CustomPersonPermission(models.Model):
    """
    Разрешения на страницу CustomPerson

    Применяется, если разрешение в записи CustomPerson прописано как selected.
    Тогда доступ предоставляется или по email или по login_phone,
    если один из таковых прописан в разрешениях в этой модели
    """

    customperson = models.ForeignKey(CustomPerson, on_delete=models.CASCADE)
    email = models.EmailField(_("Email"), null=True)
    login_phone = models.DecimalField(_("Мобильный телефон для входа в кабинет"),
                                      max_digits=15, decimal_places=0, null=True)

class MemoryGalleryPermission(models.Model):
    """
    Разрешения на страницу памяти (MemoryGallery)

    Применяется, если разрешение в записи MemoryGallery прописано как selected.
    Тогда доступ предоставляется или по email или по login_phone,
    если один из таковых прописан в разрешениях в этой модели
    """

    memorygallery = models.ForeignKey(MemoryGallery, on_delete=models.CASCADE)
    email = models.EmailField(_("Email"), null=True)
    login_phone = models.DecimalField(_("Мобильный телефон для входа в кабинет"),
                                      max_digits=15, decimal_places=0, null=True)
