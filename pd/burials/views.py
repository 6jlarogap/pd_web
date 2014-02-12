# coding=utf-8

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.db.models import Count, Avg
from django.shortcuts import redirect, render, get_object_or_404
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from django.utils.translation import ugettext as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from django.contrib.contenttypes.models import ContentType

from geo.models import Country, Region, Street, City

from pd.views import RequestToFormMixin, FormInvalidMixin

from burials.forms import CemeteryForm, AreaFormset, PlaceEditForm, AddOrgForm, AreaMergeForm, BurialfileCommentEditForm
from burials.models import Cemetery, Place, Area, BurialFiles, Grave, Burial, AreaPhoto, GravePhoto, ExhumationRequest, AreaPurpose, PlaceSize
from burials.burials_views import *
from logs.models import write_log, log_object, prepare_m2m_log, compare_obj
from users.models import Profile, Org
from persons.models import Phone, AlivePerson
from geo.models import Location

# REST import
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# EOF REST import

from django.db import transaction


from serializers import CemeterySerializer, AreaSerializer, PlaceSerializer, AreaPurposeSerializer, \
    GraveSerializer, BurialSerializer, BurialListSerializer, AreaPhotoSerializer, GravePhotoSerializer, ExhumationRequestSerializer, PlaceSizeSerializer

from persons.serializers import AlivePersonSerializer, PhoneSerializer
from geo.serializers import LocationSerializer, LocationStaticSerializer, LocationDataSerializer
from logs.serializers import LogSerializer

from logs.views import getLogQuerySet

def getCemetery(request):
    try:
        # PUT request issue
        cemetery_id = int(request.GET.get('cemetery_id'))
        assert cemetery_id>0, u'Wrong id'
    except:
        raise Http404()
    else:
        return get_object_or_404(Cemetery, id=cemetery_id, ugh=request.user.profile.org)


def getArea(request):
    try:
        # PUT request issue
        area_id = int(request.GET.get('area_id'))
        assert area_id>0, u'Wrong id'
    except:
        raise Http404()
    else:
        return get_object_or_404(Area, id=area_id, cemetery__ugh=request.user.profile.org)

def getPlace(request):
    try:
        # PUT request issue
        place_id = int(request.GET.get('place_id'))
        assert place_id>0, u'Wrong id'
    except:
        raise Http404()
    else:
        return get_object_or_404(Place, id=place_id, cemetery__ugh=request.user.profile.org)



class UGHRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated() or not getattr(self.request.user, 'profile', None) or not self.request.user.profile.is_ugh():
            return redirect('/')
        return View.dispatch(self, request, *args, **kwargs)

class LoginRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated():
            return redirect('/')
        return View.dispatch(self, request, *args, **kwargs)


class CemeteryViewSet(viewsets.ModelViewSet):
    model = Cemetery
    form_class = CemeteryForm
    serializer_class = CemeterySerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None

    def get_queryset(self):
        return  Cemetery.objects.filter(ugh=self.request.user.profile.org).all()

    
    def check_semetery_name(self, request, pk=None):
        name = request.DATA.get('name')
        if not name:
            return {"__all__":[u"Название кладбища обязательно",]}
        qs = self.get_queryset().filter(ugh=self.request.user.profile.org, name__iexact= name)
        if pk:
            qs = qs.exclude(pk=pk)
        if qs.exists():
            return {"__all__":[u"Кладбище с таким названием уже существует",]}

    
    def create(self, request, *args, **kwargs):
        """
        Add "unique together" check in parent class 
        """
        data = self.check_semetery_name(request)
        if data:
            return Response(status=400, data=data)
        return super(CemeteryViewSet, self).create(request, *args, **kwargs)


    def update(self, request, *args, **kwargs):
        try:
            pk = int(request.DATA.get('id'))
        except:
            return Response(status=400)
        data = self.check_semetery_name(request, pk)
        if data:
            return Response(status=400, data=data)
        return super(CemeteryViewSet, self).update(request, *args, **kwargs)
    

    def pre_save(self, obj):
        address = self.request.DATA.get('obj_address')
        address_serializer = LocationDataSerializer(obj.address, data=address, partial=True)
        
        obj.creator = self.request.user
        obj.ugh = self.request.user.profile.org
        
        if not address_serializer.is_valid():
            return Response(status=400, data=address_serializer.errors)
        
        obj.address = address_serializer.save()
        obj.address.set_related_addr(data=address)
        obj.address.save()
        
        try:
            old = self.model.objects.get(pk=obj.pk)
        except self.model.DoesNotExist:
            old = None
        except AttributeError:
            old = None
        log_object(self.request, obj=obj, old=old, new=obj, reason=_(u'Кладбище изменено'))
        #write_log(self.request, obj, _(u'Кладбище изменено'))

        # TODO: send signal
        phone = self.request.DATA.get('obj_phones', [])
        if obj.pk:
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




    @action(methods=['GET',])
    def getform(self, request, pk=None):
        cemetery = get_object_or_404(self.get_queryset(), pk=pk)
        data = {
                "cemetery" : CemeterySerializer(cemetery).data,
                "responsible_phones" : [],
                "responsible_address" : {}
                }
        phone_set = cemetery.phone_set.all()
        data["phones"] = PhoneSerializer(phone_set).data
        data["cemetery"]["max_graves_count"] = request.user.profile.org.max_graves_count
        if cemetery.address:
            data["address"] = LocationStaticSerializer(cemetery.address).data

        return Response(status=200, data=data)


class SupervisorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated() and \
           request.user.profile and \
           request.user.profile.is_supervisor():
            return View.dispatch(self, request, *args, **kwargs)
        raise Http404


class CemeteryList(UGHRequiredMixin, ListView):
    template_name = 'cemetery_list.html'
    model = Cemetery

    def get_queryset(self):
        return Cemetery.objects.filter(ugh=self.request.user.profile.org)

manage_cemeteries = CemeteryList.as_view()


class CemeteryCreate(UGHRequiredMixin, RequestToFormMixin, FormInvalidMixin, CreateView):
    template_name = 'cemetery_create.html'
    form_class = CemeteryForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.ugh = self.request.user.profile.org
        self.object.save()
        write_log(self.request, self.object, _(u'Кладбище создано'))
        msg = _(u"<a href='%s'>Кладбище %s</a> создано") % (
            reverse('manage_cemeteries_edit', args=[self.object.pk]),
            self.object.name,
        )
        messages.success(self.request, msg)
        return redirect('manage_cemeteries')

manage_cemeteries_create = CemeteryCreate.as_view()

class CemeteryEdit(UGHRequiredMixin, RequestToFormMixin, FormInvalidMixin, UpdateView):
    template_name = 'cemetery_edit.html'
    form_class = CemeteryForm


    def get_queryset(self):
        return Cemetery.objects.filter(ugh=self.request.user.profile.org)

    def form_valid(self, form):
        self.object = form.save()
        msg = _(u"<a href='%s'>Кладбище %s</a> изменено") % (
            reverse('manage_cemeteries_edit', args=[self.object.pk]),
            self.object.name,
        )
        messages.success(self.request, msg)
        return redirect('manage_cemeteries')


class AreaViewSet(viewsets.ModelViewSet):
    model = Area
    serializer_class = AreaSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None

    def get_queryset(self):
        item = getCemetery(self.request)
        qs = self.model.objects.filter(cemetery=item)
        return  qs.all()

    def pre_save(self, object):
        item = getCemetery(self.request)
        object.cemetery = item

        try:
            old = self.model.objects.get(pk=object.pk)
        except self.model.DoesNotExist:
            old = None
        except AttributeError:
            old = None
        log_object(self.request, obj=object, old=old, new=object, reason=_(u'Участок изменен'))


    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(self.object)
        data = serializer.data
        data["max_graves_count"] = request.user.profile.org.max_graves_count
        return Response(data)



