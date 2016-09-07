# coding=utf-8

import json
import re, decimal

from django.core.files.base import ContentFile
from django.core.validators import validate_email, URLValidator
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.db.models.query_utils import Q
from django.http import Http404, HttpResponse
from django.views.generic.base import View
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404

from persons.models import DeadPerson, AlivePerson, BasePerson, DocumentSource, Phone, \
                           CustomPlace, CustomPerson, MemoryGallery, \
                           CustomPersonPermission, MemoryGalleryPermission
from persons.serializers import AlivePersonSerializer, DeadPersonSerializer, PhoneSerializer, \
                                CustomPlaceDetailSerializer, CustomPlaceListSerializer, \
                                CustomPlaceEditSerializer, DeadPerson2Serializer, \
                                CustomPersonSerializer, CustomPerson2Serializer, \
                                CustomPerson3Serializer, CustomPerson4Serializer, \
                                MemoryGallerySerializer, MemoryGallery2Serializer
from orders.serializers import OrderSerializer

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.exceptions import PermissionDenied

from pd.models import UnclearDate, SafeDeleteMixin, validate_phone_as_number, CheckLifeDatesMixin
from burials.models import Cemetery, Place, PlacePhoto, Burial, Grave
from logs.models import write_log, LogOperation
from users.models import Org, PermitIfCabinet, user_dict, \
                         PermitIfUgh, PermitIfTradeOrCabinet, is_trade_user, is_cabinet_user, \
                         is_ugh_user, is_loru_user
from orders.models import Order, ResultFile
from geo.models import Location

from pd.utils import utcisoformat, get_image, is_video, str_to_bool_or_None
from pd.views import ServiceException

