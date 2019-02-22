# coding=utf-8

import re, datetime, os
from LatLon import LatLon, Latitude, Longitude
import geohash, uuid

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError, connection
from django.db.models.query_utils import Q
from django.db.models import Count, Avg, Min, Max
from django.shortcuts import redirect, render, get_object_or_404
from django.http import Http404, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from django.utils.translation import ugettext as _
from django.utils.formats import localize
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView

from django.contrib.contenttypes.models import ContentType

from geo.models import Country, Region, Street, City

from pd.views import RequestToFormMixin, FormInvalidMixin, get_front_end_url, ServiceException
from pd.models import UnclearDate, validate_phone_as_number, SafeDeleteMixin
from pd.utils import utcisoformat, re_search, dictfetchall

from burials.forms import AreaFormset, AddOrgForm, \
                          BurialfileCommentEditForm, BurialCommentEditFormSet, \
                          AddGravesForm
from burials.models import Cemetery, Place, Area, BurialFiles, Grave, Burial, BurialComment, AreaPhoto, PlacePhoto, \
                           ExhumationRequest, AreaPurpose, PlaceSize
from burials.burials_views import *
from logs.models import write_log, log_object, prepare_m2m_log, compare_obj, LogOperation, DeleteLog
from django.contrib.auth.models import User
from users.models import Profile, Org, CustomerProfile, PermitIfUgh, PermitIfTrade, Role, \
                         is_loru_user, is_ugh_user
from users.views import SupervisorRequiredMixin, UGHRequiredMixin, UghOrLoruRequiredMixin, ApiClientSiteMixin
from persons.models import Phone, AlivePerson, CustomPlace
from geo.models import Location
from restthumbnails.files import ThumbnailContentFile

from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, detail_route, list_route
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework_jsonp.renderers import JSONPRenderer
from rest_framework.parsers import MultiPartParser, JSONParser

from django.db import transaction

from serializers import CemeterySerializer, AreaSerializer, PlaceSerializer, AreaPurposeSerializer, \
    GraveSerializer, BurialSerializer, BurialListSerializer, BurialPutGraveSerializer, \
    AreaPhotoSerializer, PlaceSizeSerializer, \
    ApiOmsPlacesSerializer, ApiCatalogPlacesSerializer, PlaceLockSerializer, \
    CemeteryTitleSerializer, AreaTitleSerializer, PlaceTitleSerializer, \
    CemeteryClientSiteSerializer, ApiClientSitePlacesSerializer

from persons.serializers import AlivePersonSerializer, PhoneSerializer
from users.serializers import UserFioLoginSerializer, ProfileFioLoginSerializer
from geo.serializers import LocationStaticSerializer, LocationDataSerializer
from logs.serializers import PlaceLogSerializer

from logs.views import getLogQuerySet

from sms_service.utils import send_sms

class EditCemeteryObjectsMixin(object):

    def getCemetery(self, request):
        try:
            # PUT request issue
            cemetery_id = int(request.GET.get('cemetery_id'))
            assert cemetery_id>0, u'Wrong id'
        except:
            raise Http404()
        else:
            return get_object_or_404(Cemetery, id=cemetery_id, ugh=request.user.profile.org)

    def getArea(self, request):
        try:
            # PUT request issue
            area_id = int(request.GET.get('area_id'))
            assert area_id>0, u'Wrong id'
        except:
            raise Http404()
        else:
            return get_object_or_404(Area, id=area_id, cemetery__ugh=request.user.profile.org)

    def getPlace(self, request):
        try:
            # PUT request issue
            place_id = int(request.GET.get('place_id'))
            assert place_id>0, u'Wrong id'
        except:
            raise Http404()
        else:
            return get_object_or_404(Place, id=place_id, cemetery__ugh=request.user.profile.org)

    def make_error_data(self, messages):
        if isinstance(messages, basestring):
            errors = (messages,)
        else:
            errors = messages
        return {"__all__": errors}

class CaretakerMixin(object):

    def get_caretakers(self, obj):
        if isinstance(obj, Cemetery):
            ugh = obj.ugh
        else:
        # Area. Place
            ugh = obj.cemetery.ugh
        return [
            UserFioLoginSerializer(user).data \
                for user in User.objects.filter(
                                profile__org=ugh,
                                profile__out_of_staff=False,
                                profile__role__name__in=(Role.ROLE_REGISTRATOR, Role.ROLE_CARETAKER,),
                                is_active=True,
                            ).order_by(
                                'profile__user_last_name',
                                'profile__user_first_name',
                                'profile__user_middle_name',
                              ).distinct()
        ]


class CemeteryViewSet(EditCemeteryObjectsMixin, CaretakerMixin, viewsets.ModelViewSet):
    model = Cemetery
    serializer_class = CemeterySerializer
    permission_classes = (PermitIfUgh,)

    MSG_ALREADY_EXISTS = _(u"Кладбище с таким названием уже существует")

    def get_queryset(self):
        return  Cemetery.objects.filter(ugh=self.request.user.profile.org).all()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = self.model(**serializer.validated_data)
        obj.creator = self.request.user
        obj.ugh = self.request.user.profile.org
        try:
            with transaction.atomic():
                obj.save(force_insert=True)
        except IntegrityError:
            return Response(status=400, data=self.make_error_data(self.MSG_ALREADY_EXISTS))
        write_log(self.request, obj, _(u"Кладбище создано"))
        write_log(self.request, self.request.user.profile.org,
                    _(u"Создано кладбище '%s'") % obj.name)
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=201)

    @transaction.atomic
    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                super(CemeteryViewSet, self).perform_update(serializer)
        except IntegrityError:
            raise ServiceException(self.MSG_ALREADY_EXISTS)
        self.post_update(self.get_object())

    def update(self, request, *args, **kwargs):
        try:
            result = super(CemeteryViewSet, self).update(request, *args, **kwargs)
        except ServiceException as excpt:
            result = Response(status=400, data=self.make_error_data(excpt.message))
        return result

    def post_update(self, obj):
        old_lat = obj.address and obj.address.gps_y or None
        old_lng = obj.address and obj.address.gps_x or None
        address = self.request.data.get('obj_address')
        address_serializer = LocationDataSerializer(obj.address, data=address, partial=True)
        
        address_serializer.is_valid(raise_exception=True)

        obj.address = address_serializer.save()
        obj.address.set_related_addr(data=address)
        coords_by_address = False
        if obj.address and \
           (obj.address.gps_y is None or obj.address.gps_x is None):
            location = obj.address.get_yandex_coords()
            if location:
                obj.address.gps_y = location['latitude']
                obj.address.gps_x = location['longitude']
                coords_by_address = True
        obj.address.save()
        obj.save()
        
        write_log(self.request, obj,_(u'Кладбище изменено'))
        if coords_by_address:
            write_log(
                self.request,
                obj,
                _(u"Назначены координаты по адресу\n широта: %(lat)s, долгота: %(lng)s") % dict(
                    lat=obj.address.gps_y,
                    lng=obj.address.gps_x,
            ))
        elif obj.address.gps_y != old_lat or obj.address.gps_x != old_lng:
            write_log(
                self.request,
                obj,
                _(u"Изменены координаты\n широта: %(lat)s, долгота: %(lng)s") % dict(
                    lat=obj.address.gps_y,
                    lng=obj.address.gps_x,
            ))

        phone = self.request.data.get('obj_phones', [])
        id_binds = {}
        ct = ContentType.objects.get_for_model(obj)

        for i in phone:
            i["ct"] = ct.pk
            try:
                phone_obj = obj.phone_set.get(pk=i['id'])
            except:
                phone_obj = None
            phone_serializer = PhoneSerializer(phone_obj, data=i)
            if not phone_serializer.is_valid():
                return Response(status=400, data=phone_serializer.errors)
            res = phone_serializer.save()
            res.obj_id = obj.pk
            res.save()
            id_binds[res.id] = 1
        obj.phone_set.exclude(pk__in=id_binds.keys()).delete()

    @detail_route(methods=['GET',])
    def getform(self, request, pk=None):
        cemetery = get_object_or_404(self.get_queryset(), pk=pk)
        data = {
                "cemetery" : CemeterySerializer(cemetery, context=dict(request=request)).data,
                "responsible_phones" : [],
                "responsible_address" : {}
                }
        phone_set = cemetery.phone_set.all()
        data["phones"] = PhoneSerializer(phone_set, many=True).data
        data["cemetery"]["max_graves_count"] = request.user.profile.org.max_graves_count
        if cemetery.address:
            data["address"] = LocationStaticSerializer(cemetery.address).data
        data['caretakers'] = self.get_caretakers(cemetery)
        data['can_add_area'] = cemetery in Cemetery.editable_ugh_cemeteries(request.user)
        data['is_editable'] = request.user.profile.is_admin() or data['can_add_area']
        return Response(status=200, data=data)

    @detail_route(methods=['GET',])
    def authdata0(self, request, pk=None):
        return Response(
            status=200,
            data =dict(
                can_add_cemetery=request.user.profile.is_admin() or \
                                 request.user.profile.is_registrator_or_caretaker(),
            ))

    @detail_route(methods=['GET',])
    def authdata(self, request, pk=None):
        """
        Данные для создания/редактирования кладбища
        
        -   id текущего пользователя, если это смотритель: он предлагается 
            как единственный cemetery editor
        -   список всех регистраторов организации
        -   список pk всех текущих регистраторов кладбища
        -   нужен ли код кладбища, - используемый только для выгрузки
            в реестр, а для этого нужно разрешение на ид у усопшего
        -   есть ли допуск к Yandex картам
        """
        profile = request.user.profile
        if profile.is_registrator_or_caretaker():
            profile_pk = profile.pk
        else:
            profile_pk = None
        return Response(
            status=200,
            data=dict(
                profile_pk=profile_pk,
                ugh_registrators=self.get_ugh_registrators(request.user.profile.org),
                cemetery_editors_pks=self.get_cemetery_editors_pks(pk),
                need_code = settings.DEADMAN_IDENT_NUMBER_ALLOW,
        ))

    @detail_route(methods=['GET',])
    def iseditable(self, request, pk=None):
        cemetery = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(status=200, data=dict(
            is_editable=cemetery in Cemetery.editable_ugh_cemeteries(request.user)
        ))

    def get_ugh_registrators(self, org):
        return [
                ProfileFioLoginSerializer(p).data for p in Profile.objects.filter(
                    org=org,
                    role__name=Role.ROLE_REGISTRATOR,
                ).distinct()
        ]

    def get_cemetery_editors_pks(self, pk):
        if pk == "0":
            pk = None
        if pk:
            cemetery = get_object_or_404(Cemetery, pk=pk)
            return [
                    p.pk for p in Profile.objects.filter(
                        cemeteries=cemetery,
                        role__name=Role.ROLE_REGISTRATOR,
                    ).distinct()
            ]
        else:
            return []