class PlaceViewSet(viewsets.ModelViewSet):
    model = Place
    serializer_class = PlaceSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None

    def get_queryset(self):
        item = getCemetery(self.request)
        qs = self.model.objects.filter(cemetery=item)
        if self.request.GET.get('area_id'):
            area  = getArea(self.request)
            qs = qs.filter(area=area)
        return  qs.all()

    def pre_save(self, object):
        
        item = getArea(self.request) # TODO: check this
        object.area = item
        self.new_msg = []
        self.old_responsible = object.responsible
        self.old_object = None
        
        #if item.pk:
        #    write_log(self.request, object, _(u'Место №%s изменено' % object.place))

        max_graves_count = self.request.user.profile.org.max_graves_count or 10
        try:
            self.places_count = int(self.request.DATA.get('places_count',1))
            assert self.places_count>0 and self.places_count<=max_graves_count
        except:
            data = {"__all__":[_(u"Количество могил должно быть от 1 до %d") % max_graves_count,]}
            return Response(status=400, data=data)

        responsible = self.request.DATA.get('obj_responsible')
        if object.pk and responsible:
            
            responsible_serializer =  AlivePersonSerializer(object.responsible, data=responsible, partial=True)
            if not responsible_serializer.is_valid():
                return Response(status=400, data=responsible_serializer.errors) 
            
            try:
                self.old_responsible = AlivePerson.objects.get(pk=object.responsible.pk)
            except AlivePerson.DoesNotExist:
                self.old_responsible = None
            except AttributeError:
                self.old_responsible = None
            object.responsible = responsible_serializer.save()

            #object.responsible.address_id = responsible.address

        try:
            self.old_object = self.model.objects.get(pk=object.pk)
        except self.model.DoesNotExist:
            self.old_object = None
        except AttributeError:
            self.old_object = None
        
        # Update grave point coords
        items = Grave.objects.filter(place=object).all()
        for item in items:
            item.lng = object.lng
            item.lat = object.lat
            item.save()
        return object

    def post_save(self, object, created=False):
        if created: 
            #    write_log(self.request, object, _(u'Место №%s создано')% object.place)
            for i in xrange(1,self.places_count+1):
                item = Grave(place=object, grave_number=i)
                item.save()

        if object.responsible:
            address = self.request.DATA.get('obj_responsible_address')
            address_serializer = LocationDataSerializer(object.responsible.address, data=address, partial=True)
            if not address_serializer.is_valid():
                return Response(status=400, data=address_serializer.errors)
            
            object.responsible.address = address_serializer.save()
            object.responsible.address.set_related_addr(data=address)

            old_phones = [i for i in object.responsible.phone_set.all()]
            
            phone = self.request.DATA.get('obj_responsible_phones', [])
            id_binds = {}
            ct = ContentType.objects.get_for_model(object.responsible)

            for i in phone:
                i["ct"] = ct.pk
                try:
                    phone_obj = object.responsible.phone_set.get(pk=i['id'])
                except:
                    phone_obj = None
                phone_serializer = PhoneSerializer(phone_obj, data=i)
                if not phone_serializer.is_valid():
                    return Response(status=400, data=phone_serializer.errors)
                res = phone_serializer.save()
                res.obj_id = object.responsible.pk
                res.save()                
                id_binds[res.id] = 1
            object.responsible.phone_set.exclude(pk__in=id_binds.keys()).delete()
        
            phone_set = object.responsible.phone_set.all()
            self.new_msg += prepare_m2m_log(_(u'Телефон'), old_phones,  phone_set)
            
          
                
        try:
            old_address = self.old_object.responsible.address
        except AttributeError:
            old_address = None

        try:   
            new_address = object.responsible.address
        except AttributeError:
            new_address = None
        
        if unicode(old_address)!= unicode(new_address):
            self.new_msg += [compare_obj(_(u'Адрес'), old_address, new_address)]
        
        if self.old_responsible and unicode(self.old_responsible) != unicode(object.responsible):
            self.new_msg += [compare_obj(_(u'Ответственный'), self.old_responsible, object.responsible)]

        log_object(self.request, obj=object, old=self.old_object, new=object, reason=_(u'Место %s изменено') % object.place, new_msg=self.new_msg)

        if object.responsible:
            object.responsible.save()


    @action(methods=['GET',])
    def getform(self, request, pk=None):
        cemetery = getCemetery(self.request)
        if self.request.GET.get('area_id'):
            area  = getArea(self.request)
        place = get_object_or_404(self.model, pk=pk, cemetery=cemetery, area=area)
        
        # Log set
        paginator = Paginator(getLogQuerySet(log_type="place", place=place), 10)
        page = request.GET.get('log_page')
        try:
            page = paginator.page(page)
        except:
            page = paginator.page(1)
        log_data = LogSerializer(page,many=True).data
        
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
                "place" : PlaceSerializer(place).data,
                "graves" : GraveSerializer(grave_list, many=True).data,
                "grave_count" : grave_count,
                #"burials" : BurialSerializer(burial_list, many=True).data,
                "responsible" : {},
                "responsible_phones" : [],
                "responsible_address" : {},
                "log": log_data,
                "log_page":page.number,
                "log_pages":page.paginator._num_pages,
                }
        data["place"]["graves_count"] = place.get_graves_count()
        data["place"]["available_count"] = place.available_count
        if place.responsible:
            phone_set = place.responsible.phone_set.all()
            data["responsible_phones"] = PhoneSerializer(phone_set).data
            data["responsible"] = AlivePersonSerializer(place.responsible).data 
            if place.responsible.address:
                data["responsible_address"] = LocationStaticSerializer(place.responsible.address).data
        return Response(status=200, data=data)


    @action(methods=['GET',])
    def getgraves(self, request, pk=None):
        cemetery = getCemetery(self.request)
        if self.request.GET.get('area_id'):
            area  = getArea(self.request)
        place = get_object_or_404(Place, pk=pk, cemetery=cemetery, area=area)

        page = request.GET.get('grave_page')
        paginator = Paginator(place.grave_set.all(), 10)
        try:
            grave_list = paginator.page(page)
        except:
            grave_list = paginator.page(1)
        
        burial_list = Burial.objects.filter(grave__place=place, grave__in=grave_list).all()
        return Response({
                         'count': place.grave_set.count(),
                         'page': grave_list.number,
                         'pages': grave_list.paginator._num_pages,
                         'graves': GraveSerializer(grave_list, many=True).data,
                         'burials': BurialSerializer(burial_list, many=True).data,
                         })


    @action(methods=['POST',])
    def setform(self, request, pk=None):
        form = request.GET.get('form')
        address = request.GET.get('address')
        phones = request.GET.get('phones')
        responcible = request.GET.get('responcible')
        return Response(status=200)

        
    @action(methods=['GET',])
    def cancel_exhumation(self, request, pk=None):
        cemetery = getCemetery(self.request)
        if self.request.GET.get('area_id'):
            area  = getArea(self.request)
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
    paginate_by = None

    #def get_queryset(self):
    #    qs = self.model.objects.filter(cemetery__ugh=self.request.user.profile.org)
    #    return  qs.all()