class AutocompleteFIO(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']

        fio = [f.strip('.') for f in query.split(' ')]
        q = Q()
        if len(fio) > 2:
            q &= Q(middle_name__istartswith=fio[2])
        if len(fio) > 1:
            q &= Q(first_name__istartswith=fio[1])
        if len(fio) > 0:
            q &= Q(last_name__istartswith=fio[0])

        user = request.user
        if is_ugh_user(user):
            ugh_q = Q(burial__ugh=user.profile.org)
        elif is_loru_user(user):
            loru = user.profile.org
            ugh_q = Q(burial__applicant_organization=loru) | Q(burial__loru=loru) | Q(burial__ugh__loru_list__loru=loru)
        else:
            ugh_q = Q()
        q &= ugh_q

        cemeteries_editable = request.GET.get('cemeteries_editable')
        if cemeteries_editable:
            q &= Q(burial__cemetery__in=Cemetery.editable_ugh_cemeteries(user))
        else:
            cemetery = request.GET.get('cemetery')
            if cemetery:
                q &= Q(burial__cemetery__name=cemetery)

        persons = DeadPerson.objects.filter(q).distinct('last_name', 'first_name', 'middle_name')
        return HttpResponse(json.dumps([{'value': unicode(c)} for c in persons[:20]]), mimetype='text/javascript')

autocomplete_fio = AutocompleteFIO.as_view()

class AutocompleteNamesMixin(object):

    def get_names(self, what, query, user, limit=None, within_dead=False):
        """
        Поиск для autocomplete имен, отчеств

        what:           firstname или last_name
        query:          набираемая строка
        user:
        limit:          ограничение вывода
        within_dead:    искать среди усопших, внутри своей организации,
                        иначе имена/отчества ищутся среди всех, живых и мертвых
        """
        valid = True
        if not query or not isinstance(query, basestring):
            valid = False
        if valid:
            field_map = dict(firstname='first_name', middlename='middle_name')
            try:
                field_name = field_map[what.lower()]
            except (AttributeError, KeyError):
                # не строка (AttributeError при lower()); нет в словаре (KeyError)
                valid = False
        if valid:
            q = Q(**{ '%s__istartswith' % field_name: query })
            if within_dead:
                model = DeadPerson
                if is_ugh_user(user):
                    q &= Q(burial__ugh=user.profile.org)
                elif is_loru_user(user):
                    loru = user.profile.org
                    q &= Q(burial__applicant_organization=loru) | Q(burial__loru=loru) | Q(burial__ugh__loru_list__loru=loru)
            else:
                model = BasePerson
            qs = model.objects.filter(q).order_by(field_name).distinct(field_name)
            if limit:
                qs = qs[:limit]
            return  [ getattr(c, field_name) for c in qs ]
        else:
            return []

class AutocompleteName(AutocompleteNamesMixin, View):
    def get(self, request, what, *args, **kwargs):
        query = request.GET.get('query')
        names = [ {'value': name} for name in self.get_names(what, query, request.user, limit=20) ]
        return HttpResponse(json.dumps(names), mimetype='text/javascript')

autocomplete_name = AutocompleteName.as_view()

class ApiAutocompletePersons(AutocompleteNamesMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(
            data=[ name for name in self.get_names(
                request.GET.get('type'),
                request.GET.get('query'),
                request.user,
                within_dead=True,
            )],
            status=200
        )

api_autocomplete_persons = ApiAutocompletePersons.as_view()

class AutocompleteAlive(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']

        fio = [f.strip('.') for f in query.split(' ')]
        q = Q()
        if len(fio) > 2:
            q &= Q(middle_name__istartswith=fio[2])
        if len(fio) > 1:
            q &= Q(first_name__istartswith=fio[1])
        if len(fio) > 0:
            q &= Q(last_name__istartswith=fio[0])

        persons = AlivePerson.objects.filter(q).distinct('last_name', 'first_name', 'middle_name')
        return HttpResponse(json.dumps([{'value': unicode(c)} for c in persons[:20]]), mimetype='text/javascript')

autocomplete_alive = AutocompleteAlive.as_view()

class AutocompleteDocSources(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['query']
        dcs = DocumentSource.objects.filter(name__icontains=query)
        return HttpResponse(json.dumps([{'value': unicode(c)} for c in dcs[:20]]), mimetype='text/javascript')

autocomplete_docsources = AutocompleteDocSources.as_view()


class AlivePersonViewSet(viewsets.ModelViewSet):
    model = AlivePerson
    serializer_class = AlivePersonSerializer
    permission_classes = (IsAuthenticated,)

    #def get_queryset(self):
    #    # TODO: perfomance issue
    #    responcible_ids = [i.responsible.pk for i in Place.objects.filter(cemetery__ugh=self.request.user.profile.org, responsible__isnull=False).all()]
    #    #.distinct('responsible')
    #    return self.model.objects.filter(pk__in=responcible_ids).all()

    def pre_save(self, object):
        if object.pk:
            old_obj = self.model.objects.get(pk=object.pk)
            write_log(
                self.request,
                object,
                _(u'Ответственный изменен с "%(old_obj)s" на "%(object)s"') % dict(
                    old_obj=old_obj, object=object
            ))
        else:
            write_log(self.request, object, _(u'Ответственный создан'))


class DeadPersonViewSet(viewsets.ModelViewSet):
    model = DeadPerson
    serializer_class = DeadPersonSerializer
    permission_classes = (IsAuthenticated,)



class PhoneViewSet(viewsets.ModelViewSet):
    model = Phone
    serializer_class = PhoneSerializer
    permission_classes = (IsAuthenticated,)

    #def get_queryset(self):
    #    # TODO: perfomance issue
    #    responcible_ids = [i.responsible.pk for i in Place.objects.filter(cemetery__ugh=self.request.user.profile.org, responsible__isnull=False).all()]
    #    #.distinct('responsible')
    #    return self.model.objects.filter(pk__in=responcible_ids).all()

    def pre_save(self, object):
        if object.pk:
            old_obj = self.model.objects.get(pk=object.pk)
            write_log(
                self.request,
                object,
                _(u'Телефон изменен с "%(old_obj)s" на "%(object)s"') % dict(
                    old_obj=old_obj, object=object
            ))
        else:
            write_log(self.request, object, _(u'Телефон создан'))

class ApiClientPlacesMixin(CheckLifeDatesMixin):

    def get_customplace(self, pk):
        try:
            customplace = CustomPlace.objects.get(pk=pk)
        except CustomPlace.DoesNotExist:
            raise Http404
        if not is_trade_user(self.request.user) and \
           customplace.user and customplace.user != self.request.user:
            raise Http404
        return customplace

class ApiClientPlacesView(APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request):
        return Response(
            data=[CustomPlaceListSerializer(customplace,context=dict(request=request)).data \
                  for customplace in CustomPlace.objects.filter(user=request.user).order_by('pk')],
            status=200,
        )

    def post(self, request):
        place_id = request.DATA.get('placeId')
        if place_id:
            try:
                place = Place.objects.get(pk=place_id)
                customplace, created_ = CustomPlace.get_or_create_from_place(
                    user=request.user,
                    place=place
                )
                if created_:
                    customplace.fill_custom_deadmen()
                serializer = CustomPlaceEditSerializer(
                    customplace,
                    context=dict(request=request),
                )
            except Place.DoesNotExist:
                raise Http404
        else:
            serializer = CustomPlaceEditSerializer(
                data=request.DATA,
                context=dict(request=request),
            )
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=400)
        return Response(serializer.data, status=200)

api_client_places = ApiClientPlacesView.as_view()

class ApiClientPlacesDetailView(ApiClientPlacesMixin, APIView):
    permission_classes = (PermitIfTradeOrCabinet,)

    def get(self, request, pk):
        return Response(
            data=CustomPlaceDetailSerializer(self.get_customplace(pk),context=dict(request=request)).data,
            status=200,
        )

    def put(self, request, pk):
        if not is_cabinet_user(request.user):
            raise PermissionDenied
        customplace = self.get_customplace(pk)
        context = dict(request=request)
        if 'performerId' in request.DATA:
            favorite_performer_id = request.DATA['performerId']
            if favorite_performer_id:
                message = None
                try:
                    favorite_performer = Org.objects.get(pk=favorite_performer_id)
                    if not favorite_performer.is_trade():
                        message = _(u'Организация, performerId: %s, не может выполнять заказы') % favorite_performer_id
                except Org.DoesNotExist:
                        message = _(u'Оганизация, performerId: %s, не существует') % favorite_performer_id
                if message:
                    return Response(dict(status='error', message=message), status=400)
                context['favorite_performer'] = favorite_performer
            else:
                context['favorite_performer'] = None
        serializer = CustomPlaceEditSerializer(
            customplace,
            data=request.DATA,
            context=context,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        if not is_cabinet_user(request.user):
            raise PermissionDenied
        customplace = self.get_customplace(pk)
        customplace.delete()
        return Response({}, status=200)

api_client_places_detail = ApiClientPlacesDetailView.as_view()

class ApiSelectedPermissionsMixin(object):

    def get_permissions_(self, request):
        selected = request.DATA.get('selected')
        selected_perms = []
        if selected:
            if isinstance(selected, basestring):
                try:
                    selected = json.loads(selected)
                except (ValueError, TypeError,):
                    pass
            if type(selected) != type(list()):
                raise ServiceException(_(u"Разрешения (selected: '%s') - не список") % selected)
            msg_invalid_item = _(u"%s в списке selected не является ни email, ни телефоном")
            for item in selected:
                try:
                    item = decimal.Decimal(item)
                    try:
                        validate_phone_as_number(str(item))
                        field = 'login_phone'
                    except ValidationError:
                        raise ServiceException(msg_invalid_item % item)
                except (decimal.InvalidOperation, TypeError):
                    try:
                        item = unicode(item)
                        validate_email(item)
                        field = 'email'
                    except ValidationError:
                        raise ServiceException(msg_invalid_item % item)
                selected_perms.append({field: item})
        return selected_perms

    def put_permissions_(self, instance, permissions, instance_existed=True):
        """
        Назначить instance of (MemoryGallery или CustomPerson) permissions

        permissions         - массив словарей dict(email=...) или dict(login_phone=...)
        instance_existed    - новый ли это instance (удалять или нет старые permissions)
        """
        if permissions:
            model = type(instance)
            if model == CustomPerson:
                # модель, куда кладутся разрешения:
                model = CustomPersonPermission
                field = 'customperson'
            elif model == MemoryGallery:
                model = MemoryGalleryPermission
                field = 'memorygallery'
            else:
                return
            filter_kwargs = { field : instance }
            if instance_existed:
                model.objects.filter(**filter_kwargs).delete()
            for perm in permissions:
                perm.update(filter_kwargs)
                model.objects.create(**perm)

class ApiCustompersonMixin(object):

    def get_customperson(self, pk, owner_only=False):
        customperson = get_object_or_404(CustomPerson, pk=pk)
        permitted = False
        request = self.request
        if owner_only:
            permitted = is_cabinet_user(request.user) and customperson.user == request.user
        elif customperson.permission == CustomPerson.PERMISSION_PUBLIC:
            permitted = True
        elif is_cabinet_user(request.user):
            if customperson.user == request.user:
                permitted = True
            elif customperson.permission == CustomPerson.PERMISSION_SELECTED:
                qs = Q(customperson=customperson)
                qs_email = qs_phone = qs_selected = None
                if request.user.email:
                    qs_email = Q(custompersonpermission__email__iexact=request.user.email)
                if request.user.customerprofile.login_phone:
                    qs_phone = Q(custompersonpermission__login_phone=request.user.customerprofile.login_phone)
                if qs_email and qs_phone:
                    qs_selected = qs_email | qs_phone
                elif qs_email:
                    qs_selected = qs_email
                elif qs_phone:
                    qs_selected = qs_phone
                if qs_selected and CustomPersonPermission.objects.filter(
                    qs & qs_selected
                    ).exists():
                    permitted = True
        if permitted:
            return customperson
        else:
            raise Http404

    def delete_customperson(self, pk):
        customperson = self.get_customperson(pk, owner_only=True)
        customperson.delete()
        return Response({}, status=200)

class ApiCustompersonDetailView(
        ApiCustompersonMixin,
        ApiClientPlacesMixin,
        ApiSelectedPermissionsMixin,
        APIView
      ):
    parser_classes = (MultiPartParser, JSONParser, )

    def get(self, request, pk):
        customperson = self.get_customperson(pk)
        return Response(
            data=CustomPerson3Serializer(customperson, context=dict(request=request)).data,
            status=200
        )
        
    def put(self, request, pk):
        try:
            customperson = self.get_customperson(pk, owner_only=True)
            context = dict(request=request)
            if 'placeId' in request.DATA:
                customplace_id = request.DATA['placeId']
                if isinstance(customplace_id, basestring) and customplace_id == 'null':
                    customplace_id = None
                if customplace_id:
                    customplace = self.get_customplace(customplace_id)
                else:
                    customplace = None
                context['customplace'] = customplace
            message = self.check_life_dates(instance=customperson)
            if message:
                raise ServiceException(message)
            is_dead = str_to_bool_or_None(request.DATA.get('isDead'))
            if is_dead == False:
                if UnclearDate.from_str_safe(request.DATA.get('dod')):
                    raise ServiceException(u'Нельзя задавать дату смерти для живого человека')
                if request.DATA.get('placeId'):
                    raise ServiceException(u'Живой человек не может иметь место захоронения')
            photo = request.FILES.get('photo')
            if photo:
                if photo.size > CustomPerson.MAX_PHOTO_SIZE * 1024 * 1024:
                    raise ServiceException(_(u"Размер фото превышает %d Мб") % CustomPerson.MAX_PHOTO_SIZE)
                if not get_image(photo):
                    raise ServiceException(_(u"Загруженное фото не является изображением"))
            serializer = CustomPerson3Serializer(
                customperson,
                data=request.DATA,
                context=context,
            )
            if serializer.is_valid():
                serializer.save()
                self.put_permissions_(
                    serializer.object,
                    self.get_permissions_(request),
                    instance_existed=True
                )
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)
        except ServiceException as excpt:
            return Response(data=dict(status='error', message=excpt.message), status=400)

    def delete(self, request, pk):
        return self.delete_customperson(pk)

api_customperson_detail = ApiCustompersonDetailView.as_view()

class ApiMemoryGalleryMixin(ApiSelectedPermissionsMixin):

    def make_object(self, customperson_pk, memory_pk=None):
        request = self.request
        try:
            customperson = self.get_customperson(customperson_pk, owner_only=True)
            if memory_pk:
                try:
                    gallery_item = MemoryGallery.objects.filter(
                        customperson=customperson,
                        pk=memory_pk,
                    ).distinct()[0]
                except IndexError:
                    raise Http404

            fields = {
                'customperson': customperson,
                'type': request.DATA.get('type'),
                'text': request.DATA.get('text'),
                'permission': request.DATA.get('permissions'),
                'event_date': UnclearDate.from_str_safe(request.DATA.get('eventDate')),
                'creator': request.user,
            }

            if memory_pk:
                # уберем необязательные поля, чтоб не заносились при put
                # и не путались с None. например,
                # зарос {"text": Null} и отсутствие 'text' в запросе,
                # это не одно и то же при редактировании
                for f in ('event_date', 'text'):
                    if f not in request.DATA:
                        del fields[f]

            file_ = request.FILES.get('mediaContent')
            if not fields['type']:
                raise ServiceException(_(u'Не задан тип (type)'))
            if fields['type'] not in [type_[0] for type_ in MemoryGallery.TYPE_CHOICES]:
                raise ServiceException(_(u'Неверный тип (type)'))
            need_media = fields['type'] in (MemoryGallery.TYPE_IMAGE, MemoryGallery.TYPE_VIDEO)
            need_text = fields['type'] in (MemoryGallery.TYPE_TEXT, MemoryGallery.TYPE_LINK)
            if need_media and not file_:
                raise ServiceException(_(u'Тип (type) %s требует загружаемого файла (mediaContent)') % fields['type'])
            if not need_media and file_:
                raise ServiceException(_(u'Тип (type) %s исключает загружаемый файл (mediaContent)') % fields['type'])
            if need_text and \
               (not fields['text'] or not fields['text'].strip()):
                raise ServiceException(_(u'Тип (type) %s требует непустой текст') % fields['type'])
            if fields['type'] == MemoryGallery.TYPE_LINK:
                validate = URLValidator(verify_exists=False)
                if not re.search(r'^\w+\://', fields['text'], flags=re.I):
                    fields['text'] = u"http://%s" % fields['text']
                try:
                    validate(fields['text'])
                except ValidationError:
                    raise ServiceException(_(u'Тип (type) %s требует правильную ссылку') % fields['type'])
            if fields['type'] == MemoryGallery.TYPE_IMAGE:
                if file_.size > MemoryGallery.MAX_IMAGE_SIZE * 1024 * 1024:
                    raise ServiceException(
                        _(u"Размер изображения не должен превышать %sМб") % MemoryGallery.MAX_IMAGE_SIZE
                    )
                file_content = ContentFile(file_.read())
                if not get_image(file_content):
                    raise ServiceException(_(u"Прикрепленный файл не является изображением"))
            elif fields['type'] == MemoryGallery.TYPE_VIDEO:
                file_content = ContentFile(file_.read())
                if not is_video(file_content):
                    raise ServiceException(_(u"Загруженный файл не является видео"))
            if fields['permission']:
                known_permissions = [unicode(p[0]) for p in MemoryGallery.PERMISSION_CHOICES]
                if fields['permission'] not in known_permissions:
                    raise ServiceException(
                        _(u"Неизвестное разрешение (permissions): %s") % fields['permission']
                    )
            else:
                # Будет по умолчанию: private
                del fields['permission']
            selected_perms = self.get_permissions_(request)
            if memory_pk:
                for f in fields:
                    setattr(gallery_item, f, fields[f])
                    gallery_item.save()
            else:
                gallery_item = MemoryGallery.objects.create(**fields)
            # Можно было: if file_: fields['bfile'] = file_, без промежуточного буфера file_content,
            # после чего ... create(**fields), однако (!)
            # в gallery_item.bfile.path фигурирует gallery_item.pk, что еще неизвестно при .create(),
            # посему gallery_item.bfile сохраняем отдельно в уже созданный gallery_item
            if file_:
                if memory_pk:
                    gallery_item.delete_from_media()
                gallery_item.bfile.save(file_.name, file_content)
            self.put_permissions_(gallery_item, selected_perms, instance_existed=bool(memory_pk))
            return Response(
                data=MemoryGallery2Serializer(gallery_item, context=dict(request=request)).data,
                status=200,
            )
        except ServiceException as excpt:
            return Response(data=dict(status='error', message=excpt.message), status=400)

    def get_qs(self, request, pk, memory_pk=None):
        customperson = get_object_or_404(CustomPerson, pk=pk)
        is_cabinet_user_ = is_cabinet_user(request.user)
        is_owner = is_cabinet_user_ and request.user == customperson.user
        qs_public  = Q(permission=MemoryGallery.PERMISSION_PUBLIC)
        if memory_pk:
            qs_owner = Q(pk=memory_pk)
        else:
            qs_owner = Q(customperson=customperson)

        if is_owner:
            qs = qs_owner
        elif is_cabinet_user_:
            qs_email = qs_phone = qs_selected = None
            if request.user.email:
                qs_email = Q(memorygallerypermission__email__iexact=request.user.email)
            if request.user.customerprofile.login_phone:
                qs_phone = Q(memorygallerypermission__login_phone=request.user.customerprofile.login_phone)

            if qs_email and qs_phone:
                qs_selected = qs_email | qs_phone
            elif qs_email:
                qs_selected = qs_email
            elif qs_phone:
                qs_selected = qs_phone
            qs = qs_public
            if qs_selected:
                qs_selected &= Q(permission=MemoryGallery.PERMISSION_SELECTED)
                qs = qs | qs_selected
            qs &= qs_owner
        else:
            qs = qs_public & qs_owner
        return qs

class ApiCustompersonMemoryGalleryView(ApiCustompersonMixin, ApiMemoryGalleryMixin, APIView):
    parser_classes = (MultiPartParser, JSONParser, )
    
    def get(self, request, pk):
        qs = self.get_qs(request, pk)

        offset = self.request.GET.get('offset') and int(self.request.GET.get('offset'))
        limit = self.request.GET.get('limit') and int(self.request.GET.get('limit'))
        filter = MemoryGallery.objects.filter(qs).distinct()
        if offset and limit:
            filter = filter[offset:offset+limit]
        elif offset:
            filter = filter[offset:]
        elif limit:
            filter = filter[:limit]

        return Response(
            [ MemoryGallery2Serializer(gallery_item, context=dict(request=request)).data \
              for gallery_item in filter ],
            status=200,
        )

    @transaction.commit_on_success
    def post(self, request, pk):
        return self.make_object(pk)

api_customperson_memory_gallery = ApiCustompersonMemoryGalleryView.as_view()

class ApiCustompersonMemoryGalleryDetail(ApiCustompersonMixin, ApiMemoryGalleryMixin, APIView):
    parser_classes = (MultiPartParser, JSONParser, )
    
    def get(self, request, pk, memory_pk):
        qs = self.get_qs(request, pk, memory_pk)
        try:
            gallery_item = MemoryGallery.objects.filter(qs).distinct()[0]
        except IndexError:
            raise Http404
        return Response(
            MemoryGallery2Serializer(gallery_item, context=dict(request=request)).data,
            status=200,
        )

    @transaction.commit_on_success
    def put(self, request, pk, memory_pk):
        return self.make_object(pk, memory_pk)

    def delete(self, request, pk, memory_pk):
        customperson = self.get_customperson(pk, owner_only=True)
        try:
            gallery_item = MemoryGallery.objects.filter(
                customperson=customperson,
                pk=memory_pk,
            ).distinct()[0]
        except IndexError:
            raise Http404
        gallery_item.delete()
        return Response({}, status=200,)

api_customperson_memory_gallery_detail = ApiCustompersonMemoryGalleryDetail.as_view()

class ApiClientPlacesDeadmansView(ApiClientPlacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        return Response(
            data=[CustomPersonSerializer(customperson, context=dict(request=request)).data \
                  for customperson in CustomPerson.objects.filter(customplace=self.get_customplace(pk))],
            status=200,
        )

    def post(self, request, pk):
        customplace=self.get_customplace(pk)
        message = self.check_life_dates()
        if message:
            return Response({"status": "error", "message": message}, 400)
        serializer = CustomPersonSerializer(
            data=request.DATA,
            context=dict(
                request=request,
                customplace=customplace,
            ),
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

api_client_places_deadmans = ApiClientPlacesDeadmansView.as_view()

class ApiClientPlacesDeadmansDetailView(ApiClientPlacesMixin, ApiCustompersonMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def put(self, request, pk, deadman_pk):
        customplace = self.get_customplace(pk)
        customperson = self.get_customperson(deadman_pk, owner_only=True)
        if not customperson.customplace or customperson.customplace != customplace:
            raise Http404
        message = self.check_life_dates()
        if message:
            return Response({"status": "error", "message": message}, 400)
        serializer = CustomPersonSerializer(
            customperson,
            data=request.DATA,
            context=dict(request=request),
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk, deadman_pk):
        customplace = self.get_customplace(pk)
        customperson = self.get_customperson(deadman_pk, owner_only=True)
        if not customperson.customplace or customperson.customplace != customplace:
            raise Http404
        customperson.delete()
        return Response({}, status=200)

api_client_places_deadmans_detail = ApiClientPlacesDeadmansDetailView.as_view()

class ApiClientDeadmansView(APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request):
        data = list()
        for pk in re.split(r'[,\s]+', request.GET.get('ids', '').strip()):
            try:
                customperson=CustomPerson.objects.get(pk=pk, user=request.user)
            except (ValueError, CustomPerson.DoesNotExist, ):
                raise Http404
            data.append(
                CustomPerson2Serializer(customperson, context=dict(request=request)).data
            )
        return Response(
            data=data,
            status=200,
        )

api_client_deadmans = ApiClientDeadmansView.as_view()

class ApiClientPersonsView(ApiClientPlacesMixin, ApiSelectedPermissionsMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request):
        return Response(
            data=[ CustomPerson4Serializer(customperson, context=dict(request=request)).data \
                   for customperson in CustomPerson.objects.filter(user=request.user)
            ],
            status=200,
        )

    def post(self, request):
        try:
            customplace_id = request.DATA.get('placeId')
            if customplace_id:
                customplace = self.get_customplace(customplace_id)
            else:
                customplace = None
            message = self.check_life_dates()
            if message:
                raise ServiceException(message)
            serializer = CustomPerson4Serializer(
                data=request.DATA,
                context=dict(request=request, customplace=customplace),
            )
            if serializer.is_valid():
                serializer.save()
                self.put_permissions_(
                    serializer.object,
                    self.get_permissions_(request),
                    instance_existed=False,
                )
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)
        except ServiceException as excpt:
            return Response(data=dict(status='error', message=excpt.message), status=400)

api_client_persons = ApiClientPersonsView.as_view()

class ApiClientPersonsDetailView(
        ApiClientPlacesMixin,
        ApiCustompersonMixin,
        ApiSelectedPermissionsMixin,
        APIView
      ):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        customperson = self.get_customperson(pk)
        return Response(
            data=CustomPerson4Serializer(customperson, context=dict(request=request)).data,
            status=200,
        )

    def put(self, request, pk):
        try:
            customperson = self.get_customperson(pk, owner_only=True)
            context = dict(request=request)
            if 'placeId' in request.DATA:
                customplace_id = request.DATA['placeId']
                if customplace_id:
                    customplace = self.get_customplace(customplace_id)
                else:
                    customplace = None
                context['customplace'] = customplace
            message = self.check_life_dates()
            if message:
                raise ServiceException(message)
            serializer = CustomPerson4Serializer(
                customperson,
                data=request.DATA,
                context=context,
            )
            if serializer.is_valid():
                serializer.save()
                self.put_permissions_(
                    serializer.object,
                    self.get_permissions_(request),
                    instance_existed=True,
                )
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)
        except ServiceException as excpt:
            return Response(data=dict(status='error', message=excpt.message), status=400)

    def delete(self, request, pk):
        return self.delete_customperson(pk)

api_client_persons_detail = ApiClientPersonsDetailView.as_view()

class ApiClientPlacesAttachmentsView(ApiClientPlacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        customplace = self.get_customplace(pk)
        gallery = [dict(
                    id=resultfile.pk,
                    title=None,
                    type=resultfile.type,
                    url=request.build_absolute_uri(resultfile.bfile.url),
                    createdAt=utcisoformat(resultfile.date_of_creation),
                    createdBy=user_dict(resultfile.creator),
                ) \
                for resultfile in ResultFile.objects.filter(
                    order__customplace=customplace,
                    ).order_by('-date_of_creation') \
                if resultfile.bfile
        ]
        if customplace.place:
            gallery += [dict(
                        id=placephoto.pk,
                        title=None,
                        type=ResultFile.TYPE_IMAGE,
                        url=request.build_absolute_uri(placephoto.bfile.url),
                        createdAt=utcisoformat(placephoto.date_of_creation),
                        createdBy=user_dict(placephoto.creator),
                    ) \
                    for placephoto in PlacePhoto.objects.filter(
                        place=customplace.place,
                        ).order_by('-date_of_creation') \
                    if placephoto.bfile
            ]
        return Response(
            data=gallery,
            status=200,
        )

api_client_places_attachments = ApiClientPlacesAttachmentsView.as_view()

class ApiClientPlacesOrdersView(ApiClientPlacesMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request, pk):
        customplace=self.get_customplace(pk)
        return Response(data=[OrderSerializer(o).data \
                              for o in Order.objects.filter(customplace=customplace) \
                        ], status=200)

api_client_places_orders = ApiClientPlacesOrdersView.as_view()

class ApiOmsBurialsView(CheckLifeDatesMixin, APIView):
    permission_classes = (PermitIfUgh,)

    def post(self, request):
        place_pk = request.DATA.get('placeId')
        place, status, message = Place.check_invent_place(request, place_pk)
        if not message:
            status = 400
            message = self.check_life_dates(format='d.m.y')
        if message:
            return Response(data=dict(status='error', message=message), status=status)
        serializer = DeadPerson2Serializer(
            data=request.DATA,
            context=dict(request=request),
        )
        if serializer.is_valid():
            with transaction.commit_on_success():
                deadman = serializer.save()
                grave, grave_created = Grave.objects.get_or_create(place=place, grave_number=1)
                burial = Burial.objects.create(
                    burial_type=Burial.BURIAL_NEW if grave_created else Burial.BURIAL_OVER,
                    burial_container=Burial.CONTAINER_COFFIN,
                    source_type=Burial.SOURCE_ARCHIVE,
                    place=place,
                    cemetery=place.cemetery,
                    area=place.area,
                    row=place.row,
                    place_number=place.place,
                    grave=grave,
                    grave_number=1,
                    deadman=deadman,
                    ugh=place.cemetery.ugh,
                    status=Burial.STATUS_CLOSED,
                    changed_by=request.user,
                    flag_no_applicant_doc_required = True,
                )
                write_log(request, burial, operation=LogOperation.BURIAL_PHOTO_PROCESSED)
                return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

api_oms_burials = ApiOmsBurialsView.as_view()

class ApiOmsBurialsDetailView(CheckLifeDatesMixin, APIView):
    permission_classes = (PermitIfUgh,)

    def put(self, request, pk):
        status = 404
        message = ''
        try:
            deadman = DeadPerson.objects.get(pk=pk)
        except DeadPerson.DoesNotExist:
            message = _(u'Нет усопшего с id = %s') % pk
        else:
            message_noplace = _(u'Усопший с id = %s не имеет привязки к захоронению/месту') % pk
            try:
                burial = deadman.burial_set.all()[0]
            except IndexError:
                message = message_noplace
            else:
                place = burial.place
                if not place:
                    message = message_noplace
                else:
                    place, status, message = Place.check_invent_place(request, place.pk)
        if not message:
            status = 400
            message = self.check_life_dates(instance=deadman, format='d.m.y')
        if message:
            return Response(data=dict(status='error', message=message), status=status)
        serializer = DeadPerson2Serializer(
            deadman,
            data=request.DATA,
            context=dict(request=request),
        )
        if serializer.is_valid():
            serializer.save()
            write_log(request, burial, _(u'Захоронение изменено при обработке фото места'))
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

api_oms_burials_detail = ApiOmsBurialsDetailView.as_view()