class CemeteryEditorsView(APIView):
    permission_classes = (PermitIfUgh,)

    def put(self, request):
        cemetery = get_object_or_404(
            Cemetery,
            pk=request.data.get('cemetery_id'),
            ugh=request.user.profile.org)
        previous_profiles = Profile.objects.filter(
                cemeteries=cemetery,
                role__name=Role.ROLE_REGISTRATOR,
            ).distinct()
        new_cemetery_editor_ids = request.data.get('cemetery_editors_pks', [])
        new_profiles = [Profile.objects.get(pk=id_) for id_ in new_cemetery_editor_ids]

        previous_profiles = set(previous_profiles)
        new_profiles = set(new_profiles)

        # set with elements in previous_profiles but not in new_profiles
        #
        to_delete = previous_profiles - new_profiles

        # set with elements in new_profiles but not in previous_profiles
        #
        to_add = new_profiles - previous_profiles
        
        for profile in to_delete:
            profile.cemeteries.remove(cemetery)
            write_log(request, profile, _(u"Отменен доступ к кладбищу '%s'") % cemetery)
        for profile in to_add:
            profile.cemeteries.add(cemetery)
            write_log(request, profile, _(u"Добавлен доступ к кладбищу '%s'") % cemetery)
        return Response({}, status=200)

api_cemeteries_editors = CemeteryEditorsView.as_view()