class GraveViewSet(viewsets.ModelViewSet):
    model = Grave
    serializer_class = GraveSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = 1

    #def delete(self, request, *args, **kwargs):
    #    write_log(self.request, self.get_object(), _(u'Могила №%d удалена') % object.grave_number)
      #  return super(GraveViewSet, self).delete(request, *args, **kwargs)

    def get_queryset(self):
        place = getPlace(self.request)
        return self.model.objects.filter(place=place).order_by('grave_number').all()

    def pre_save(self, object):
        # Update placer point coords
        res = Grave.objects.filter(place=object.place, lng__isnull=False, lat__isnull=False).\
            aggregate(lng=Avg('lng'), lat=Avg('lat')) #, cnt=Count('id')
        object.place.lat = res["lat"]
        object.place.lng = res["lng"]  
        object.place.save()
        
        """
        TODO: Newd review this. Replacement for "def move(self, request, pk=None):"
        current_qs = Grave.objects.filter(place__cemetery__ugh=self.request.user.profile.org)
        if current.filter(pk=pk).count():
            current = current_qs.get(pk=pk)
            if current.grave_number != object.grave_number:
                 current_qs = current_qs.filter(grave_number__gte=current.grave_number).all()
                 ind = object.grave_number
                 for row in current_qs:
                     ind += 1
                     row.grave_number = ind
                     row.save()
        """
        
        footer = ''
        try:
            old = self.model.objects.get(pk=object.pk)
        except self.model.DoesNotExist:
            footer = []
            old = None
            if object.is_wrong_fio:
                footer.append(u"Неверное ФИО")
            if object.is_military:
                footer.append(u"Воинская могила")
            if len(footer):
                footer = ", ".join(footer)
        except AttributeError:
            old = None
        log_object(self.request, obj=object.place, old=old, footer=footer, \
                   new=object, reason="", \
                   create_text=_(u"Могила %d создана") % object.grave_number)        
        return object


    """
    #@action(methods=['GET',])
    def move(self, request, pk=None):
        direction = request.GET.get('direction','forward')
        try:
            current = Grave.objects.filter(place__cemetery__ugh=self.request.user.profile.org).get(pk=pk)
            if direction==u'forward':
                direction = 1
                direction_text = _(u'вправо')
                assert current.grave_number+direction<=current.place.grave_set.count()
            else:
                direction = -1
                direction_text = _(u'влево')
                assert current.grave_number+direction>0

            swapped = Grave.objects.get(place=current.place, grave_number = current.grave_number+direction)
            t = current.grave_number
            t1 = swapped.grave_number
            write_log(self.request, current, _(u'Могила №%d  перемещена %s c №%d на №%d' % (t1, direction_text, t, t1)))
            #TODO: Transaction level?
            current.grave_number = 32767
            current.save()
            current.grave_number = t1
            swapped.grave_number = t
            swapped.save()
            current.save()
        except:
            pass
        return Response(status=200)
    """


    def destroy(self, request, pk=None):
        try:
            object = self.model.objects.get(pk=int(pk))
            #write_log(self.request, object.place, _(u'Могила №%d удалена') % object.grave_number)
            object.delete(request=request)
        except:
            raise Http404()
        return Response(status=200)


class BurialViewSet(viewsets.ModelViewSet):
    model = Burial
    serializer_class = BurialSerializer
    serializer_list_class = BurialListSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None

    def get_queryset(self):
        return self.model.objects.filter(cemetery__ugh=self.request.user.profile.org)

    def filter_queryset(self, queryset):
        # place_id filter removed. Exhumation issue

        item = getCemetery(self.request)
        queryset = queryset.filter(cemetery=item)
        
        id = self.request.GET.get('area_id')
        item = get_object_or_404(Area, id=id)
        queryset = queryset.filter(area=item)
        return  queryset

    def get_serializer_class(self):
        """
        Serilializer fetches a list of related items, result - resource overuse.
        Solution: replacement with easier serializer
        """
        if self.action == 'list':
            serializer_class = self.serializer_list_class
        else:
            serializer_class = self.serializer_class
        return serializer_class


    def pre_save(self, object):
        try:
            old = self.model.objects.get(pk=object.pk)
        except self.model.DoesNotExist:
            old = None
        except AttributeError:
            old = None
            footer = None
        log_object(self.request, obj=object.place, old=old, new=object, reason=_(u'Захоронение изменено'))        
        return object


class AreaPhotoViewSet(viewsets.ModelViewSet):
    model = AreaPhoto
    serializer_class = AreaPhotoSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None
    
    def get_queryset(self):
        qs = self.model.objects.filter(area__cemetery__ugh=self.request.user.profile.org)
        item = getArea(self.request)
        qs = qs.filter(area=item)
        return  qs.all()


class GravePhotoViewSet(viewsets.ModelViewSet):
    model = GravePhoto
    serializer_class = GravePhotoSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None
    def get_queryset(self):
        qs = self.model.objects.filter(grave__place__cemetery__ugh=self.request.user.profile.org)
        id = self.request.GET.get('grave_id')
        if id:
            item = get_object_or_404(Grave, id=id)
            qs = qs.filter(grave=item)
        return  qs.all()


class PlaceSizeViewSet(viewsets.ModelViewSet):
    model = PlaceSize
    serializer_class = PlaceSizeSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None
    def get_queryset(self):
        qs = self.model.objects.filter(org=self.request.user.profile.org)
        return  qs.all()