class AreaViewSet(EditCemeteryObjectsMixin, CaretakerMixin, viewsets.ModelViewSet):
    model = Area
    serializer_class = AreaSerializer
    permission_classes = (PermitIfUgh,)

    def get_queryset(self):
        item = self.getCemetery(self.request)
        return self.model.objects.filter(cemetery=item)

    def check_new_area(self, area):
        if area.kind != Area.KIND_GRAVES and area.places_count > 1:
            area.places_count = 1
            area.save()
        serializer = self.get_serializer(area)
        return serializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        area = self.model(**serializer.validated_data)
        area.cemetery = self.getCemetery(self.request)
        area.save(force_insert=True)
        serializer = self.check_new_area(area)
        write_log(request, area.cemetery, _(u'Создан участок: %s') % area)
        return Response(serializer.data, status=201)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        area = self.get_object()
        kind = request.data.get('kind')
        if area and kind and kind != Area.KIND_GRAVES and \
        Place.objects.filter(area=area, kind_crypt=True).exists():
            data = self.make_error_data(_(u"Здесь есть склеп(ы): нельзя в колумбарии"))
            return Response(status=400, data=data)
        serializer = self.get_serializer(area, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.check_new_area(area)
        write_log(request, area, _(u'Участок изменен'))
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        area = self.get_object()
        serializer = self.get_serializer(area)
        data = serializer.data
        data["max_graves_count"] = request.user.profile.org.max_graves_count
        data['caretakers'] = self.get_caretakers(area)
        return Response(data)

class ApiOmsPlacesViewSet(viewsets.ReadOnlyModelViewSet):
    model = Place
    serializer_class = ApiOmsPlacesSerializer
    permission_classes = (PermitIfUgh,)

    def get_queryset(self):
        return Place.objects.filter(
            cemetery__ugh=self.request.user.profile.org,
            lat__isnull=False,
            lng__isnull=False,
        ).distinct()

class ApiCatalogPlacesViewSet(viewsets.ReadOnlyModelViewSet):
    model = Place
    serializer_class = ApiCatalogPlacesSerializer

    def get_queryset(self):
        q = Q(
            lat__isnull=False,
            lng__isnull=False,
        )
        statuses = self.request.GET.getlist('filter[status]')
        while statuses.count(u''):
            statuses.remove(u'')
        qs = None
        for status in statuses:
            if status in Place.STATUS_LIST:
                this_status = { "%s__isnull" % status: False }
                if qs is None:
                    qs = Q(**this_status)
                else:
                    qs |= Q(**this_status)
        if qs is not None:
            q &= qs
        return Place.objects.filter(q).distinct()


class PlaceViewSet(EditCemeteryObjectsMixin, SafeDeleteMixin, CaretakerMixin, viewsets.ModelViewSet):
    model = Place
    serializer_class = PlaceSerializer
    permission_classes = (IsAuthenticated,)

    old_place = None
    old_responsible = None
    old_responsible_address = None

    def get_queryset(self):
        item = self.getCemetery(self.request)
        qs = self.model.objects.filter(cemetery=item)
        if self.request.GET.get('area_id'):
            area  = self.getArea(self.request)
            qs = qs.filter(area=area)
        return qs

    @transaction.atomic
    def perform_create(self, serializer):
        super(PlaceViewSet, self).perform_create(serializer)
        data = serializer.data
        area = Area.objects.get(pk=data['area'])
        place = Place.objects.get(
            area=area,
            row=data['row'],
            place=data['place']
        )
        place.get_or_create_graves(area.places_count)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            place = self.get_object()
            serializer = self.get_serializer(place, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.pre_update(place)
            super(PlaceViewSet, self).perform_update(serializer)
            place = self.post_update()
            serializer = self.get_serializer(place)
            return Response(serializer.data)
        except ServiceException as excpt:
            result = Response(status=400, data=self.make_error_data(excpt.message))
        return result

    def pre_update(self, place):
        place = self.get_object()
        self.old_place = place
        self.old_responsible = place.responsible
        self.old_responsible_address = place.responsible and place.responsible.address or None

    def post_update(self):
        request = self.request
        data = request.data
        place = self.get_object()
        new_msg = []

        responsible = data.get('obj_responsible')
        if responsible and responsible.get('login_phone'):
            try:
                validate_phone_as_number(responsible['login_phone'])
            except (TypeError, ValidationError, ):
                raise ServiceException(_(u"Неверный формат телефона ответственного"))

        if place.lat is not None and place.lng is not None:
            # Если у места есть CustomPlace, а координаты в CustomPlace
            # не заданы, задаем
            for customplace in CustomPlace.objects.filter(
                place=place,
                address__gps_x__isnull=True,
                address__gps_y__isnull=True,
            ):
                if customplace.address:
                    address = customplace.address
                else:
                    address = Location()
                address.gps_x = customplace.place.lng
                address.gps_y = customplace.place.lat
                address.save()
                if not customplace.address:
                    customplace.address = address
                    customplace.save()

        for b in Burial.objects.filter(place=place). \
                    filter(~Q(row=place.row) | ~Q(place_number=place.place)):
            write_log(
                self.request,
                b,
                _(
                    u"Изменение ряда и/или номера места при правке места\n"
                    u"Ряд: '%(old_row)s' -> '%(new_row)s'\n"
                    u"Номер места: '%(old_place)s' -> '%(new_place)s'\n"
                    ) % dict(
                        old_row=b.row,
                        new_row=place.row,
                        old_place=b.place_number,
                        new_place=place.place,
            ))
            b.row = place.row
            b.place_number = place.place
            if b.is_valid_for_register():
                # есть изменения, существенные для регистра
                b.dt_register = datetime.datetime.now()
            b.save()

        if responsible:
            responsible_serializer =  AlivePersonSerializer(place.responsible, data=responsible, partial=True)
            if not responsible_serializer.is_valid():
                raise ServiceException(_(u"Неверные данные ответственного"))
            place.responsible = responsible_serializer.save()
            place.responsible.save()
            place.save()

            if place.responsible.login_phone and \
              (not self.old_responsible or not self.old_responsible.login_phone):
                try:
                    customerprofile = CustomerProfile.objects.get(login_phone=place.responsible.login_phone)
                    user = customerprofile.user
                    text=_(u'Место %s прикреплено.') % place.pk
                    email_error_text = _(u"Пользователь %s (телефон %s) не смог получить СМС после прикрепления места %s" % \
                                        (customerprofile.user.username, place.responsible.login_phone, place.pk,))
                except CustomerProfile.DoesNotExist:
                    user, password = CustomerProfile.create_cabinet(place.responsible, self.request)
                    text=_(u'%s login: %s parol: %s') % (
                        get_front_end_url(self.request).rstrip('/'),
                        place.responsible.login_phone,
                        password,
                    )
                    email_error_text = _(u"Пользователь %s не смог получить пароль после закрытия захоронения" % \
                                        (place.responsible.login_phone,))
                customplace, created_ = CustomPlace.get_or_create_from_place(user=user, place=place)
                if not place.responsible.user:
                    place.responsible.user = user
                if created_:
                    customplace.fill_custom_deadmen()
                if not settings.DEBUG:
                    sent, message = send_sms(
                        phone_number=place.responsible.login_phone,
                        text=text,
                        email_error_text=email_error_text,
                        user=self.request.user,
                    )
            address = data.get('obj_responsible_address')
            address_serializer = LocationDataSerializer(place.responsible.address, data=address, partial=True)
            if address_serializer.is_valid():
                place.responsible.address = address_serializer.save()
                place.responsible.address.set_related_addr(data=address)
            else:
                raise ServiceException(_(u"Неверные данные адреса ответственного"))
            place.responsible.save()

            phone = data.get('obj_responsible_phones', [])
            id_binds = {}
            ct = ContentType.objects.get_for_model(place.responsible)

            for i in phone:
                i["ct"] = ct.pk
                try:
                    phone_obj = place.responsible.phone_set.get(pk=i['id'])
                except:
                    phone_obj = None
                phone_serializer = PhoneSerializer(phone_obj, data=i)
                if phone_serializer.is_valid():
                    res = phone_serializer.save()
                    res.obj_id = place.responsible.pk
                    res.save()                
                    id_binds[res.id] = 1
            place.responsible.phone_set.exclude(pk__in=id_binds.keys()).delete()

            old_phones = [i for i in self.old_responsible.phone_set.all()] if self.old_responsible else []
            phone_set = place.responsible.phone_set.all()
            new_msg += prepare_m2m_log(_(u'Телефон ответственного'), old_phones,  phone_set)

            if unicode(self.old_responsible_address)!= unicode(place.responsible.address):
                new_msg += [compare_obj(_(u'Адрес ответственного'), self.old_responsible_address, place.responsible.address)]

        responsible_changed = False
        if unicode(self.old_responsible) != unicode(place.responsible):
            new_msg += [compare_obj(_(u'Ответственный'), self.old_responsible, place.responsible)]
            if self.old_responsible:
                responsible_changed = True

        log_object(self.request, obj=place, old=self.old_place, new=place, reason=_(u'Изменено'), new_msg=new_msg)

        if place.responsible and (not self.old_responsible or responsible_changed):
            write_log(self.request, place, operation=LogOperation.PLACE_PASSPORT_ISSUED)
            
        if data.get('delete_responsible') and self.old_responsible:
            write_log(self.request, place, _(u'Ответственный %s откреплен') % self.old_responsible.full_name_complete())
            self.safe_delete('responsible', place)
        
        return place

    @detail_route(methods=['GET',])
    def getform(self, request, pk=None):
        cemetery = self.getCemetery(self.request)
        if self.request.GET.get('area_id'):
            area  = self.getArea(self.request)
        place = get_object_or_404(self.model, pk=pk, cemetery=cemetery, area=area)
        
        # Log set
        paginator = Paginator(getLogQuerySet(log_type="place", place=place), 10)
        page = request.GET.get('log_page')
        try:
            page = paginator.page(page)
        except:
            page = paginator.page(1)
        log_data = PlaceLogSerializer(page, many=True).data
        
        paginator = Paginator(place.grave_set.all(), 10)
        grave_page = request.GET.get('grave_page')
        try:
            grave_list = paginator.page(grave_page)
        except:
            grave_list = paginator.page(1)
        grave_count = place.grave_set.count()
        
        #burial_list = Burial.objects.filter(grave__place=place, grave__in=grave_list).all()
        data = {
                "cemetery" : CemeterySerializer(cemetery).data,
                "area" : AreaSerializer(area).data,
                "place" : PlaceSerializer(place, context={ 'request': request, }).data,
                "graves" : GraveSerializer(grave_list, many=True).data,
                "grave_count" : grave_count,
                "responsible" : {},
                "responsible_phones" : [],
                "responsible_address" : {},
                "log": log_data,
                "log_page":page.number,
                "log_pages":page.paginator.num_pages,
                "is_editable": cemetery in Cemetery.editable_ugh_cemeteries(request.user),
                "is_caretaker_only": request.user.profile.is_caretaker_only(), 
                }
        data["place"]["graves_count"] = place.get_graves_count()
        data["place"]["available_count"] = place.available_count
        if place.responsible:
            phone_set = place.responsible.phone_set.all()
            data["responsible_phones"] = PhoneSerializer(phone_set, many=True).data
            data["responsible"] = AlivePersonSerializer(place.responsible).data 
            if place.responsible.address:
                data["responsible_address"] = LocationStaticSerializer(place.responsible.address).data
        data['caretakers'] = self.get_caretakers(cemetery)
        data["max_graves_count"] = request.user.profile.org.max_graves_count
        return Response(status=200, data=data)


    @detail_route(methods=['GET',])
    def getgraves(self, request, pk=None):
        cemetery = self.getCemetery(self.request)
        if self.request.GET.get('area_id'):
            area  = self.getArea(self.request)
        place = get_object_or_404(Place, pk=pk, cemetery=cemetery, area=area)

        page = request.GET.get('grave_page')
        paginator = Paginator(place.grave_set.all(), 10)
        try:
            grave_list = paginator.page(page)
        except:
            grave_list = paginator.page(1)
        
        burial_list = Burial.objects.filter(grave__place=place, grave__in=grave_list).order_by('-fact_date')
        return Response({
                         'count': place.grave_set.count(),
                         'page': grave_list.number,
                         'pages': grave_list.paginator.num_pages,
                         'graves': GraveSerializer(grave_list, many=True).data,
                         'burials': BurialSerializer(burial_list, many=True).data,
                         })


    @detail_route(methods=['POST',])
    def setform(self, request, pk=None):
        form = request.GET.get('form')
        address = request.GET.get('address')
        phones = request.GET.get('phones')
        responcible = request.GET.get('responcible')
        return Response(status=200)


    @detail_route(methods=['DELETE',])
    def deletephoto(self, request, pk=None):
        photo_id = request.GET.get('photo_id')
        placePhoto = get_object_or_404(PlacePhoto, place=pk, pk=photo_id)
        if placePhoto.place.cemetery not in Cemetery.editable_ugh_cemeteries(request.user):
            raise HttpResponseForbidden
        msg = _(u"Удалено фото места:\n%s") % request.build_absolute_uri(placePhoto.bfile.url)
        placePhoto.delete()
        write_log(request, placePhoto.place, msg)
        return Response(status=200)

        
    @detail_route(methods=['GET',])
    def cancel_exhumation(self, request, pk=None):
        cemetery = self.getCemetery(self.request)
        if self.request.GET.get('area_id'):
            area  = self.getArea(self.request)
        place = get_object_or_404(Place, pk=pk, cemetery=cemetery, area=area)

        burial_id = request.GET.get('burial_id')
        burial = get_object_or_404(Burial, pk=burial_id, cemetery=cemetery)
        burial.place = place
        Place.objects.cancel_exhumation(request,  burial)
        return Response(status=200)


class AreaPurposeViewSet(viewsets.ModelViewSet):
    model = AreaPurpose
    serializer_class = AreaPurposeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.model.objects.all()


class GraveViewSet(viewsets.ModelViewSet):
    model = Grave
    serializer_class = GraveSerializer
    permission_classes = (PermitIfUgh,)

    def get_queryset(self):
        place = self.getPlace(self.request)
        return self.model.objects.filter(place=place).order_by('grave_number')

    @transaction.atomic
    def perform_create(self, serializer):
        super(GraveViewSet, self).perform_create(serializer)
        grave = self.model(**serializer.validated_data)
        msg = _(u"Могила %d создана") % grave.grave_number
        if grave.is_wrong_fio:
            msg = u"%s, %s" % (msg, _(u"Неверное ФИО"),)
        if grave.is_military:
            msg = u"%s, %s" % (msg, _(u"Воинская могила"),)
        write_log(self.request, grave.place, msg)
    
    def destroy(self, request, pk=None):
        try:
            grave = self.model.objects.get(pk=pk)
            grave.delete(request=request)
        except self.model.DoesNotExist:
            raise Http404()
        return Response(status=200)


class BurialViewSet(EditCemeteryObjectsMixin, viewsets.ModelViewSet):
    model = Burial
    serializer_class = BurialSerializer
    serializer_list_class = BurialListSerializer
    serializer_put_grave_class = BurialPutGraveSerializer
    permission_classes = (PermitIfUgh,)

    def get_queryset(self):
        return self.model.objects.filter(cemetery__ugh=self.request.user.profile.org)

    def filter_queryset(self, queryset):
        # place_id filter removed. Exhumation issue

        item = self.getCemetery(self.request)
        queryset = queryset.filter(cemetery=item)
        
        area_id = self.request.GET.get('area_id')
        item = get_object_or_404(Area, pk=area_id)
        queryset = queryset.filter(area=item)
        return  queryset

    def get_serializer_class(self):
        """
        Serilializer fetches a list of related items, result - resource overuse.
        Solution: replacement with easier serializer
        """
        if self.action == 'list':
            serializer_class = self.serializer_list_class
        elif self.action == 'update':
            serializer_class = self.serializer_put_grave_class
        else:
            serializer_class = self.serializer_class
        return serializer_class


    @transaction.atomic
    def perform_update(self, serializer):
        burial = self.get_object()
        old_grave_number = burial.grave_number
        super(BurialViewSet, self).perform_update(serializer)
        burial = self.get_object()
        if burial.grave_number != 0 and \
           burial.grave and \
           burial.place and \
           burial.grave_number != burial.grave.grave_number:
            grave = burial.place.get_or_create_graves(burial.grave_number)
            burial.grave = grave
            burial.save()
        if old_grave_number != burial.grave_number:
            write_log(
                self.request,
                burial,
                _(u'Могила %(old_grave_number)s -> %(new_grave_number)s') % dict(
                    old_grave_number=old_grave_number,
                    new_grave_number=burial.grave_number,
            ))


class AreaPhotoViewSet(EditCemeteryObjectsMixin, viewsets.ModelViewSet):
    model = AreaPhoto
    serializer_class = AreaPhotoSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        qs = self.model.objects.filter(area__cemetery__ugh=self.request.user.profile.org)
        item = self.getArea(self.request)
        qs = qs.filter(area=item)
        return  qs.all()


class PlaceSizeViewSet(viewsets.ModelViewSet):
    model = PlaceSize
    serializer_class = PlaceSizeSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None
    def get_queryset(self):
        qs = self.model.objects.filter(org=self.request.user.profile.org)
        return  qs.all()

class AddDoverView(UghOrLoruRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        prefix = kwargs.get('prefix') or ''
        f = AddDoverForm(data=request.POST, prefix='%sdover' % prefix)
        try:
            agent = Profile.objects.get(pk=request.GET['agent'], is_agent=True)
        except Profile.DoesNotExist:
            return HttpResponse(_(u'Агент не существует'), content_type='text/plain')
        except KeyError:
            return HttpResponse(_(u'Ошибка'), content_type='text/plain')
        if f.is_valid():
            dover = f.save(commit=False)
            dover.target_org = request.user.profile.org
            dover.agent = agent
            dover.save()
            return HttpResponse(json.dumps({'pk': dover.pk, 'label': u'%s' % dover}), content_type='application/json')
        else:
            err_str = _(u'Ошибка:\n%s')
            errors = '\n'.join([u'%s' % v for v in f.non_field_errors()])
            if "\n" in errors:
                err_str = _(u'Ошибки:\n%s')
            return HttpResponse(err_str % errors, content_type='text/plain')

add_dover = AddDoverView.as_view()

class AddAgentView(UghOrLoruRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        prefix = kwargs.get('prefix') or ''
        fa = AddAgentForm(data=request.POST, prefix='%sagent' % prefix)
        fd = AddDoverForm(data=request.POST, prefix='%sagent_dover' % prefix)
        if request.GET.get('org'):
            q = Q(pk=request.GET['org'])
        elif request.GET.get('org_name'):
            q = Q(name=request.GET['org_name'])
        else:
            return HttpResponse(_(u'Ошибка'), content_type='text/plain')
        try:
            org = Org.objects.get(q)
        except KeyError:
            return HttpResponse(_(u'Ошибка'), content_type='text/plain')
        except Org.DoesNotExist:
            return HttpResponse(_(u'Нет такой организации'), content_type='text/plain')
        if fa.is_valid() and fd.is_valid():
            agent = fa.save(org=org)
            dover = fd.save(commit=False)
            dover.target_org = request.user.profile.org
            dover.agent = agent
            dover.save()
            return HttpResponse(json.dumps({
                'org_pk': org.pk,
                'pk': agent.pk, 'label': u'%s' % agent,
                'dover_pk': dover.pk, 'dover_label': u'%s' % dover
            }), content_type='application/json')
        else:
            err_str = _(u'Ошибка:\n%s')
            errors = '\n'.join([u'%s' % v for v in fa.non_field_errors()] + \
                               [u'%s' % v for v in fd.non_field_errors()])
            if "\n" in errors:
                err_str = _(u'Ошибки:\n%s')
            return HttpResponse(err_str % errors, content_type='text/plain')

add_agent = AddAgentView.as_view()

class AddOrgView(UghOrLoruRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if kwargs.get('type'):
            prefix = kwargs['type']
            instance = Org(type=kwargs['type'])
        else:
            prefix='org'
            instance = None
        f = AddOrgForm(request=self.request, data=request.POST, prefix=prefix, instance=instance)
        f_errors = dict()
        if f.is_valid():
            new_org = f.save()
            if new_org:
                f.put_log_data(msg=_(u'Данные сохранены'))
                if request.user.profile.is_ugh() and new_org.type == Org.PROFILE_LORU:
                    new_org.ugh_list.create(ugh=request.user.profile.org)
                return HttpResponse(json.dumps({'pk': new_org.pk, 'label': u'%s' % new_org}), content_type='application/json')
            else:
                # Случай, который не удалось воспроизвести: duplicate auto-slug field
                f_errors = dict(error=_(u"Есть такая организация"))
        else:
            f_errors = f.errors
        err_str = _(u'Ошибка:\n%s')
        errors = '\n'.join([u'%s' % v[0] for k,v in f_errors.items()])
        if "\n" in errors:
            err_str = _(u'Ошибки:\n%s')
        return HttpResponse(err_str % errors, content_type='text/plain')

add_org = AddOrgView.as_view()

class AddDocTypeView(SupervisorRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        f = AddDocTypeForm(data=request.POST, prefix='doctype')
        if f.is_valid():
            dt = f.save()
            return HttpResponse(json.dumps({'pk': dt.pk, 'label': u'%s' % dt}), content_type='application/json')
        else:
            err_str = _(u'Ошибка:\n%s')
            errors = '\n'.join([u'%s' % v[0] for k,v in f.errors.items()])
            if "\n" in errors:
                err_str = _(u'Ошибки:\n%s')
            return HttpResponse(err_str % errors, content_type='text/plain')

add_doctype = AddDocTypeView.as_view()

class AddGravesView(UGHRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            place = Place.objects.get(pk=pk, cemetery__ugh=request.user.profile.org)
        except Place.DoesNotExist:
            raise Http404
        f = AddGravesForm(data=request.POST, prefix='add_graves')
        if f.is_valid():
            graves_count = place.get_graves_count()
            graves_number = int(f.cleaned_data['place_grave_choice'])
            if graves_number < graves_count:
                for i in range(graves_count, graves_number, -1):
                    try:
                        Grave.objects.filter(place=place, grave_number=i).delete()
                        write_log(request, place, _(u"Удалена могила %s") % i)
                    except IntegrityError:
                        pass
            elif graves_number > graves_count:
                for i in range(graves_count+1, graves_number+1):
                    grave, created_ = Grave.objects.get_or_create(place=place, grave_number=i)
                    if created_:
                        write_log(request, place, _(u"Создана могила %s") % i)
            return HttpResponse(json.dumps({'place_grave_choice': graves_number}), content_type='application/json')
        else:
            err_str = _(u'Ошибка:\n%s')
            errors = '\n'.join([u'%s' % v[0] for k,v in f.errors.items()])
            if "\n" in errors:
                err_str = _(u'Ошибки:\n%s')
            return HttpResponse(err_str % errors, content_type='text/plain')

add_graves = AddGravesView.as_view()

class GetPlaceView(View):
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated:
            return redirect('/')
        return View.dispatch(self, request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.GET.get('place_number'):
            try:
                place = Place.objects.get(
                    cemetery__pk=request.GET.get('cemetery') or None,
                    area__pk=request.GET.get('area') or None,
                    row=request.GET.get('row') or '',
                    place=request.GET.get('place_number') or '',
                )
                burials = place.burial_set.filter(annulated=False)
                count_burials_all = burials.count()
                burials = burials.order_by('grave_number')[:20]
                count_burials_showed = burials.count()
            except Place.DoesNotExist:
                return HttpResponse('')
            except Place.MultipleObjectsReturned:
                return HttpResponse('')
            else:
                return render(
                    request,
                    'create_burial_place_info.html',
                    dict(
                        place=place,
                        burials=burials,
                        count_burials_all=count_burials_all,
                        count_burials_showed=count_burials_showed,
                ))
        else:
            return HttpResponse('')

get_place = GetPlaceView.as_view()

class GetGravesNumberView(View):
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated:
            return redirect('/')
        return View.dispatch(self, request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        data = dict(
            cemetery__pk=request.GET.get('cemetery') or None,
            area__pk=request.GET.get('area') or None,
            row=request.GET.get('row') or '',
            place=request.GET.get('place_number') or '',
        )
        desired_graves_count=request.GET.get('desired_graves_count') or '',

        if request.GET.get('place_number'):
            try:
                p = Place.objects.get(**data)
            except Place.DoesNotExist:
                pass
            except Place.MultipleObjectsReturned:
                return HttpResponse('')
            else:
                return HttpResponse('{"place_pk": %s, "graves_count": %s}' % (p.pk, p.get_graves_count()), content_type='application/json')

        return HttpResponse('{"graves_count": %s}' % desired_graves_count, content_type='application/json')

get_graves_number = GetGravesNumberView.as_view()

class CommentView(BurialsListGenericMixin, UghOrLoruRequiredMixin, DetailView):
    def get_queryset(self):
        return Burial.objects.filter(self.get_qs_filter()).distinct()

    def get(self, request, *args, **kwargs):
        return redirect('view_burial', self.get_object().pk)

    def post(self, request, *args, **kwargs):
        burial = self.get_object()
        comment = request.POST.get('comment').strip()
        if comment:
            write_log(request, burial, _(u'Комментарий: %s') % comment)
            BurialComment.objects.create(
                creator=request.user,
                burial=burial,
                comment=comment,
            )
        return redirect('view_burial', burial.pk)

burial_comment = CommentView.as_view()

class BurialEditComments(UGHRequiredMixin, View):
    template_name = 'burial_edit_comments.html'

    def get_formset(self):
        return BurialCommentEditFormSet(request=self.request, data=self.request.POST or None, instance=self.get_object())

    def get_object(self):
        return get_object_or_404(Burial, pk=self.kwargs['pk'], ugh=self.request.user.profile.org)

    def get_context_data(self, **kwargs):
        return {
            'burial': self.get_object(),
            'formset': self.get_formset(),
        }

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.request = request

        formset = self.get_formset()
        burial = self.get_object()
        if formset.is_valid():
            for f in formset.forms:
                f_data = f['comment'].data and f['comment'].data.strip() or ''
                if f.instance.pk:
                    str_dt_modified = localize(f.instance.dt_modified, use_l10n=settings.USE_L10N)
                    if f['DELETE'].value() or not f_data:
                        write_log(request, burial, _(u"Комментарий от %s удален") % str_dt_modified)
                        f.instance.delete()
                    elif 'comment' in f.changed_data:
                        if f.instance.owner() != request.user:
                            f.instance.modifier = request.user
                        write_log(
                            request,
                            burial,
                            _(u"Комментарий от %(dt_modified)s изменен:\n%(comment)s") % dict(
                                dt_modified=str_dt_modified,
                                comment=f_data,
                        ))
                        f.save()
                elif f_data:
                        write_log(request, burial, _(u"Комментарий: %s") % f_data)
                        BurialComment.objects.create(
                            burial=burial,
                            comment=f_data,
                            creator=request.user,
                            modifier=request.user,
                        )

            return redirect(reverse('burials_comments_edit', args=[self.kwargs['pk']]))
        else:
            messages.error(self.request, _(u"Обнаружены ошибки"))
            return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.request = request
        try:
            return render(request, self.template_name, self.get_context_data())
        except Burial.DoesNotExist:
            raise Http404

burials_comments_edit = BurialEditComments.as_view()

class AutocompleteCemeteries(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']
        cemeteries = Cemetery.objects.filter(name__icontains=query)
        if request.user.profile.is_loru():
            cemeteries = cemeteries.filter(ugh__loru_list__loru=request.user.profile.org)
        elif request.user.profile.is_ugh():
            cemeteries = cemeteries.filter(ugh=request.user.profile.org)
        else:
            cemeteries = Cemetery.objects.none()
        return HttpResponse(json.dumps([{'value': c.name} for c in cemeteries[:20]]), content_type='application/json')

autocomplete_cemeteries = AutocompleteCemeteries.as_view()

class AutocompleteAreas(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']
        cemetery = request.GET['cemetery']
        areas = Area.objects.filter(cemetery__name=cemetery, name__icontains=query)
        if request.user.profile.is_loru():
            areas = areas.filter(cemetery__ugh__loru_list__loru=request.user.profile.org)
        elif request.user.profile.is_ugh():
            areas = areas.filter(cemetery__ugh=request.user.profile.org)
        else:
            areas = Area.objects.none()
        return HttpResponse(json.dumps([{'value': c.name} for c in areas[:20]]), content_type='application/json')

autocomplete_areas = AutocompleteAreas.as_view()

class DeleteBurialfile(UghOrLoruRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        burial_file = get_object_or_404(BurialFiles, pk=self.kwargs['pk'])
        if not burial_file.burial.is_editable(request.user):
            raise Http404
        burial_file.delete()
        return redirect('edit_burial', burial_file.burial.pk)

delete_burialfile = DeleteBurialfile.as_view()

class BurialfileCommentEdit(UghOrLoruRequiredMixin, UpdateView):
    template_name = 'edit_burialfile_comment.html'
    form_class = BurialfileCommentEditForm

    def get_object(self):
        obj =  get_object_or_404(BurialFiles, pk=self.kwargs['pk'])
        if not obj.burial.is_editable(self.request.user):
            raise Http404
        return obj

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form(self.get_form_class())
        if form.is_valid():
            form.save()
            return redirect('edit_burial', self.get_object().burial.pk)
        context = self.get_context_data(object=self.object, form=form)
        return self.render_to_response(context)

edit_burialfile_comment = BurialfileCommentEdit.as_view()

class PlaceCertificateView(UGHRequiredMixin, DetailView):
    template_name = 'place_certificate.html'

    def get_object(self):
        place =  get_object_or_404(
            Place,
            pk=self.kwargs['pk'],
            cemetery__ugh=self.request.user.profile.org
        )
        return place

    def get_context_data(self, **kwargs):
        
        def make_table(left, right):
            table = []
            for i in range(max(len(left), len(right))):
                item = dict(left='', right='')
                try:
                    item['left'] = left[i]
                except IndexError:
                    pass
                try:
                    item['right'] = right[i]
                except IndexError:
                    pass
                table.append(item)
            return table
            
        data = super(PlaceCertificateView, self).get_context_data(**kwargs)
        place = self.object
        if place.is_columbarium():
            title1 = _(u'ПАСПОРТ МЕСТА В КОЛУМБАРИИ')
            title2 = _(u'ОТВЕТСТВЕННЫЙ ЗА МЕСТО В КОЛУМБАРИИ')
            title3 = _(u'АДРЕС МЕСТА В КОЛУМБАРИИ')
        else:
            title1 = _(u'ПАСПОРТ МЕСТА')
            title2 = _(u'ОТВЕТСТВЕННЫЙ ЗА МЕСТО')
            title3 = _(u'АДРЕС МЕСТА')
            
        ugh = place.cemetery.ugh
        left = [ ugh, ]
        if ugh.off_address:
            left.append(u"%s: %s" % (_(u'Адрес'), ugh.off_address, ))
        if ugh.phones:
            left.append(u"%s: %s" % (
                _(u'Телефоны') if re.search(r'\s+', ugh.phones) else _(u'Телефон'),
                ", ".join(ugh.phones.split()),
            ))
        if ugh.worktime:
            left.append(u"%s: %s" % (_(u'Время работы'), ugh.worktime, ))

        right = []
        for burial in place.burials_available():
            if burial.deadman.birth_date or burial.deadman.death_date:
                lived = u"%s — %s" % (
                    burial.deadman.birth_date or u"...",
                    burial.deadman.death_date or u"...",
                )
            else:
                lived = _(u"годы жизни неизвестны")
            if burial.fact_date:
                fact_date = _(u"похоронен %s") % burial.fact_date
            else:
                fact_date = _(u"дата похорон неизвестна")
            right.append(_(u"№: %(pk)s, %(deadman)s, %(lived)s, %(fact_date)s") % dict(
                            pk=burial.pk,
                            deadman=burial.deadman,
                            lived=lived,
                            fact_date=fact_date
            ))
        if not right:
            right.append(_(u"Нет захоронений"))
        table1 = make_table(left, right)

        left = []
        if place.responsible:
            left.append(place.responsible.last_name)
            if place.responsible.first_name:
                left.append(place.responsible.first_name)
            if place.responsible.middle_name:
                left.append(place.responsible.middle_name)
            if place.responsible.user:
                left.append(_(u"Вход на сайт %s, логин: %s") % (
                    get_front_end_url(self.request),
                    place.responsible.user.username,
                ))
        else:
            left.append(_(u"не указан"))
        right=[u"%s: %s" % (_(u'Кладбище'), place.cemetery, ), ]
        if place.cemetery.address:
            right.append(u"%s: %s" % (_(u'Адрес'), place.cemetery.address, ))
        urm = u"%s: %s" % (_(u'Участок'), place.area and place.area.name or _(u"не указан"), )
        if place.row:
            urm = u"%s, %s: %s" % (urm, _(u"ряд"), place.row, )
        if place.place:
            urm = u"%s, %s: %s" % (urm, _(u"место в колумбарии") if place.is_columbarium() else _(u"место"), place.place, )
        right.append(urm)

        yandex_api_key = None
        if place.cemetery.address and \
           place.cemetery.address.gps_x is not None and place.cemetery.address.gps_y is not None:
            right.append(_(u"Координаты GPS/ГЛОНАСС: ш. %(lat)s, д. %(lng)s") % dict(
                lat=place.cemetery.address.gps_y,
                lng=place.cemetery.address.gps_x,
            ))
            host = self.request.get_host()
            for key in settings.YANDEX_API_KEYS:
                if re.search(key['re_host'], host, flags=re.I):
                    yandex_api_key = key['api_key']

        table2 = make_table(left, right)
        try:
            place_photo = PlacePhoto.objects.filter(place=place).order_by('-date_of_creation')[0].bfile
        except IndexError:
            place_photo = None
        data.update(dict(
            title1=title1,
            title2=title2,
            title3=title3,
            table1=table1,
            table2=table2,
            yandex_api_key=yandex_api_key,
            place=place,
            place_photo=place_photo,
            request=self.request,
        ))
        return data

place_certificate = PlaceCertificateView.as_view()

class ApiOmsPhotoPlaces(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request):
        place = None
        cemeteries = Cemetery.editable_ugh_cemeteries(user=request.user)
        # Показать место, с которым работал ранее
        with transaction.atomic():
            try:
                place = Place.objects.select_for_update().filter(
                            cemetery__ugh=request.user.profile.org,
                            is_invent=True,
                            dt_wrong_fio__isnull=True,
                            dt_unindentified__isnull=True,
                            dt_free__isnull=True,
                            user_processed=request.user,
                            is_inprocess=True,
                            dt_processed__isnull=True,
                            placephoto__isnull=False,
                    ).order_by('pk')[0]
                if place.cemetery not in cemeteries:
                    return Response(status=400, data=dict(
                        message=_(u"Вы не закончили обрабатывать место на кладбище, "
                                  u"доступ к которому после этого был Вам отменен. "
                                  u"Обратитесь к администратору, чтобы возобновил Вам доступ "
                                  u"к кладбищу %s") % place.cemetery.name
                ))
            except IndexError:
                message = None
                if not request.user.profile.is_registrator_or_caretaker():
                    message = _(u"У вас нет прав вносить захоронения. Обратитесь к администратору")
                elif not request.user.profile.cemeteries.count():
                    message = _(u"Вам не назначены кладбища для ввода захоронений. Обратитесь к администратору")
                if message:
                    return Response(status=400, data=dict(message=message))

                # Если такого места не было, ищем первое среди необработанных
                try:
                    place = Place.objects.select_for_update().filter(
                                cemetery__in=cemeteries,
                                is_invent=True,
                                is_inprocess=False,
                                dt_wrong_fio__isnull=True,
                                dt_unindentified__isnull=True,
                                dt_free__isnull=True,
                                dt_processed__isnull=True,
                                placephoto__isnull=False,
                        ).order_by('pk')[0]
                    place.user_processed = request.user
                    place.is_inprocess = True
                    place.save()
                except IndexError:
                    pass
        if place:
            serializer = PlaceLockSerializer(place, context=dict(request=request))
            data=serializer.data
            data['place'] = PlaceTitleSerializer(place).data
        else:
            data = {}
        return Response(status=200, data=data)

api_oms_photo_places = ApiOmsPhotoPlaces.as_view()

class ApiPlacePhotoUpload(EditCemeteryObjectsMixin, APIView):
    permission_classes = (PermitIfUgh,)
    parser_classes = (MultiPartParser, JSONParser,)

    def post(self, request, pk):
        place = get_object_or_404(Place, pk=pk)
        if place.cemetery not in Cemetery.editable_ugh_cemeteries(request.user):
            raise PermissionDenied
        # -------------------
        # Если размер картинки size_х * size_y > minsize, то
        #   cохраняем файл в тех же размерах (size_y, size_y),
        #   с правкой ориентации, если необходимо
        #   с качеством quality,
        #   тем самым уменьшая размер файла по сравнению с поданным
        # иначе возвращаем оригинал.
        # В любом случае результатом будет ContentFile
        #
        photo_content = ThumbnailContentFile(
            request.data['file'],
            quality=30,
            minsize=1600*1200,
        ).generate()
        if photo_content:
            data = dict()
            status = 200
            photo = PlacePhoto(place=place)
            photo.save()
            photo.bfile.save(request.data['file'].name, photo_content)
            msg = request.build_absolute_uri(photo.bfile.url)
            write_log(
                request,
                place,
                operation=LogOperation.PHOTO_TO_PLACE_MOBILE,
                msg=msg,
            )
        else:
            data = self.make_error_data(_(u"Загружаемый файл не является изображением"))
            status = 400
        return Response(status=status, data=data)

api_place_photo_upload = ApiPlacePhotoUpload.as_view()

class ApiOmsPhotoPlacesDetail(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request, pk):
        place, status, message = Place.check_invent_place(request, pk)
        if message:
            return Response(data=dict(status='error', message=message), status=status)
        data = PlaceLockSerializer(place, context=dict(request=request)).data
        data['place'] = PlaceTitleSerializer(place).data
        return Response(status=200, data=data)

api_oms_photo_places_detail = ApiOmsPhotoPlacesDetail.as_view()

class ApiOmsPhotoPlacesChange(ApiOmsPhotoPlacesDetail):
    permission_classes = (PermitIfUgh,)

    def put(self, request, pk):
        place, status, message = Place.check_invent_place(request, pk)
        if message:
            return Response(data=dict(status='error', message=message), status=status)

        do_save = False
        log_messages = []
        log_operations = []

        if 'remakePhoto' in request.data:
            do_save = True
            remakePhoto = request.data.get('remakePhoto')
            if remakePhoto:
                place.dt_wrong_fio = datetime.datetime.now()
                place.user_processed = None
                place.is_inprocess = False
                log_operations.append(LogOperation.PLACE_PHOTO_REJECT)
                remake_photo_comment = request.data.get('remakePhotoComment')
                if remake_photo_comment:
                    log_messages.append(_(u'Комментарий к повторному фото места: %s') % remake_photo_comment)
            else:
                place.dt_wrong_fio = None
                log_messages.append(_(u'Отменен признак повторного фото места'))

        if 'processed' in request.data:
            do_save = True
            processed = request.data.get('processed')
            if processed:
                place.dt_processed = datetime.datetime.now()
                log_operations.append(LogOperation.PLACE_PHOTO_PROCESSED)
            else:
                place.dt_processed = None
                place.user_processed = None
                place.is_inprocess = False
                log_messages.append(_(u'Фотографии места могут быть обработаны повторно'))

        with transaction.atomic():
            if do_save:
                place.save()
            for o in log_operations:
                write_log(request, place, operation=o)
            for m in log_messages:
                write_log(request, place, m)
        return Response(status=status, data={})

api_oms_photo_places_change = ApiOmsPhotoPlacesChange.as_view()

class ApiOmsPhotoPlacesCounts(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request):
        return Response(
            status=200,
            data=dict(
                unprocessed=Place.unprocessed_count(user=request.user)
        ))

api_oms_photo_places_counts = ApiOmsPhotoPlacesCounts.as_view()

class ApiOmsCemeteriesView(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request):
        """
        Получить список кладбищ, доступных для правки пользователю, или все кладбища
        организации

        Если есть get параметр all (...?all=1), то отдать все кладбища
        """
        if request.GET.get('all'):
            cemeteries = Cemetery.objects.filter(ugh=request.user.profile.org)
        else:
            cemeteries = Cemetery.editable_ugh_cemeteries(user=request.user)
        return Response(
            status=200,
            data=[CemeteryTitleSerializer(cemetery).data for cemetery in cemeteries]
        )

api_oms_cemeteries = ApiOmsCemeteriesView.as_view()

class ApiOmsAreaMsAccessSync(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request, pk):
        area = get_object_or_404(
            Area,
            cemetery__ugh=request.user.profile.org,
            pk=pk
        )
        try:
            dt_modified = int(request.GET.get('dt_modified') or 0)
        except ValueError:
            dt_modified = 0
        q = Q(annulated=False, status=Burial.STATUS_CLOSED, area=area)
        data = []
        if dt_modified > 0:
            dt_modified = datetime.datetime.fromtimestamp(dt_modified)
            q &= Q(dt_modified__gte=dt_modified)
            # Get deleted and annulated to data
        for b in Burial.objects.filter(q).select_related(
                'cemetery', 'area', 'deadman', 'applicant', 'applicant__address',
            ).order_by('dt_modified').iterator():

            burial_comments = u""
            for comment in BurialComment.objects.filter(burial=b).order_by('dt_created'):
                burial_comments += comment.dt_created.strftime("%Y-%m-%d") + "\r\n"
                burial_comments += comment.comment + "\r\n"

            applicant = b.applicant and b.applicant.full_human_name() or ''
            applicant_phones = b.applicant and b.applicant.phones or ''
            if applicant or applicant_phones:
                applicant = u"%s\r\n%s" % (applicant, applicant_phones,)

            burial_type = b.get_burial_type_display() or ''
            burial_container = b.get_burial_container_display() or ''
            if burial_type or burial_container:
                burial_type = u"%s\r\n%s" % (burial_type, burial_container)

            data.append(dict(
                cemetery=b.cemetery.name,
                area=b.area.name,
                row=b.row,
                place=b.place_number,
                grave_number=int(b.grave_number),
                deadman=b.deadman and b.deadman.full_human_name() or '',
                fact_date=b.fact_date and b.fact_date.str_safe() or '',
                deadman_dob=b.deadman and b.deadman.birth_date and b.deadman.birth_date.str_safe() or '',
                deadman_dod=b.deadman and b.deadman.death_date and b.deadman.death_date.str_safe() or '',
                burial_comments=burial_comments,
                burial_type=burial_type,
                applicant=applicant,
                applicant_address=b.applicant and b.applicant.address and b.applicant.address.short() or '',
                deadman_address=b.deadman and b.deadman.address and b.deadman.address.short() or '',
                burial_id=int(b.pk),
                dt_modified=int(b.dt_modified.strftime("%s")),
                cemetery_id=int(b.cemetery.pk),
                area_id=int(b.area.pk),
                place_id=int(b.place.pk),
            ))
        return Response(status=200, data=data)

api_oms_area_msaccess_sync = ApiOmsAreaMsAccessSync.as_view()

class ApiOmsCemeteriesDeletedBurials(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request, pk):
        data = list()
        cemetery = get_object_or_404(
            Cemetery,
            ugh=request.user.profile.org,
            pk=pk
        )
        try:
            dt_modified = int(request.GET.get('dt_modified') or 0)
        except ValueError:
            dt_modified = 0
        if dt_modified > 0:
            dt_modified = datetime.datetime.fromtimestamp(dt_modified)
            data += DeleteLog.get_deleted(dt_modified, Burial, [cemetery.pk])
            q1 = Q(
                annulated=True,
                status=Burial.STATUS_CLOSED,
                cemetery=cemetery,
                dt_modified__gte=dt_modified
            )
            q2 = Q(
                annulated=False,
                status=Burial.STATUS_EXHUMATED,
                cemetery=cemetery,
                dt_modified__gte=dt_modified
            )
            for q in [q1, q2]:
                for b in Burial.objects.filter(q):
                    data.append({
                        'pk': int(b.pk),
                        '_deleted': True,

                    })
        return Response(status=200, data=data)

api_oms_cemeteries_deleted_burials = ApiOmsCemeteriesDeletedBurials.as_view()

class ApiOmsCemeteriesAreasView(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request, pk):
        cemetery = get_object_or_404(
            Cemetery,
            pk=pk,
            ugh=request.user.profile.org
        )
        q = Q(cemetery=cemetery)
        try:
            dt_modified = int(request.GET.get('dt_modified') or 0)
        except ValueError:
            dt_modified = 0
        if dt_modified > 0:
            dt_modified = datetime.datetime.fromtimestamp(dt_modified)
            q &= Q(dt_modified__gte=dt_modified)
        return Response(
            status=200,
            data=[ AreaTitleSerializer(area).data \
                   for area in Area.objects.filter(q)
            ]
        )

api_oms_cemeteries_areas = ApiOmsCemeteriesAreasView.as_view()

class ApiOmsPlacesBounds(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request):
        ugh = request.user.profile.org
        data = Place.objects.filter(
            cemetery__ugh=ugh,
            lat__isnull=False,
            lng__isnull=False,
        ).aggregate(
            s=Min('lat'),
            n=Max('lat'),
            w=Min('lng'),
            e=Max('lng'),
        )
        return Response(data=data)

api_oms_places_bounds = ApiOmsPlacesBounds.as_view()

class ApiOmsPlacesClusters(APIView):
    renderer_classes = (JSONPRenderer, )

    def get(self, request, ugh_id):
        '''
        Вывод отдельных мест и кластеров мест для yandex maps remoteManager api

        callback_get_parm({
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": 0,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [55.831903, 37.411961]
                    },
                    "properties": {
                        "balloonContent": "Содержимое балуна",
                        "clusterCaption": "Метка 1",
                        "hintContent": "Текст подсказки"
                    }
                },
                {
                    // Описание кластера.
                    type: 'Cluster',
                    // Идентификатор кластера формируется самостоятельно.
                    id: 1,
                    bbox: [[35, 46], [46, 57]],
                    number: 34,
                    // Массив, описывающий 34 объекта в составе кластера.
                    // Необязательное поле.
                    features: [...],            
                    geometry: {                         
                        type: 'Point',                         
                        coordinates: [40.5, 51]                     
                    },                     
                    properties: {
                        // Если поле iconContent не задано, то 
                        // в иконке кластера будет отображаться значение, указанное в поле number.                 
                        iconContent: 'Кластер 1'                     
                    }
                },
                {
                    "type": "Feature",
                    "id": 2,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [55.763338, 37.565466]
                    },
                    "properties": {
                        "balloonContent": "Содержимое балуна",
                        "clusterCaption": "Метка 2",
                        "hintContent": "Текст подсказки"
                    }
                }
            ]
        })
        '''

        status_code = 200
        data = { "type": "FeatureCollection", "features": [] }
        try:
            bounds = request.GET.get('bbox', '').strip()
            m = re.search(
                r'^'
                r'([+-]?\d+(?:\.?\d*))\s*\,\s*'
                r'([+-]?\d+(?:\.?\d*))\s*\,\s*'
                r'([+-]?\d+(?:\.?\d*))\s*\,\s*'
                r'([+-]?\d+(?:\.?\d*))'
                r'$',
                bounds,
            )
            if not m:
                raise ServiceException(u"Invalid or absent 'bounds' GET parm")
            w_ = m.group(1)
            s_ = m.group(2)
            e_ = m.group(3)
            n_ = m.group(4)
            
            w_f = float(w_)
            s_f = float(s_)
            e_f = float(e_)
            n_f = float(n_)

            # bbox get параметр задает границы области, которая на yandex карте
            # рисуется квадратом (тайлом) 256x256 пикселей. Там помещается
            # по диаганали балунов и кружков кластера:
            #
            MARKS_PER_TILE = 20
            #
            # Находим погрешность для geohash (geohash_error).
            # Это длина диаганали тайла, уменьшенная в MARKS_PER_TILE раз.
            # Из этой погрешности ищем длину префикса geohash,
            # при которой прямоугольник внутри geohash'a с таким префиксом
            # чуть превышает погрешность для geohash.
            # Начинаем поиск с длины geohash prefix, при которой погрешность
            # меньше метра:
            #
            GEOHASH_PREFIX_LEN_START = 10

            tile_diag_len = LatLon(Latitude(s_f), Longitude(w_f)).\
                                distance(LatLon(Latitude(n_f), Longitude(e_f)))
            geohash_error = tile_diag_len / float(MARKS_PER_TILE)
            
            # точка в центре тайла:
            #
            tile_center = dict(
                lat=s_f + (n_f-s_f) / 2.,
                lng=w_f + (e_f-w_f) / 2.,
            )
            geohash_prefix_len = GEOHASH_PREFIX_LEN_START
            tile_center_geohash_start = geohash.encode(
                latitude=tile_center['lat'],
                longitude=tile_center['lng'],
                precision=geohash_prefix_len,
            )
            diff_prev = 40000.
            while geohash_prefix_len > 0:
                tile_center_geohash = tile_center_geohash_start[:geohash_prefix_len]
                center_box = geohash.bbox(tile_center_geohash)
                center_diag_len = LatLon(Latitude(center_box['s']), Longitude(center_box['w'])).\
                                distance(LatLon(Latitude(center_box['n']), Longitude(center_box['e'])))
                diff = center_diag_len - geohash_error
                if diff >= 0.:
                    # Если при чуть большей длине префикса разница
                    # была меньшей, то выбираем чуть больший префикс
                    if diff_prev < diff:
                        geohash_prefix_len += 1
                    break
                diff_prev = abs(diff)
                geohash_prefix_len -= 1

            req_str = '''
                SELECT
                    AVG(lat)                AS avg_lat,
                    AVG(lng)                AS avg_lng,
                    MIN(lat)                AS min_lat,
                    MIN(lng)                AS min_lng,
                    MAX(lat)                AS max_lat,
                    MAX(lng)                AS max_lng,
                    COUNT(dt_free)          AS cnt_dt_free,
                    COUNT(dt_wrong_fio)     AS cnt_dt_wrong_fio,
                    COUNT(dt_military)      AS cnt_dt_military,
                    COUNT(dt_size_violated) AS cnt_dt_size_violated,
                    COUNT(dt_unowned)       AS cnt_dt_unowned,
                    COUNT(dt_unindentified) AS cnt_dt_unindentified,
                    SUBSTRING(geohash FROM 1 FOR %(geohash_prefix_len)s) AS geohash_prefix,
                    COUNT(*) AS quantity
                FROM
                    burials_place
                INNER JOIN 
                    burials_cemetery ON (burials_place.cemetery_id = burials_cemetery.id)
                WHERE
                    burials_cemetery.ugh_id = %(ugh_id)s AND
                    lat IS NOT NULL AND
                    lng IS NOT NULL AND
                    lat BETWEEN %(s_)s AND %(n_)s AND 
                    lng BETWEEN %(w_)s AND %(e_)s
                GROUP BY
                    geohash_prefix;
            ''' % dict(
                geohash_prefix_len=geohash_prefix_len,
                ugh_id=ugh_id,
                n_=n_,
                s_=s_,
                e_=e_,
                w_=w_,
            )
            cursor = connection.cursor()
            cursor.execute(req_str)

            columns = [col[0] for col in cursor.description]
            stata = Place.status_dict()
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                res = dict()
                res['id'] = str(uuid.uuid1())
                if row_dict['quantity'] == 1:
                    res['type'] = 'Feature'
                    res['geometry'] = dict(
                        type='Point',
                        coordinates=[row_dict['avg_lng'], row_dict['avg_lat'],],
                    )
                    res['properties'] = dict(
                        balloonContent=u"",
                        clusterCaption=_(u"Место"),
                        hintContent=u""
                    )
                    for status in stata:
                        if row_dict["cnt_%s" % status]:
                            res['properties']['hintContent'] += u"%s, " % stata[status]
                    if res['properties']['hintContent']:
                        res['properties']['hintContent'] = _(u"Признак(и) места: %s") % \
                            res['properties']['hintContent'][:-2]
                else:
                    res['type'] = 'Cluster'
                    res['bbox'] = [
                        [row_dict['min_lng'], row_dict['min_lat']],
                        [row_dict['max_lng'], row_dict['max_lat']]
                    ]
                    res['number'] = row_dict['quantity']

                    # Массив, описывающий <number> объекта в составе кластера.
                    #  Необязательное поле.
                    # res['features'] = [],

                    res['geometry'] = {
                        'type': 'Point',
                        'coordinates': [row_dict['avg_lng'], row_dict['avg_lat'],],
                    }
                    res['properties'] = dict(
                        iconContent=str(row_dict['quantity'])
                    )

                data['features'].append(res)

        except ServiceException as excpt:
            data.update(dict(message=excpt.message))
            status_code = 400
        return Response(data, status=status_code)

api_oms_places_clusters = ApiOmsPlacesClusters.as_view()

class TradeCemeteriesMixin(object):

    def available_cemeteries(self, user):
        if is_loru_user(user):
            qs = Q(ugh__loru_list__loru=user.profile.org)
        elif is_ugh_user(user):
            qs = Q(ugh=user.profile.org)
        else:
            return []
        return Cemetery.objects.filter(qs)

class ApiLoruCemeteriesView(TradeCemeteriesMixin, APIView):
    permission_classes = (PermitIfTrade,)

    def get(self, request):
        cemeteries = self.available_cemeteries(request.user)
        return Response(
            status=200,
            data=[ CemeteryTitleSerializer(cemetery).data \
                   for cemetery in cemeteries
            ]
        )

api_loru_cemeteries = ApiLoruCemeteriesView.as_view()

class ApiLoruCemeteriesAreasView(TradeCemeteriesMixin, APIView):
    permission_classes = (PermitIfTrade,)

    def get(self, request, pk):
        cemetery = get_object_or_404(Cemetery, pk=pk)
        cemeteries = self.available_cemeteries(request.user)
        if cemetery not in cemeteries:
            raise Http404
        return Response(
            status=200,
            data=[ AreaTitleSerializer(area).data \
                   for area in Area.objects.filter(cemetery=cemetery)
            ]
        )

api_loru_cemeteries_areas = ApiLoruCemeteriesAreasView.as_view()

class ApiOmsAreasPlacesView(APIView):
    permission_classes = (PermitIfUgh,)

    def get(self, request, cemetery_pk, area_pk):
        area = get_object_or_404(
            Area,
            cemetery__pk=cemetery_pk,
            pk=area_pk,
            cemetery__ugh=request.user.profile.org
        )
        q = Q(area=area)
        try:
            dt_modified = int(request.GET.get('dt_modified') or 0)
        except ValueError:
            dt_modified = 0
        if dt_modified > 0:
            dt_modified = datetime.datetime.fromtimestamp(dt_modified)
            q &= Q(dt_modified__gte=dt_modified)
        return Response(
            status=200,
            data=[ PlaceTitleSerializer(place).data \
                   for place in Place.objects.filter(q)
            ])

api_oms_areas_places = ApiOmsAreasPlacesView.as_view()

class ApiClientSiteCemeteriesView(ApiClientSiteMixin, APIView):

    def get(self, request, token):
        ugh = self.get_org(token)
        return Response(
            status=200,
            data=CemeteryClientSiteSerializer(
                    Cemetery.objects.filter(ugh=ugh),
                    context=dict(request=request),
                    many=True,
                ).data
        )

api_client_site_cemeteries = ApiClientSiteCemeteriesView.as_view()

class ApiClientSitePlacesView(ApiClientSiteMixin, APIView):

    def get(self, request, token):
        ugh = self.get_org(token)
        query = request.GET.get('query', '').strip()
        places = Place.objects.none()
        if query:
            try:
                offset = request.GET.get('offset') and int(request.GET.get('offset'))
                limit = request.GET.get('limit') and int(request.GET.get('limit'))
            except ValueError:
                pass
            else:
                q = Q(cemetery__ugh=ugh, burial__annulated=False)
                fio = [re_search(f) for f in query.split()]
                if len(fio) > 2:
                    q &= Q(burial__deadman__middle_name__iregex=fio[2])
                if len(fio) > 1:
                    q &= Q(burial__deadman__first_name__iregex=fio[1])
                q &= Q(burial__deadman__last_name__iregex=fio[0])
                places = Place.objects.filter(q).distinct()
                if offset and limit:
                    places = places[offset:offset+limit]
                elif offset:
                    places = places[offset:]
                elif limit:
                    places = places[:limit]
        return Response(
            status=200,
            data=ApiClientSitePlacesSerializer(
                places,
                context=dict(request=request), many=True).data
            )

api_client_site_places = ApiClientSitePlacesView.as_view()

class ApiClientSitePlacesIdView(ApiClientSiteMixin, APIView):

    def get(self, request, token, pk):
        ugh = self.get_org(token)
        place = get_object_or_404(
            Place,
            pk=pk,
            cemetery__ugh=ugh
        )
        return Response(
            status=200,
            data=ApiClientSitePlacesSerializer(
                place,
                context=dict(request=request)).data
            )

api_client_site_places_id = ApiClientSitePlacesIdView.as_view()

class ApiClientSitePlacePhotosView(ApiClientSiteMixin, APIView):

    def get(self, request, ugh_token, place_pk):
        ugh = self.get_org(ugh_token)
        try:
            place = Place.objects.filter(
                cemetery__ugh=ugh,
                pk=place_pk
            )[0]
        except IndexError:
            raise Http404
        return Response(status=200, data=place.get_photo_gallery(request))

api_client_site_placephotos = ApiClientSitePlacePhotosView.as_view()

class BurialDoublesView(UGHRequiredMixin, TemplateView):
    template_name = 'burial_doubles.html'

    def date_str(self, d, what):
        date = '%s_date' % what
        result = ''
        if d[date]:
            date_no_day = '%s_date_no_day' % what
            date_no_month = '%s_date_no_month' % what
            result = UnclearDate(
                year=d[date].year,
                month=None if d[date_no_month] else d[date].month,
                day=None if d[date_no_day] else d[date].day,
            ).str_safe(format='d.m.y')
        else:
            result = ''
        return result

    def get_context_data(self, **kwargs):
        data = super(BurialDoublesView, self).get_context_data(**kwargs)
        ugh_pk = self.request.user.profile.org.pk
        cemetery_pk_in=[c.pk for c in Cemetery.editable_ugh_cemeteries(self.request.user)]
        if not cemetery_pk_in:
            raise Http404
        req_str = '''
        SELECT
            "persons_baseperson"."last_name" as last_name,
            "persons_baseperson"."first_name" as first_name,
            "persons_baseperson"."middle_name" as middle_name,

            "persons_baseperson"."birth_date_no_month" as birth_date_no_month,
            "persons_baseperson"."birth_date_no_day" as birth_date_no_day,
            "persons_baseperson"."birth_date" as birth_date,

            "persons_deadperson"."death_date_no_month" as death_date_no_month,
            "persons_deadperson"."death_date_no_day" as death_date_no_day,
            "persons_deadperson"."death_date" as death_date,

            "burials_burial"."fact_date_no_month" as fact_date_no_month,
            "burials_burial"."fact_date_no_day" as fact_date_no_day,
            "burials_burial"."fact_date" as fact_date,

            "burials_cemetery"."name" as cemetery_name,
            "burials_cemetery"."id" as cemetery_pk

            FROM "persons_deadperson"

            INNER JOIN "burials_burial" ON ("persons_deadperson"."baseperson_ptr_id" = "burials_burial"."deadman_id")
            INNER JOIN "burials_cemetery" ON ("burials_burial"."cemetery_id" = "burials_cemetery"."id")
            INNER JOIN "persons_baseperson" ON ("persons_deadperson"."baseperson_ptr_id" = "persons_baseperson"."id")

            WHERE
                last_name > '' AND
                "burials_burial"."annulated" = False AND
                "burials_burial"."status" = 'closed' AND
                "burials_cemetery"."id" IN (%(cemetery_pk_in_str)s) AND
                "burials_cemetery"."ugh_id" = %(ugh_pk)s

            GROUP BY
                last_name,
                first_name,
                middle_name,
                birth_date_no_month,
                birth_date_no_day, birth_date,
                death_date_no_month,
                death_date_no_day,
                death_date,
                fact_date_no_month,
                fact_date_no_day,
                fact_date,
                "burials_cemetery"."id"

            HAVING Count(*) > 1

            ORDER BY
                last_name,
                first_name,
                middle_name
            ;
        ''' % dict(
                cemetery_pk_in_str=", ".join([str(pk) for pk in cemetery_pk_in]),
                ugh_pk=ugh_pk,
            )

        with connection.cursor() as cursor:
            cursor.execute(req_str)
            doubles = dictfetchall(cursor)
        for d in doubles:
            d['search_str'] = "&".join([
                "%s=%s" % (key, d[key],) for key in d if key not in ('cemetery_name', )
            ])
            d['fio'] = d['last_name']
            if d['first_name']:
                d['fio'] += u" %s" % d['first_name']
                if d['middle_name']:
                    d['fio'] += u" %s" % d['middle_name']
            d['birthdate'] = self.date_str(d, 'birth')
            d['deathdate'] = self.date_str(d, 'death')
            d['factdate'] = self.date_str(d, 'fact')

        data.update(dict(doubles=doubles))
        return data

burials_doubles = BurialDoublesView.as_view()

class BurialDoubleView(UGHRequiredMixin, TemplateView):
    template_name = 'burial_double_table.html'

    def unclear_date(self, what):
        req = self.request.GET
        date = '%s_date' % what
        date_no_day = '%s_date_no_day' % what
        date_no_month = '%s_date_no_month' % what
        bool_dict = { 'True': True, 'False': False }
        if req[date] != 'None':
            clear_date = datetime.datetime.strptime(req[date], '%Y-%m-%d')
            result = UnclearDate(
                year=clear_date.year,
                month=None if bool_dict[req[date_no_month]] else clear_date.month,
                day=None if bool_dict[req[date_no_day]] else clear_date.day,
            )
        else:
            result = None
        return result

    def get_context_data(self, **kwargs):
        data = super(BurialDoubleView, self).get_context_data(**kwargs)
        burials=[]
        get_parms = []
        req = self.request.GET
        try:
            birth_date = self.unclear_date('birth')
            death_date = self.unclear_date('death')
            fact_date = self.unclear_date('fact')
            cemetery_pk = req['cemetery_pk']
            if cemetery_pk not in \
                [str(c.pk) for c in Cemetery.editable_ugh_cemeteries(self.request.user)]:
                raise Http404
            qs = Q(
                status=Burial.STATUS_CLOSED,
                deadman__last_name=req['last_name'],
                deadman__first_name=req['first_name'],
                deadman__middle_name=req['middle_name'],
                cemetery__pk=cemetery_pk,
            )
            if birth_date is None:
                qs &= Q(deadman__birth_date__isnull=True)
            else:
                qs &= Q(
                    deadman__birth_date__gte=birth_date.d,
                    deadman__birth_date__lt=birth_date.d + datetime.timedelta(days=1),
                    deadman__birth_date_no_month=birth_date.no_month,
                    deadman__birth_date_no_day=birth_date.no_day,
                )
            if death_date is None:
                qs &= Q(deadman__death_date__isnull=True)
            else:
                qs &= Q(
                    deadman__death_date__gte=death_date.d,
                    deadman__death_date__lt=death_date.d + datetime.timedelta(days=1),
                    deadman__death_date_no_month=death_date.no_month,
                    deadman__death_date_no_day=death_date.no_day,
                )
            if fact_date is None:
                qs &= Q(fact_date__isnull=True)
            else:
                qs &= Q(
                    fact_date__gte=fact_date.d,
                    fact_date__lt=fact_date.d + datetime.timedelta(days=1),
                    fact_date_no_month=fact_date.no_month,
                    fact_date_no_day=fact_date.no_day,
                )

            burials = Burial.objects.filter(qs).order_by('-pk')
        except (ValueError, KeyError, TypeError, ):
            raise Http404

        message = ''
        burials_count = 0
        n_responsibles = 0
        put_controls = False
        for b in burials:
            if not b.annulated:
                burials_count += 1
                if b.place and b.place.responsible:
                    n_responsibles += 1
        one_responsible = n_responsibles == 1
        if burials_count < 1:
            message = _(u"Не найдены одни и те же захороненные по заданным параметрам поиска")
        elif burials_count == 1:
            message = _(u"Найдено только одно не-аннулированное захоронение.")
        else:
            put_controls = True

        data.update(dict(
            burials=burials,
            burials_count=burials_count,
            one_responsible=one_responsible,
            message=message,
            put_controls=put_controls,
        ))
        return data

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        b_dest = b_dest_pk = None
        r_dest = request.POST.get('destination_')
        if r_dest:
            m = re.search(r'^destination_(\d+)$', r_dest)
            if m:
                try:
                    b_dest_pk = m.group(1)
                    b_dest = Burial.objects.get(pk=b_dest_pk)
                    if b_dest.ugh != request.user.profile.org:
                        raise Http404
                except Burial.DoesNotExist:
                    raise Http404
        if b_dest:
            # Надо проверить не подсунули ли чего.
            # Или пока выбирали, то что-то изменилось
            context = self.get_context_data()
            if context['burials_count'] < 2:
                return redirect(request.get_full_path())
            # Для дальнейшей проверки, чтоб тоже чего не подсунули,
            # собираем pks этих дублей
            b_pks = dict()
            for b in context['burials']:
                if not b.place:
                    raise Http404
                s_b_pk = str(b.pk)
                if s_b_pk not in b_pks:
                    b_pks[s_b_pk] = dict(b=b, p=b.place, r=b.place.responsible)
            if b_dest_pk not in b_pks:
                raise Http404
            p_dest = b_dest.place

            r_place = request.POST.get('source_place_')
            p_source = None
            b_source = None
            if r_place:
                m = re.search(r'^source_place_(\d+)$', r_place)
                if m:
                    s_b_pk = m.group(1)
                    if s_b_pk not in b_pks:
                        raise Http404
                    p_source = b_pks[s_b_pk]['p']
                    b_source = b_pks[s_b_pk]['b']
            if not p_source:
                p_source = p_dest
            if p_source != p_dest:
                b_dest.area = b_source.area
                b_dest.row = b_source.row
                b_dest.place_number = b_source.place_number
                b_dest.grave_number = b_source.grave_number
                b_dest.grave = b_source.grave
                b_dest.place = b_source.place
                b_dest.save()
                write_log(
                    request,
                    b_dest,
                    _(u"Изменено место при объединении дублируемых захоронений\n"
                      u"'%(old_place)s' -->\n"
                      u"'%(new_place)s'"
                     ) % dict(
                         old_place = p_dest.full_name(),
                         new_place = p_source.full_name(),
                ))

            r_resp = request.POST.get('source_responsible_')
            r_source = None
            if r_resp:
                m = re.search(r'^source_responsible_(\d+)$', r_resp)
                if m:
                    s_b_pk = m.group(1)
                    if s_b_pk not in b_pks:
                        raise Http404
                    r_source = b_pks[s_b_pk]['r']
            if r_source and r_source != b_dest.place.responsible:
                old_responsible = b_dest.place.responsible
                old_responsible_str = old_responsible and \
                    old_responsible.full_human_name() or _(u"<отсутствовал>")
                b_dest.place.responsible = r_source.deep_copy()
                b_dest.place.save()
                write_log(
                    request,
                    b_dest.place,
                    _(u"Изменен ответственный при объединении дублируемых захоронений\n"
                      u"'%(old_responsible)s' -->\n"
                      u"'%(new_responsible)s'"
                     ) % dict(
                         old_responsible = old_responsible_str,
                         new_responsible = b_dest.place.responsible and \
                             b_dest.place.responsible.full_human_name() or '',
                ))

            b_photos = []
            for r in request.POST:
                m= re.search(r'^source_photo_(\d+)$', r)
                if m and request.POST[r] == r:
                    b_photo_pk = m.group(1)
                    if b_photo_pk not in b_pks:
                        raise Http404
                    if b_photo_pk not in b_photos:
                        b_photos.append(b_photo_pk)
            ## Надо ли удалять фотки в месте - destination?
            ## Только если:
            ##   - pd_dest == p_source
            ##   - в p_dest есть фотки
            ##   - среди мест в b_pks нет этого места
            #if p_dest == p_source and p_dest.placephoto_set.exists():
                #save_these_photos = False
                #for b_pk in b_photos:
                    #if b_pks[b_pk]['p'] == p_dest:
                        #save_these_photos = True
                        #break
                #if not save_these_photos:
                    #for photo in p_dest.placephoto_set.all():
                        #url = ''
                        #if photo.bfile:
                            #url = request.build_absolute_uri(photo.bfile.url)
                        #photo.delete_only_rec()
                        #write_log(
                            #request,
                            #p_dest,
                            #_(u"Удалено фото при объединении дублируемых захоронений\n%s") % url
                        #)
            for b_pk in b_photos:
                p = b_pks[b_pk]['p']
                if p != b_dest.place:
                    for photo in p.placephoto_set.all():
                        content = None
                        if photo.bfile:
                            try:
                                fpath = os.path.join(settings.MEDIA_ROOT, photo.bfile.name)
                                f = open(fpath, "rb")
                                content = ContentFile(f.read())
                                f.close()
                            except IOError:
                                pass
                        new_photo = PlacePhoto.objects.create(
                            place=b_dest.place,
                            creator=request.user,
                            comment=photo.comment,
                            original_name=photo.original_name,
                            lat=photo.lat,
                            lng=photo.lng,
                        )
                        if content:
                            name = photo.original_name
                            if not name:
                                name = os.path.basename(photo.bfile.name)
                            new_photo.bfile.save(name, content)
                        PlacePhoto.objects.filter(pk=new_photo.pk).update(
                            dt_created=photo.dt_created,
                        )
                        url = ''
                        if new_photo.bfile:
                            url = request.build_absolute_uri(new_photo.bfile.url)
                        write_log(
                            request,
                            b_dest.place,
                            _(u"Прикреплено фото из другого места\n"
                              u"(%(old_place)s)\n"
                              u"при объединении дублируемых захоронений\n"
                              u"%(url)s") % dict(
                                  old_place=p.full_name(),
                                  url=url,
                        ))

            for b_pk in b_pks:
                if b_pk != b_dest_pk:
                    b = b_pks[b_pk]['b']
                    b.grave = None
                    b.annulated = True
                    b.save()
                    write_log(request, b,
                            _(u"Захоронение аннулировано при объединении дублируемых захоронений"))

        return redirect(request.get_full_path())

burials_double = BurialDoubleView.as_view()