class ExhumationRequestViewSet(viewsets.ModelViewSet):
    model = ExhumationRequest
    serializer_class = ExhumationRequestSerializer
    permission_classes = (IsAuthenticated,)
    paginate_by = None
    def get_queryset(self):
        qs = self.model.objects.filter(place__cemetery__ugh=self.request.user.profile.org)
        id = self.request.GET.get('burial_id')
        if id:
            item = get_object_or_404(Burial, id=id)
            qs = qs.filter(burial=item)
        id = self.request.GET.get('place_id')
        if id:
            item = get_object_or_404(Place, id=id)
            qs = qs.filter(place=item)
        return  qs.all()




class CemeteryMerge(UGHRequiredMixin, TemplateView):
    template_name = 'cemetery_merge.html'

    def get_object(self):
        return get_object_or_404(Cemetery, ugh=self.request.user.profile.org, pk=self.kwargs['pk'])

    def get_form(self):
        return AreaMergeForm(data=self.request.POST or None, cemetery=self.get_object())

    def get_context_data(self, **kwargs):
        return {
            'cemetery': self.get_object(),
            'form': self.get_form(),
        }

    def post(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            form.save()
            write_log(self.request, self.object, _(u'Участки объединены'))
            msg = _(u"Участки <a href='%s'>кладбища %s</a> изменены") % (
                reverse('manage_cemeteries_edit', args=[self.object.pk]),
                self.object.name,
            )
            messages.success(self.request, msg)
            return redirect('manage_cemeteries_edit', self.get_object().pk)
        return self.get(request, *args, **kwargs)

manage_cemeteries_merge = CemeteryMerge.as_view()

class PlaceView(UGHRequiredMixin, RequestToFormMixin, UpdateView):
    template_name = 'view_place.html'
    context_object_name = 'place'
    model = Place
    form_class = PlaceEditForm

    def get_queryset(self):
        org = self.request.user.profile.org
        return Place.objects.filter(Q(burial__ugh=org) | Q(cemetery__ugh=org)).distinct()

    def get_success_url(self):
        messages.success(self.request, _(u"Данные обновлены"))
        return reverse('view_place', args=[self.get_object().pk])


view_place = PlaceView.as_view()

class AddDoverView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        f = AddDoverForm(data=request.POST, prefix='dover')
        try:
            agent = Profile.objects.get(pk=request.GET['agent'], is_agent=True)
        except Profile.DoesNotExist:
            return HttpResponse(_(u'Агент не существует'), mimetype='text/plain')
        except KeyError:
            return HttpResponse(_(u'Ошибка'), mimetype='text/plain')
        if f.is_valid():
            dover = f.save(commit=False)
            dover.target_org = request.user.profile.org
            dover.agent = agent
            dover.save()
            return HttpResponse(json.dumps({'pk': dover.pk, 'label': u'%s' % dover}), mimetype='application/json')
        else:
            err_str = _(u'Ошибка:\n%s')
            errors = '\n'.join([u'%s' % v[0] for k,v in f.errors.items() if k == '__all__'])
            if "\n" in errors:
                err_str = _(u'Ошибки:\n%s')
            return HttpResponse(err_str % errors, mimetype='text/plain')

add_dover = AddDoverView.as_view()

class AddAgentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        fa = AddAgentForm(data=request.POST, prefix='agent')
        fd = AddDoverForm(data=request.POST, prefix='agent_dover')
        try:
            org = Org.objects.get(pk=request.GET['org'])
        except KeyError:
            return HttpResponse(_(u'Ошибка'), mimetype='text/plain')
        except Org.DoesNotExist:
            return HttpResponse(_(u'Нет такой организации'), mimetype='text/plain')
        if fa.is_valid() and fd.is_valid():
            agent = fa.save(org=org)
            dover = fd.save(commit=False)
            dover.target_org = request.user.profile.org
            dover.agent = agent
            dover.save()
            return HttpResponse(json.dumps({
                'pk': agent.pk, 'label': u'%s' % agent,
                'dover_pk': dover.pk, 'dover_label': u'%s' % dover
            }), mimetype='application/json')
        else:
            err_str = _(u'Ошибка:\n%s')
            errors = '\n'.join([u'%s' % v[0] for k,v in fa.errors.items()] + \
                               [u'%s' % v[0] for k,v in fd.errors.items()])
            if "\n" in errors:
                err_str = _(u'Ошибки:\n%s')
            return HttpResponse(err_str % errors, mimetype='text/plain')

add_agent = AddAgentView.as_view()

class AddOrgView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if kwargs.get('type'):
            prefix = kwargs['type']
            instance = Org(type=kwargs['type'])
        else:
            prefix='org'
            instance = None
        f = AddOrgForm(request=self.request, data=request.POST, prefix=prefix, instance=instance)
        if f.is_valid():
            new_org = f.save()
            f.put_log_data(msg=_(u'Данные сохранены'))
            if request.user.profile.is_ugh() and new_org.type == Org.PROFILE_LORU:
                new_org.ugh_list.create(ugh=request.user.profile.org)
            return HttpResponse(json.dumps({'pk': new_org.pk, 'label': u'%s' % new_org}), mimetype='application/json')
        else:
            err_str = _(u'Ошибка:\n%s')
            errors = '\n'.join([u'%s' % v[0] for k,v in f.errors.items()])
            if "\n" in errors:
                err_str = _(u'Ошибки:\n%s')
            return HttpResponse(err_str % errors, mimetype='text/plain')

add_org = AddOrgView.as_view()

class AddDocTypeView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        f = AddDocTypeForm(data=request.POST, prefix='doctype')
        if f.is_valid():
            dt = f.save()
            return HttpResponse(json.dumps({'pk': dt.pk, 'label': u'%s' % dt}), mimetype='application/json')
        else:
            err_str = _(u'Ошибка:\n%s')
            errors = '\n'.join([u'%s' % v[0] for k,v in f.errors.items()])
            if "\n" in errors:
                err_str = _(u'Ошибки:\n%s')
            return HttpResponse(err_str % errors, mimetype='text/plain')

add_doctype = AddDocTypeView.as_view()

class GetPlaceView(View):
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated():
            return redirect('/')
        return View.dispatch(self, request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        places = Place.objects.all()
        data = dict(
            cemetery__pk=request.GET.get('cemetery') or None,
            area__pk=request.GET.get('area') or None,
            row=request.GET.get('row') or '',
            place=request.GET.get('place_number') or '',
        )

        if request.GET.get('place_number'):
            try:
                p = places.get(**data)
            except Place.DoesNotExist:
                return HttpResponse('')
            except Place.MultipleObjectsReturned:
                return HttpResponse('')
            else:
                return render(request, 'create_burial_place_info.html', {'place': p})
        else:
            return HttpResponse('')

get_place = GetPlaceView.as_view()

class GetGravesNumberView(View):
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated():
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
                return HttpResponse('{"place_pk": %s, "graves_count": %s}' % (p.pk, p.get_graves_count()), mimetype='application/json')

        return HttpResponse('{"graves_count": %s}' % desired_graves_count, mimetype='application/json')

get_graves_number = GetGravesNumberView.as_view()

class CommentView(BurialsListGenericMixin, LoginRequiredMixin, DetailView):
    def get_queryset(self):
        return Burial.objects.filter(self.get_qs_filter()).distinct()

    def get(self, request, *args, **kwargs):
        return redirect('view_burial', self.get_object().pk)

    def post(self, request, *args, **kwargs):
        comment = request.POST.get('comment').strip()
        if comment:
            write_log(request, self.get_object(), _(u'Комментарий: %s') % comment)
        return redirect('view_burial', self.get_object().pk)

burial_comment = CommentView.as_view()

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
        return HttpResponse(json.dumps([{'value': c.name} for c in cemeteries[:20]]), mimetype='text/javascript')

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
        return HttpResponse(json.dumps([{'value': c.name} for c in areas[:20]]), mimetype='text/javascript')

autocomplete_areas = AutocompleteAreas.as_view()

class DeleteBurialfile(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        burial_file = get_object_or_404(BurialFiles, pk=self.kwargs['pk'])
        if not burial_file.burial.is_editable(request.user):
            raise Http404
        burial_file.delete()
        return redirect('edit_burial', burial_file.burial.pk)

delete_burialfile = DeleteBurialfile.as_view()

class BurialfileCommentEdit(LoginRequiredMixin, UpdateView):
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
