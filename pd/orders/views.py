# coding=utf-8

import datetime
import decimal
import json

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.aggregates import Count, Sum
from django.db.models.query_utils import Q
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.shortcuts import get_object_or_404

from LatLon import LatLon, Latitude, Longitude

from logs.models import write_log
from geo.models import Location
from burials.forms import AddOrgForm, AddAgentForm, AddDoverForm, AddDocTypeForm
from burials.models import Burial, Place, Grave, PlacePhoto
from users.models import CustomerProfile, CustomerProfilePhoto, Org, ProfileLORU, Store, is_loru_user, is_supervisor, \
                         PermitIfLoru, PermitIfCabinet, is_cabinet_user
from billing.models import Rate
from orders.forms import ProductForm, OrderForm, OrderItemFormset, CoffinForm, CatafalqueForm, \
                         AddInfoForm, OrderSearchForm, OrderBurialForm
from orders.models import Product, Order, OrderItem, ProductCategory, Iorder, IorderItem, \
                          Service, Measure, OrgService, OrgServicePrice, ServiceItem, OrderComment, \
                          Route
from persons.models import CustomPlace, AlivePerson
from pd.forms import CommentForm
from pd.views import PaginateListView, RequestToFormMixin, ServiceException, get_front_end_url, get_host_url
from reports.models import make_report

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from orders.serializers import ProductCategorySerializer, ProductsSerializer, ProductsOptSerializer, \
                               ProductInfoSerializer, IordersSerializer, IorderInfoSerializer, \
                               ProductEditSerializer, ServiceSerializer, OrgServiceSerializer

from pd.utils import EmailMessage
from pd.models import validate_phone_as_number

from sms_service.utils import send_sms

class ProductCategoryQsMixin(object):
    
    def product_category_qs(self):
        category_ids_got = self.request.GET.getlist('filter[category]')
        category_ids = []
        for category_id in category_ids_got:
            try:
                # может быть '', 'null'
                category_ids.append(int(category_id))
            except ValueError:
                pass
        if category_ids:
            return Q(productcategory__pk__in=category_ids)
        else:
            return Q()

class LORURequiredMixin:
    def is_loru(self, request):
        if not request.user.is_authenticated():
            return False
        if not getattr(self.request.user, 'profile', None):
            return False
        if not self.request.user.profile.is_loru():
            return False
        return True

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return self.is_loru(request) and View.dispatch(self, request, *args, **kwargs) or redirect('/')

class ProductList(LORURequiredMixin, ListView):
    template_name = 'product_list.html'
    model = Product

    def get_queryset(self):
        return Product.objects.filter(loru=self.request.user.profile.org)
    
manage_products = ProductList.as_view()

class ProductCreate(LORURequiredMixin, RequestToFormMixin, CreateView):
    template_name = 'product_edit.html'
    form_class = ProductForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.loru = self.request.user.profile.org
        self.object.save()
        if not self.object.sku or not self.object.sku.strip():
            self.object.sku = str(self.object.pk)
            self.object.save()
        write_log(self.request, self.object, _(u'Создание: %s') % self.object.name)
        msg = _(u"<a href='%s'>Товар %s</a> создан") % (
            reverse('manage_products_edit', args=[self.object.pk]),
            self.object.name,
        )
        messages.success(self.request, msg)
        return redirect('manage_products')

manage_products_create = ProductCreate.as_view()

class ProductEdit(LORURequiredMixin, RequestToFormMixin, UpdateView):
    template_name = 'product_edit.html'
    form_class = ProductForm

    def get_queryset(self):
        return Product.objects.filter(loru=self.request.user.profile.org)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if not self.object.sku or not self.object.sku.strip():
            self.object.sku = str(self.object.pk)
        self.object.save()
        write_log(self.request, self.object, _(u'Изменение: %s') % self.object.name)
        msg = _(u"<a href='%s'>Товар %s</a> изменен") % (
            reverse('manage_products_edit', args=[self.object.pk]),
            self.object.name,
        )
        messages.success(self.request, msg)
        return redirect('manage_products')

manage_products_edit = ProductEdit.as_view()

class OrderList(LORURequiredMixin, PaginateListView):
    template_name = 'order_list.html'
    model = Order

    def __init__(self, *args, **kwargs):
        super(OrderList, self).__init__(*args, **kwargs)
        self.SORT_DEFAULT = '-order_date'
        
    def get_queryset(self):
        if not self.request.GET:
            return Order.objects.none()

        return self.filtered_orders()

    def filtered_orders(self):
        orders = Order.objects.filter(loru=self.request.user.profile.org, customplace__isnull=True) 
                # .annotate(item_count=Count('orderitem'))  # мы не показываем в таблице кол-во товаров,
                                                            # к тому же это резко замедляет поиск

        form = self.get_form()
        if form.data and form.is_valid():
            if form.cleaned_data['fio']:
                search_by =  ['burial__deadman__last_name__istartswith', 'burial__deadman__first_name__istartswith', 'burial__deadman__middle_name__istartswith']
                orders = self.filter_by_name(queryset=orders, search_by=search_by, name_string=form.cleaned_data['fio'])
            if form.cleaned_data['birth_date_from']:
                orders = orders.filter(burial__deadman__birth_date__gte=form.cleaned_data['birth_date_from'])
            if form.cleaned_data['birth_date_to']:
                orders = orders.filter(burial__deadman__birth_date__lte=form.cleaned_data['birth_date_to'])
            if form.cleaned_data['death_date_from']:
                orders = orders.filter(burial__deadman__death_date__gte=form.cleaned_data['death_date_from'])
            if form.cleaned_data['death_date_to']:
                orders = orders.filter(burial__deadman__death_date__lte=form.cleaned_data['death_date_to'])
            if form.cleaned_data['burial_date_from']:
                orders = orders.filter(burial__plan_date__gte=form.cleaned_data['burial_date_from'])
            if form.cleaned_data['burial_date_to']:
                orders = orders.filter(burial__plan_date__lte=form.cleaned_data['burial_date_to'])
            if form.cleaned_data['account_number_from']:
                orders = orders.filter(loru_number__gte=form.cleaned_data['account_number_from'])
            if form.cleaned_data['account_number_to']:
                orders = orders.filter(loru_number__lte=form.cleaned_data['account_number_to'])
            if form.cleaned_data['responsible']:
                fio = [f.strip('.') for f in form.cleaned_data['responsible'].split(' ')]
                q1r = Q(burial__responsible__isnull=False)
                q2r = Q(burial__place__isnull=False)
                if len(fio) > 2:
                    q1r &= Q(burial__responsible__middle_name__istartswith=fio[2])
                    q2r &= Q(burial__place__responsible__middle_name__istartswith=fio[2])
                if len(fio) > 1:
                    q1r &= Q(burial__responsible__first_name__istartswith=fio[1])
                    q2r &= Q(burial__place__responsible__first_name__istartswith=fio[1])
                if len(fio) > 0:
                    q1r &= Q(burial__responsible__last_name__istartswith=fio[0])
                    q2r &= Q(burial__place__responsible__last_name__istartswith=fio[0])
                qr = Q(q1r | q2r)
                orders = orders.filter(qr)
            if form.cleaned_data['cemetery']:
                orders = orders.filter(burial__cemetery__name=form.cleaned_data['cemetery'])
            if form.cleaned_data['area']:
                orders = orders.filter(burial__area__name=form.cleaned_data['area'])
            if form.cleaned_data['row']:
                orders = orders.filter(burial__row=form.cleaned_data['row'])
            if form.cleaned_data['place']:
                orders = orders.filter(burial__place_number=form.cleaned_data['place'])
            if form.cleaned_data['no_last_name']:
                orders = orders.filter(Q(burial__deadman__last_name='') | Q(burial__deadman__last_name__isnull=True))
            if form.cleaned_data['no_responsible']:
                orders = orders.filter(burial__place__responsible__isnull=True)
            if form.cleaned_data['status']:
                orders = orders.filter(burial__status=form.cleaned_data['status'])
            if form.cleaned_data['order_num_from']:
                orders = orders.filter(loru_number__gte=form.cleaned_data['order_num_from'])
            if form.cleaned_data['order_num_to']:
                orders = orders.filter(loru_number__lte=form.cleaned_data['order_num_to'])
            if form.cleaned_data['order_cost_from']:
                orders = orders.filter(cost__gte=form.cleaned_data['order_cost_from'])
            if form.cleaned_data['order_cost_to']:
                orders = orders.filter(cost__lte=form.cleaned_data['order_cost_to'])
            if form.cleaned_data['annulated']:
                orders = orders.filter(annulated=True)
            else:
                orders = orders.filter(annulated=False)
            if form.cleaned_data['burial_num_from']:
                orders = orders.filter(burial__id__gte = form.cleaned_data['burial_num_from'])
            if form.cleaned_data['burial_num_to']:
                orders = orders.filter(burial__id__lte = form.cleaned_data['burial_num_to'])
            if form.cleaned_data['applicant_org']:
                orders = orders.filter(applicant_organization__name__istartswith=form.cleaned_data['applicant_org'])
            if form.cleaned_data['applicant_person']:
                search_by =  ['applicant__last_name__istartswith','applicant__first_name__istartswith','applicant__middle_name__istartswith']
                orders = self.filter_by_name(queryset=orders, search_by=search_by, name_string=form.cleaned_data['applicant_person'])
            if form.cleaned_data['reg_number_from']:
                orders = orders.filter(burial__account_number__gte = form.cleaned_data['reg_number_from'])
            if form.cleaned_data['reg_number_to']:
                orders = orders.filter(burial__account_number__lte= form.cleaned_data['reg_number_to'])
            if form.cleaned_data['burial_container']:
                orders = orders.filter(burial__burial_container=form.cleaned_data['burial_container'])
        else:
            orders = orders.exclude(annulated=True)

        orders_count = orders.count()
        orders = orders.select_related(
            'burial', 'burial__ugh', 'burial__cemetery', 'burial__area', 'burial__responsible',
            'burial__changed_by', 'burial__deadman', 'applicant_organization', 'applicant',
        )

        sort = self.request.GET.get('sort', self.SORT_DEFAULT)
        SORT_FIELDS = {
            'order_date': 'dt',
            '-order_date': '-dt',
            'account_number': 'burial__account_number',
            '-account_number': '-burial__account_number',
            'deadman': 'burial__deadman__last_name',
            '-deadman': '-burial__deadman__last_name',
            'plan_date': 'burial__plan_date',
            '-plan_date': '-burial__plan_date',
            'place': 'burial__place',
            '-place': '-burial__place',
            'cemetery': 'burial__cemetery',
            '-cemetery': '-burial__cemetery',
            'burial': 'burial__pk',
            '-burial': '-burial__pk',
            'applicant': ['applicant', 'applicant_organization'],
            '-applicant': ['-applicant', '-applicant_organization'],
            'order_num': 'loru_number',
            '-order_num': '-loru_number',
            'cost': 'cost',
            '-cost': '-cost',
        }
        s = SORT_FIELDS[sort]
        if not isinstance(s, list):
            s = [s]
        orders = orders.order_by(*s)

        orders.count = lambda: orders_count
        return orders

    def get_form(self):
        return OrderSearchForm(data=self.request.GET or None)

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        paginator = super(OrderList, self).get_paginator(queryset, per_page, orphans, allow_empty_first_page)
        paginator._count = queryset.count()
        return paginator

    def filter_by_name(self, queryset, search_by, name_string):
        import operator
        values = [f.strip('.') for f in name_string.split(' ')]
        predicates = zip(search_by, values)
        query = [Q(p) for p in predicates]
        q = reduce(operator.and_, query)
        return queryset.filter(q)

order_list = OrderList.as_view()

class OrderCreate(LORURequiredMixin, RequestToFormMixin, CreateView):
    template_name = 'order_create.html'
    form_class = OrderForm

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.burial = None
        if self.is_loru(request):
            burial_pk = self.request.REQUEST.get('burial')
            if burial_pk:
                try:
                    self.burial = Burial.objects.get(pk=burial_pk)
                    if not self.burial.can_bind_to_order(self.request.user.profile.org):
                        raise Http404
                except Burial.DoesNotExist:
                    raise Http404
            return View.dispatch(self, request, *args, **kwargs)
        else:
            raise Http404
        
    def get_context_data(self, **kwargs):
        data = super(OrderCreate, self).get_context_data(**kwargs)
        data.update({
            'agent_form': AddAgentForm(prefix='agent'),
            'agent_dover_form': AddDoverForm(prefix='agent_dover'),
            'dover_form': AddDoverForm(prefix='dover'),
            'org_form': AddOrgForm(request=self.request, prefix='org'),
            'doc_type_form': AddDocTypeForm(prefix='doctype'),
        })
        return data

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.loru = self.request.user.profile.org
        if self.burial:
            self.object.burial = self.burial
        self.object.save()

        for p in Product.objects.filter(loru=self.request.user.profile.org, default=True):
            OrderItem.objects.create(order=self.object, product=p)

        write_log(self.request, self.object, _(u'Заказ сохранен'))
        msg = _(u"<a href='%s'>Заказ %s</a> сохранен") % (
            reverse('order_edit', args=[self.object.pk]),
            self.object.pk,
        )
        messages.success(self.request, msg)
        return redirect('order_products', self.object.pk)

order_create = OrderCreate.as_view()

class OrderEdit(LORURequiredMixin, RequestToFormMixin, UpdateView):
    template_name = 'order_edit_applicant.html'
    form_class = OrderForm

    def get_context_data(self, **kwargs):
        data = super(OrderEdit, self).get_context_data(**kwargs)
        data.update({
            'order': self.get_object(),
            'agent_form': AddAgentForm(prefix='agent'),
            'agent_dover_form': AddDoverForm(prefix='agent_dover'),
            'dover_form': AddDoverForm(prefix='dover'),
            'org_form': AddOrgForm(request=self.request, prefix='org'),
        })
        return data

    def get(self, request, *args, **kwargs):
        self.request = request
        if self.request.session.get('order_burial_saved'):
            del self.request.session['order_burial_saved']
            if self.get_object().has_services:
                return redirect('order_services', self.get_object().pk)
        return super(OrderEdit, self).get(request, *args, **kwargs)

    def get_queryset(self):
        return Order.objects.filter(loru=self.request.user.profile.org)

    def form_valid(self, form):
        self.object = form.save()

        write_log(self.request, self.object, _(u'Заказ сохранен'))
        msg = _(u"<a href='%s'>Заказ %s</a> сохранен") % (
            reverse('order_edit', args=[self.object.pk]),
            self.object.pk,
        )
        messages.success(self.request, msg)
        return redirect('.')

order_edit = OrderEdit.as_view()

class AjaxProductPrice(LORURequiredMixin, View):
    def get(self, request, *args, **kwargs):
        id = request.GET.get('id')
        if id:
            product = get_object_or_404(Product, pk=id)
            price = product.price
        else:
            price = 0
        return HttpResponse(json.dumps({'price': float(price)}), mimetype='application/json')

ajax_product_price = AjaxProductPrice.as_view()

class OrderEditProducts(LORURequiredMixin, View):
    template_name = 'order_edit_products.html'

    def get_queryset(self):
        return Order.objects.filter(loru=self.request.user.profile.org)

    def get_formset(self):
        return OrderItemFormset(request=self.request, data=self.request.POST or None, instance=self.get_object())

    def get_object(self):
        return self.get_queryset().get(pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        return {
            'order': self.get_object(),
            'formset': self.get_formset(),
        }

    def post(self, request, *args, **kwargs):
        self.request = request
            
        formset = self.get_formset()
        if formset.is_valid():
            self.object = self.get_object()
            for orderitem in self.object.orderitem_set.all():
                orderitem.delete()
            
            formset.save()


            write_log(self.request, self.object, _(u'Заказ сохранен'))
            msg = _(u"<a href='%s'>Заказ %s</a> сохранен") % (
                reverse('order_edit', args=[self.object.pk]),
                self.object.pk,
            )
            messages.success(self.request, msg)
            return redirect('.')
        else:
            messages.error(self.request, _(u"Обнаружены ошибки"))
            return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.request = request
        return render(request, self.template_name, self.get_context_data())

order_products = OrderEditProducts.as_view()

class OrderInfo(LORURequiredMixin, DetailView):
    template_name = 'order_info.html'

    def get_queryset(self):
        return Order.objects.filter(loru=self.request.user.profile.org)

    def get_context_data(self, **kwargs):
        data = super(OrderInfo, self).get_context_data(**kwargs)
        data.update({
            'comment_form': CommentForm(),
        })
        return data

order_info = OrderInfo.as_view()

class OrderEditServices(OrderEditProducts):
    template_name = 'order_edit_service.html'

    def get_catafalque_form(self):
        return CatafalqueForm(data=self.request.POST or None, instance=self.get_object().get_catafalquedata())

    def get_add_info_form(self):
        return AddInfoForm(data=self.request.POST or None, instance=self.get_object().get_addinfodata())

    def get_coffin_form(self):
        return CoffinForm(data=self.request.POST or None, instance=self.get_object().get_coffindata())

    def get_context_data(self, **kwargs):
        data = {'order': self.get_object()}
        if self.get_object().has_catafalque():
            data.update({'catafalque_form': self.get_catafalque_form()})
        if self.get_object().has_catafalque() or self.get_object().has_coffin():
            data.update({'add_info_form': self.get_add_info_form()})
        if self.get_object().has_coffin():
            data.update({'coffin_form': self.get_coffin_form()})
        return data

    def post(self, request, *args, **kwargs):
        self.request = request
        self.catafalque_form = self.get_catafalque_form()
        self.add_info_form = self.get_add_info_form()
        self.coffin_form = self.get_coffin_form()
        catafalque_ok = not self.get_object().has_catafalque() or self.catafalque_form.is_valid()
        add_info_ok = not (self.get_object().has_coffin() or self.get_object().has_catafalque()) or self.add_info_form.is_valid()
        coffin_ok = not self.get_object().has_coffin() or self.coffin_form.is_valid()
        if catafalque_ok and add_info_ok and coffin_ok:
            self.object = self.get_object()

            if self.catafalque_form.is_valid():
                cat = self.catafalque_form.save(commit=False)
                cat.order = self.object
                cat.save()

            if self.add_info_form.is_valid():
                add_info = self.add_info_form.save(commit=False)
                add_info.order = self.object
                add_info.save()

            if self.coffin_form.is_valid():
                coffin = self.coffin_form.save(commit=False)
                coffin.order = self.object
                coffin.save()

            write_log(self.request, self.object, _(u'Заказ сохранен'))
            msg = _(u"<a href='%s'>Заказ %s</a> сохранен") % (
                reverse('order_edit', args=[self.object.pk]),
                self.object.pk,
            )
            messages.success(self.request, msg)
            return redirect('.')
        else:
            messages.error(self.request, _(u"Обнаружены ошибки"))
            return self.get(request, *args, **kwargs)

order_services = OrderEditServices.as_view()

class PrintOrderView(LORURequiredMixin, DetailView):
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(loru=self.request.user.profile.org).distinct()

    def render_to_response(self, context, **response_kwargs):
        context['now'] = datetime.datetime.now()
        report = make_report(
            user=self.request.user,
            msg=_(u"Счет-заказ"),
            obj=self.get_object(),
            template='reports/order.html',
            context=RequestContext(self.request, context),
        )
        return redirect('report_view', report.pk)

order_print = PrintOrderView.as_view()

class PrintContractView(LORURequiredMixin, DetailView):
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(loru=self.request.user.profile.org).distinct()

    def render_to_response(self, context, **response_kwargs):
        context['now'] = datetime.datetime.now()
        report = make_report(
            user=self.request.user,
            msg=_(u"Договор"),
            obj=self.get_object(),
            template='reports/contract.html',
            context=RequestContext(self.request, context),
        )
        return redirect('report_view', report.pk)

order_contract = PrintContractView.as_view()

class CommentView(LORURequiredMixin, DetailView):
    def get_queryset(self):
        return Order.objects.filter(loru=self.request.user.profile.org).distinct()

    def post(self, request, *args, **kwargs):
        write_log(request, self.get_object(), _(u'Комментарий: %s') % request.POST.get('comment'))
        return redirect('order_edit', self.get_object().pk)

order_comment = CommentView.as_view()

class AnnulateOrder(LORURequiredMixin, DetailView):
    def get_queryset(self):
        return Order.objects.filter(loru=self.request.user.profile.org).distinct()

    def post(self, request, *args, **kwargs):
        o = self.get_object()
        if request.GET.get('recover'):
            o.recover()
            messages.success(self.request, _(u'Заказ восстановлен'))
            write_log(request, o, _(u'Заказ восстановлен'))
        else:
            b = o.burial
            old_annulated = b.annulated if b else None
            o.annulate()
            messages.success(self.request, _(u'Заказ аннулирован'))
            write_log(request, o, _(u'Заказ аннулирован'))
            if b and b.annulated and not old_annulated:
                write_log(request, b, _(u'Захоронение аннулировано'))
        return redirect('order_edit', o.pk)

order_annulate = AnnulateOrder.as_view()

class OrderBurialView(LORURequiredMixin, RequestToFormMixin, UpdateView):
    """
    Cоздание или привязка захоронения к заказу
    """
    template_name = 'order_burial.html'
    form_class = OrderBurialForm

    def get_queryset(self):
        return Order.objects.filter(loru=self.request.user.profile.org)

    def get(self, request, *args, **kwargs):
        order = self.get_object()
        burial = order.burial
        if burial:
            if burial.is_edit() and not burial.annulated:
                return redirect(reverse('edit_burial', args=[burial.pk]) + '?order=%s' % order.pk)
            else:
                return redirect(reverse('view_burial', args=[burial.pk]) + '?order=%s' % order.pk)
        return super(OrderBurialView, self).get(request, *args, **kwargs)
        
    def form_valid(self, form):
        if self.object.burial:
            # - форма привязала к этому заказу захоронение
            write_log(self.request, self.object.burial, _(u'Захоронение прикреплено к заказу %s') % self.object.pk)
            write_log(self.request, self.object, _(u'Заказ: прикреплено захоронение %s') % self.object.burial.pk)
            msg = _(u"<a href='%s'>Заказ %s</a>: прикреплено захоронение") % (
                reverse('order_edit', args=[self.object.pk]),
                self.object.pk,
            )
            messages.success(self.request, msg)
            return redirect('.')
        # - форма отдала "Создать новое захоронение"
        return redirect(reverse('create_burial') + '?order=%s' % self.object.pk)

order_burial = OrderBurialView.as_view()


class ProductCategoryViewSet(viewsets.ModelViewSet):
    model = ProductCategory
    serializer_class = ProductCategorySerializer

    def get_queryset(self):
        loru_ids = self.request.GET.getlist('filter[supplier]')
        while loru_ids.count(u''):
            loru_ids.remove(u'')
        if loru_ids:
            qs = Q(product__loru__pk__in=loru_ids)
        else:
            qs = Q()
        onlyOpt = self.request.GET.get('filter[onlyOpt]')
        if onlyOpt and onlyOpt == 'true':
            qs &= Q(product__is_wholesale=True)
        return ProductCategory.objects.filter(qs).order_by('name').distinct()

class ProductsViewSet(ProductCategoryQsMixin, viewsets.ReadOnlyModelViewSet):
    """
    Показ продуктов в публичном каталоге только!!!
    """
    model = Product
    serializer_class = ProductsSerializer
    paginate_by = None

    def get_queryset(self):
        store_ids = self.request.GET.getlist('filter[supplierStore]')
        while store_ids.count(u''):
            store_ids.remove(u'')
        if store_ids:
            qs = Q(loru__store__pk__in=store_ids)
        else:
            return Product.objects.none()

        loru_ids = self.request.GET.getlist('filter[supplier]')
        while loru_ids.count(u''):
            loru_ids.remove(u'')
        if loru_ids:
            qs &= Q(loru__pk__in=loru_ids)

        if self.request.GET.get('filter[price_from]'):
            qs &= Q(price__gte=self.request.GET.get('filter[price_from]'))
        if self.request.GET.get('filter[price_to]'):
            qs &= Q(price__lte=self.request.GET.get('filter[price_to]'))

        qs &= self.product_category_qs()

        q_public_whole = Q(is_public_catalog=True)
        if self.request.GET.get('filter[productType]', '').lower() == 'opt':
            q_public_whole = Q(is_wholesale=True)
        qs &= q_public_whole

        ordered = None
        orders = {'price': 'price', 'date': 'dt_created', }
        directions = {'asc': '', 'desc': '-', }
        for order in orders:
            direction = self.request.GET.get('order[%s]' % order)
            if direction and direction in directions:
                ordered = directions[direction] + orders[order]
                break
        
        filter = Product.objects.filter(qs)
        if ordered:
            filter = filter.order_by(ordered)
        filter = filter.distinct()

        offset = self.request.GET.get('offset') and int(self.request.GET.get('offset'))
        limit = self.request.GET.get('limit') and int(self.request.GET.get('limit'))

        if offset and limit:
            filter = filter[offset:offset+limit]
        elif offset:
            filter = filter[offset:]
        elif limit:
            filter = filter[:limit]
        
        return filter

class ProductsOptViewSet(ProductCategoryQsMixin, viewsets.ReadOnlyModelViewSet):
    """
    Показ продуктов оптовика-поставщика

    api/optplaces/suppliers/(?P<loru_pk>\d+)/products
    """
    model = Product
    paginate_by = None

    def get_queryset(self, *args, **kwargs):
        qs = Q(
            loru__pk=self.kwargs['loru_pk'],
            is_wholesale=True,
        )
        qs &= self.product_category_qs()
        return Product.objects.filter(qs)

    def get_serializer(self, *args, **kwargs):
        try:
            is_wholesale_with_vat = Org.objects.get(pk=self.kwargs['loru_pk']).is_wholesale_with_vat
        except Org.DoesNotExist:
            is_wholesale_with_vat = False
        return ProductsOptSerializer(
            self.get_queryset(),
            context = dict(
                request=self.request,
                view=self,
                is_wholesale_with_vat=is_wholesale_with_vat,
            )
        )

class ProductInfoView(APIView):

    def get(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        show_wholesale = is_loru_user(request.user) or is_supervisor(request.user)
        return Response(
            status=200,
            data=ProductInfoSerializer(product, context=dict(
                request=request,
                show_wholesale=show_wholesale,
            )).data,
        )

api_catalog_products_detail = ProductInfoView.as_view()

class ApiProfileView(APIView):
    permission_classes = (PermitIfCabinet,)
    
    def get(self, request):
        profile = request.user.customerprofile
        data = {
            'id': request.user.pk,
        }
        try:
            photo = request.build_absolute_uri(profile.customerprofilephoto.bfile.url) \
                if profile.customerprofilephoto.bfile else None
        except CustomerProfilePhoto.DoesNotExist:
            photo = None
        data['photo'] = photo
        data['lastName'] = profile.user_last_name
        data['firstName'] = profile.user_first_name
        data['middleName'] = profile.user_middle_name
        data['loginPhone'] = request.user.customerprofile.login_phone
        data['username'] = request.user.username
        data['places'] = []
        for cp in CustomPlace.objects.filter(place__responsible__user=request.user).select_related('place'):
            place={'id': cp.pk}
            p = cp.place
            place['address'] = _(u'Кладбище %s, участок %s') % (p.cemetery.name, p.area.name, )
            if p.row:
                place['address'] += _(u', ряд %s') % p.row
            place['address'] += _(u', место %s') % p.place
            cemetery_address = p.cemetery.address and p.cemetery.address.__unicode__() or ''
            if cemetery_address:
                place['address'] += _(u', %s') % cemetery_address
            place['location'] = {
                'latitude': p.lat,
                'longitude': p.lng,
            }
            place['graves'] = []
            gallery = p.get_photo_gallery(request)
            for g in Grave.objects.filter(place=p).order_by('grave_number'):
                grave = {'graveNumber': g.grave_number}
                burials = []
                for b in g.burial_set.exclude(burial_container=Burial.CONTAINER_BIO):
                    burials.append(
                        {
                            'id': b.pk,
                            'fio': b.deadman and b.deadman.full_name_complete() or _(u"Неизвестный"),
                            'lastName': b.deadman and b.deadman.last_name,
                            'firstName': b.deadman and b.deadman.first_name,
                            'middleName': b.deadman and b.deadman.middle_name,
                            'photo': None,
                            'birthDate': b.deadman and b.deadman.birth_date and b.deadman.birth_date.str_safe() or None,
                            'deathDate': b.deadman and b.deadman.death_date and b.deadman.death_date.str_safe() or None,
                        }
                    )
                grave['burials'] = burials
                place['graves'].append(grave)
            place['gallery'] = sorted(gallery, key=lambda photo: photo['addedAt'], reverse=True)
            place['photo'] = place['gallery'][0]['photo'] if place['gallery'] else None
            data['places'].append(place)           
            
        return Response(status=200, data=data)

api_profile = ApiProfileView.as_view()

class ApiLoruProductPlaces(APIView):
    """
    Обновление статусов продуктов на площадках (ОМС)

    Пример:
    [
        {
            "id": 1,
            "places": [
            {
                "id": 5, 
                "status": "disable"
            },
            {
                "id": 8, 
                "status": "up"
            }
            ]
        },
        {
            "id": 2,
            "places": [
            {
                "id": 5, 
                "status": "enable"
            }
            ]
        }
    ]
    """
    
    permission_classes = (PermitIfLoru,)

    @transaction.commit_on_success
    def post(self, request, format=None):
        # Соответствие входных данных с константами в поле Rate.action
        rate_action = {
            'disable': Rate.RATE_ACTION_DISABLE,
            'enable': Rate.RATE_ACTION_PUBLISH,
            'up': Rate.RATE_ACTION_UPDATE,
        }
        data = []
        catalog_org_pk = Org.get_catalog_org_pk()
        for p in request.DATA:
            try:
                product = Product.objects.get(pk=p['id'], loru=request.user.profile.org)
                data_p = { 'id': p['id'], 'places': [catalog_org_pk] }
                for o in p['places']:
                    if o['id'] == catalog_org_pk:
                        try:
                            if rate_action[o['status']] == Rate.RATE_ACTION_DISABLE:
                                product.is_public_catalog = False
                            elif rate_action[o['status']] in \
                                    (Rate.RATE_ACTION_PUBLISH, Rate.RATE_ACTION_UPDATE,):
                                product.is_public_catalog = True
                            product.save()
                            write_log(
                                request,
                                product,
                                _(u"Добавлен в публичный каталог") if product.is_public_catalog else _(u"Изъят из публичного каталога"),
                            )
                            data.append(data_p)
                        except IndexError:
                            pass
            except Product.DoesNotExist:
                pass
        return Response(data=data, status=200)

api_loru_product_places = ApiLoruProductPlaces.as_view()

class UghPublishedProductsViewSet(viewsets.ViewSet):
    queryset = Product.objects.none()
    permission_classes = (PermitIfLoru,)
    
    def list(self, request):
        data=[]
        catalog_org_pk = Org.get_catalog_org_pk()
        for p in Product.objects.filter(loru=request.user.profile.org).order_by('pk'):
            data_p = {
                'id': p.pk,
                'name': p.name,
                'availableOnPlaces': [],
                'category': {
                    'id': p.productcategory.pk,
                    'name': p.productcategory.name,
                },
            }
            if p.is_public_catalog:
                data_p['availableOnPlaces'] = [catalog_org_pk,]
            data.append(data_p)
        return Response(status=200, data=data)

class IorderMixin(APIView):

    def put_item(self, iorder, product, count, comment):
        """
        Забить позицию интернет-заказа iorder продуктом product
        """
        return IorderItem.objects.create(
            iorder=iorder,
            product=product,
            quantity=decimal.Decimal(count),
            comment=comment or '',
            measure=product.measure,
            price_wholesale=product.price_wholesale,
            name=product.name,
            productcategory=product.productcategory,
            productcategory_name=product.productcategory.name,
            productgroup=product.productgroup,
            productgroup_name=product.productgroup.name if product.productgroup else '',
            productgroup_description=product.productgroup.description if product.productgroup else '',
            is_wholesale_with_vat=iorder.supplier.is_wholesale_with_vat,
        )

    def email_notifications(self, iorder, is_new_iorder):
        """
        """
        email_from = settings.DEFAULT_FROM_EMAIL
        number_verbose = iorder.number_verbose()
        if iorder.customer and iorder.customer.email:
            email_to = (iorder.customer.email, )
            email_subject = u"%s: %s %s" % (
                _(u"Похоронное Дело"),
                _(u"создан заказ") if is_new_iorder else _(u"изменен заказ"),
                number_verbose,
            )
            email_text = render_to_string(
                            'iorder_notification.txt',
                            {
                                'preambule': _(u"Создан") if is_new_iorder else _(u"Изменен"),
                                'front_end_url': get_front_end_url(self.request),
                                'iorder': iorder,
                                'to_customer': True,
                            }
            )
            EmailMessage(email_subject, email_text, email_from, email_to,).send()
        if iorder.supplier.email:
            email_to = (iorder.supplier.email, )
            email_subject = u"%s: %s %s" % (
                _(u"Похоронное Дело"),
                _(u"поступил заказ") if is_new_iorder else _(u"изменен заказ"),
                number_verbose,
            )
            email_text = render_to_string(
                            'iorder_notification.txt',
                            {
                                'preambule': _(u"Поступил") if is_new_iorder else _(u"Изменен"),
                                'front_end_url': get_front_end_url(self.request),
                                'iorder': iorder,
                                'to_customer': False,
                            }
            )
            EmailMessage(email_subject, email_text, email_from, email_to,).send()
        if not settings.DEBUG:
            # Отправка смс поставщику
            if iorder.supplier.sms_phone:
                supplier_email = u" (email: %s)" % iorder.supplier.email if iorder.supplier.email else ""
                text =  _(u"%s zakaz N %s summa %s") % (
                    get_front_end_url(self.request).rstrip('/'),
                    number_verbose,
                    iorder.total_float(),
                )
                if is_new_iorder:
                    email_error_text = u"Поставщик %s%s не получил СМС- уведомление о новом заказе" % \
                                        (iorder.supplier.name, supplier_email,)
                else:
                    email_error_text = _(u"Поставщик %s%s не получил СМС- уведомление об изменении заказа %s") % \
                                        (iorder.supplier.name, supplier_email, number_verbose, )
                send_sms(
                    phone_number=iorder.supplier.sms_phone,
                    text=text,
                    email_error_text=email_error_text,
                )
            elif iorder.supplier.email:
                EmailMessage(
                    subject=_(u'Похоронное Дело: телефон смс- уведомений'),
                    body=_(
                        u'Невозможно доставить СМС %s заказе № %s.\n'
                        u'\n'
                        u'В свойствах вашей организации: %s\n'
                        u'не указан телефон для СМС- уведомлений.\n'
                        u'\n'
                        u'Это можно исправить: %s\n'
                    ) % (
                        _(u'о новом') if is_new_iorder else _(u'об измененном'),
                        number_verbose,
                        iorder.supplier.name,
                        get_host_url(self.request) + reverse('edit_org', args=(iorder.supplier.pk,)).lstrip('/'),
                    ),
                    from_email=email_from,
                    to=(iorder.supplier.email,),
                ).send(fail_silently=True)

class ApiOptPlacesOrders(IorderMixin, APIView):
    """
    Интернет-заказ товаров

    Пример входных данных:
    {
        "products": [
            {
            "id": 62,
            "count": 2
            },
            {
            "id": 57,
            "count": 1
            }
        ],
        "comment": "Текст комментария",
        "customer": {
            "id": 2,
            # или, если заказал по телефону
            "title": "Директор Рога и Копыта",
            "phoneNumber": "375291234567",
            "address": "Одесса Малая Арнаутская"
        }
    }
    Заказывает покупатель у поставщика.
    Покупатель может быть указан в customer, или если не указан, то это выполнивший
    логин.
    Поставщик - в id продуктов. Эти id проверяются на то, чтоб им соответствовали
    продукты, и чтоб они относились к одному поставщику. Если проверка не пройдет,
    то возвращается status=400, message=”что произошло”. Если проверка успешна,
    то формируется новый заказ, статус код - 200 
    """
    permission_classes = (PermitIfLoru,)

    @transaction.commit_on_success
    def post(self, request):
        status_code=200
        data = dict(status='success')
        year = datetime.datetime.now().year
        try:
            customer= title = phones = address = None
            customer_input = request.DATA.get("customer")
            if customer_input:
                if customer_input.get('id'):
                    try:
                        customer = Org.objects.get(pk=customer_input['id'])
                    except Org.DoesNotExist:
                        raise ServiceException(
                            _(u"Покупатель с сustomer['id']==%s отсутствует") % customer_input['id']
                        )
                elif set(('title', 'phoneNumber', 'address',)).intersection(customer_input.keys()):
                    title = customer_input.get('title', '')
                    phones = customer_input.get('phoneNumber')
                    addr_str = customer_input.get('address')
                    if addr_str:
                        address = Location.objects.create(addr_str=addr_str)
                else:
                    raise ServiceException(_(u'Невозможно определить покупателя'))
            else:
                customer = request.user.profile.org
            supplier = None
            products = request.DATA.get("products",[])
            comment = request.DATA.get("comment",'')
            for p in products:
                try:
                    product = Product.objects.get(pk=p['id'])
                    if supplier is None:
                        supplier = product.loru
                        try:
                            number = Iorder.objects.filter(
                                supplier=supplier,
                                customer=customer,
                                dt_created__year=year,
                            ).order_by('-number')[0].number
                        except IndexError:
                            number = 0
                        iorder = Iorder.objects.create(
                            supplier=supplier,
                            customer=customer,
                            status=Iorder.STATUS_POSTED,
                            number=number+1,
                            comment=comment,
                            title=title or '',
                            phones=phones,
                            address=address,
                        )
                    else:
                        if product.loru != supplier:
                            raise ServiceException(_(u'В списке товаров таковые от разных поставщиков'))
                    self.put_item(iorder, product, p['count'], p.get('comment'))
                    data['id'] = iorder.pk
                except Product.DoesNotExist:
                    raise ServiceException(_(u'Не найден товар/услуга Id=%s') % p['id'])
        except ServiceException as excpt:
            transaction.rollback()
            status_code=400
            data['status'] = 'error'
            data['message'] = excpt.message
        else:
            self.email_notifications(iorder, is_new_iorder=True)
        return Response(data=data, status=status_code)

    def get(self, request):
        org = request.user.profile.org
        qs = Q(customer=org) | Q(supplier=org)
        iorders = Iorder.objects.filter(qs).order_by('-dt_created').distinct()
        return Response(
            status=200,
            data=IordersSerializer(iorders, context=dict(
                request=request,
            )).data,
        )

api_optplaces_orders = ApiOptPlacesOrders.as_view()

class IorderInfoView(IorderMixin, APIView):
    permission_classes = (PermitIfLoru,)

    def instance_permitted(self, request, pk):
        """
        Просматривать и править заказ может лишь поставщик или покупатель, если имеется
        """
        iorder = get_object_or_404(Iorder, pk=pk)
        org = request.user.profile.org
        if iorder.supplier == org or iorder.customer and iorder.customer == org:
            return iorder, None
        else:
            return None, Response(
                status=403,
                data={"detail": "Not authorized: you are not customer nor supplier"},
            )

    def get(self, request, pk):
        iorder, response = self.instance_permitted(request, pk)
        if response:
            return response
        return Response(
            status=200,
            data=IorderInfoSerializer(iorder, context=dict(
                request=request,
            )).data,
        )

    @transaction.commit_on_success
    def put(self, request, pk):
        iorder, response = self.instance_permitted(request, pk)
        if response:
            return response
        status_code=200
        data = dict(status='success')
        products = request.DATA.get("products")
        if products is None:
            raise ServiceException(_(u'Не задан список товаров, пусть даже пустой'))
        try:
            IorderItem.objects.filter(iorder=iorder).delete()
            for p in products:
                try:
                    product = Product.objects.get(pk=p['id'])
                    if product.loru != iorder.supplier:
                        raise ServiceException(_(u'Товара Id=%s нет среди товаров поставщика заказа') % p['id'])
                    if p.get('count'):
                        self.put_item(iorder, product, p['count'], p.get('comment'))
                except Product.DoesNotExist:
                    raise ServiceException(_(u'Не найден товар/услуга Id=%s') % p['id'])
            comment = request.DATA.get("comment")
            if comment is not None:
                iorder.comment = comment
            iorder.save()
        except ServiceException as excpt:
            transaction.rollback()
            status_code=400
            data['status'] = 'error'
            data['message'] = excpt.message
        else:
            self.email_notifications(iorder, is_new_iorder=False)
        return Response(data=data, status=status_code)

api_optplaces_orders_detail = IorderInfoView.as_view()

class ApiLoruProductTypesView(APIView):
    permission_classes = (PermitIfLoru,)

    def get(self, request):
        return Response(
            data=[ dict(
                    id=pt[0],
                    name =unicode(pt[1]),
                   )
                    for pt in Product.PRODUCT_TYPES
            ],
            status=200,
        )

api_loru_product_types = ApiLoruProductTypesView.as_view()

class ApiProductList(ProductCategoryQsMixin, APIView):
    permission_classes = (PermitIfLoru,)
    parser_classes = (MultiPartParser,)

    def get(self, request):
        qs = Q(loru=request.user.profile.org)
        qs &= self.product_category_qs()

        data = [ ProductEditSerializer(p, context=dict(request=request)).data \
                for p in Product.objects.filter(qs)
        ]
        return Response(data=data, status=200)

    def post(self, request):
        required_not_got = list()
        for f in (
            'name',
            'description',
            'categoryId',
                 ):
            if not request.DATA.get(f):
                required_not_got.append(f)
        if required_not_got:
            return Response(
                data={
                    'status': 'error',
                    'message': _(u"Не заданы параметры: %s") % ", ".join(required_not_got),
                     },
                status=400,
            )
        serializer = ProductEditSerializer(data=request.DATA, context={ 'request': request, })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

api_product_list = ApiProductList.as_view()

class ApiProductDetail(APIView):
    permission_classes = (PermitIfLoru,)
    parser_classes = (MultiPartParser,)

    def get_object(self, request, pk):
        try:
            return Product.objects.get(loru=request.user.profile.org, pk=pk)
        except Product.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        product = self.get_object(request, pk)
        serializer = ProductEditSerializer(product, context=dict(request=request))
        return Response(serializer.data)

    def put(self, request, pk):
        product = self.get_object(request, pk)
        serializer = ProductEditSerializer(
            product,
            data=request.DATA,
            context=dict(request=request),
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

api_product_detail = ApiProductDetail.as_view()

class ApiServicesView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = ServiceSerializer(Service.objects.all(), many=True)
        return Response(serializer.data, status=200)

api_services = ApiServicesView.as_view()

class ApiOrgServicesMixin(object):
    
    class Data(object):
        service=None
        measures = []
        orgservice = None
        measures_get = []

    def check_org_id(self, request, org_id):
        org, message = request.user.profile.org, ''
        if str(org.pk) != str(org_id):
            message = _(u"Org_id %s не соответствует организации, выполняющей запрос") % org_id
        return org, message
    
    def check_input_message(self, request, org_id, service_name=None):
        self.data = self.Data()
        self.data.measures_get = request.DATA.get('measures', [])

        org, message = self.check_org_id(request, org_id)
        if message:
            return message

        if not service_name:
            service_name = request.DATA.get('type')
        try:
            self.data.service = Service.objects.get(name=service_name)
        except Service.DoesNotExist:
            return _(u"Сервис %s неизвестен в системе") % service_name

        try:
            self.data.orgservice = OrgService.objects.get(org=org, service=self.data.service)
        except OrgService.DoesNotExist:
            if request.method == 'POST' and not self.data.measures_get:
                return _(u"У организации нет цен по сервису %s. Нельзя его активировать, не указав цены") % service_name
            # - put (задать цены):          сервис будет создан у организации
            # - delete (де-активировать):   нет сервиса, не будет и после запроса,
            #                               т.е. сервис останется неактивированным у организации

        if request.method == 'PUT' and not self.data.measures_get:
            return _(u"Изменение цен по сервису. Не указаны цены")

        self.data.measures = Measure.objects.filter(service=self.data.service)
        measure_names = [v['name'] for v in self.data.measures.values('name')]
        for m in self.data.measures_get:
            if m['name'] not in measure_names:
                return _(u"Нет единицы измерения %s у услуги %s") % (m['name'], service_name)
        return ''

    def put_prices(self, request):
        if self.data.orgservice:
            orgservice = self.data.orgservice
            if request.method == 'POST' and not orgservice.enabled:
                orgservice.enabled = True
                orgservice.save()
        else:
            orgservice = OrgService.objects.create(
                org=request.user.profile.org,
                service=self.data.service,
                enabled=request.method == "POST",
            )
            self.data.orgservice = orgservice
        for measure in self.data.measures:
            price = None
            for m in self.data.measures_get:
                if m['name'] == measure.name:
                    price = m['price']
                    break
            orgserviceprice, created_ = OrgServicePrice.objects.get_or_create(
                orgservice=orgservice,
                measure=measure,
                defaults=dict(price=price or 0.00)
            )
            if not created_ and price is not None:
                orgserviceprice.price = price
                orgserviceprice.save()

class ApiOrgServicesView(ApiOrgServicesMixin, APIView):
    permission_classes = (PermitIfLoru,)

    def get(self, request, org_id):
        org, message = self.check_org_id(request, org_id)
        if message:
            return Response(data=dict(status='error', message=message), status=200)
        return Response(
            data=OrgServiceSerializer(OrgService.objects.filter(org=org), many=True).data,
            status=200
        )

    @transaction.commit_on_success
    def post(self, request, org_id):
        """
        Активизировать сервис у организации org_id
        
        Вх.данные, пример:
        {
        "type": "photo",
        "measures": [
          {
          "name": "unit",
          "value": 234
          }
         ]
        }
        """
        message = self.check_input_message(request, org_id)
        if message:
            return Response(data=dict(status='error', message=message), status=400)
        self.put_prices(request)
        return Response(data=dict(status='success'), status=200)

api_org_services = ApiOrgServicesView.as_view()

class ApiOrgServicesEditView(ApiOrgServicesMixin, APIView):
    permission_classes = (PermitIfLoru,)

    @transaction.commit_on_success
    def put(self, request, org_id, service_name):
        """
        Править сервис service_name у организации org_id
        
        Вх.данные, пример:
        {
        "measures": [
          {
          "name": "unit",
          "value": 234
          }
         ]
        }
        """
        message = self.check_input_message(request, org_id, service_name)
        if message:
            return Response(data=dict(status='error', message=message), status=400)
        self.put_prices(request)
        return Response(data=dict(status='success'), status=200)

    def delete(self, request, org_id, service_name):
        """
        Де-активация сервиса service_name у организации org_id
        """
        message = self.check_input_message(request, org_id, service_name)
        orgservice = self.data.orgservice
        if orgservice and orgservice.enabled:
            orgservice.enabled = False
            orgservice.save()
        return Response(data=dict(status='success'), status=200)

api_org_services_edit = ApiOrgServicesEditView.as_view()

class ApiServicePriceMixin(object):

    class Data(object):
        service = None
        service_name = None
        orgservice=None
        orgservice_delivery = None
        customplace = None
        latitude = None
        longitude = None
        need_delivery = False
        org = None

    def check_input_message(self, request):
        self.data = self.Data()
        try:
            if request.method == 'GET':
                req_dict = request.GET
            elif request.method == 'POST':
                req_dict = request.DATA

            self.data.service_name = req_dict.get('type')
            try:
                self.data.service = self.data.service_name and Service.objects.get(name=self.data.service_name)
            except Service.DoesNotExist:
                self.data.service = None
            if not self.data.service:
                raise ServiceException(_(u'Сервис не задан или неизвестен'))

            if request.method == 'POST':
                org = req_dict.get('performerId')
                try:
                    org = org and Org.objects.get(pk=org)
                except Org.DoesNotExist:
                    pass
                if not org:
                    raise ServiceException(_(u"Id исполнителя не задан или не найден среди организаций"))
                if org.type not in (Org.PROFILE_LORU, ):
                    raise ServiceException(_(u"performerId %s - не ЛОРУ (поставщик услуг)") % org.pk)
                try:
                    self.data.orgservice = OrgService.objects.get(
                        org=org,
                        service=self.data.service,
                        enabled=True
                    )
                except OrgService.DoesNotExist:
                    raise ServiceException(_(u"Сервис %s не активирован у организации Id=%s") % (
                          self.data.service_name,
                          org.pk,
                    ))
                self.data.org = org

            customplace_id = req_dict.get('placeId')
            try:
                self.data.customplace = customplace_id and CustomPlace.objects.get(pk=customplace_id)
            except CustomPlace.DoesNotExist:
                self.data.customplace = None
            if not self.data.customplace:
                raise ServiceException(_(u'Не задан placeId или не найдено место'))
            if self.data.customplace.user != request.user:
                raise ServiceException(_(u'Пользователь %s не имеет прав на запрос по этому месту') % request.user.username)
            
            self.data.need_delivery = self.data.service_name in ('photo', 'delivery')
            if self.data.need_delivery:
                if request.method == 'GET':
                    latitude = req_dict.get('location[latitude]')
                    longitude = req_dict.get('location[longitude]')
                elif request.method == 'POST':
                    latitude = req_dict.get('location') and req_dict['location'].get('latitude')
                    longitude = req_dict.get('location') and req_dict['location'].get('longitude')
                if latitude is None or longitude is None:
                    latitude = self.data.customplace.address and self.data.customplace.address.gps_y
                    longitude = self.data.customplace.address and self.data.customplace.address.gps_x
                if (latitude is None or longitude is None) and self.data.customplace.place:
                    latitude = self.data.customplace.place.lat
                    longitude = self.data.customplace.place.lng
                if latitude is None or longitude is None:
                    raise ServiceException(_(u'Не заданы и не удалось выяснить координаты места'))
                self.data.latitude = float(latitude)
                self.data.longitude = float(longitude)
                if request.method == 'POST' and self.data.service_name != 'delivery':
                    try:
                        self.data.orgservice_delivery = OrgService.objects.get(
                            org=org,
                            service__name='delivery',
                            enabled=True
                        )
                    except OrgService.DoesNotExist:
                        raise ServiceException(_(u'Услуга %s требует еще активной услуги доставки у организации') % (
                            self.data.service_name,
                        ))
                    

        except ServiceException as excpt:
            return excpt.message
        return ''

    def get_price_service(self, org):
        """
        Цена за услугу у огранизации
        """
        if self.data.service.name == 'delivery':
            # цена за доставку считается не по организации, а по складам
            price_service = 0
        elif self.data.service.name in ('photo', ):
            price_service = OrgServicePrice.objects.get(
                orgservice__service=self.data.service,
                orgservice__org=org,
                measure__name='unit',
            ).price
        else:
            price_service = 0
        return round(float(price_service), 2)

    def get_price_delivery(self, org, km, kg=None, m3=None):
        """
        Цена за доставку XX kg и/или yy m3 груза на расстояние km в организации org
        """
        result = 0.00
        for m in OrgServicePrice.objects.filter(
            orgservice__org=org,
            orgservice__service__name='delivery'
            ).values('measure__name', 'price'):
            if m['measure__name'] == 'km':
                result += float(m['price']) * km
            elif kg and m['measure__name'] == 'kg':
                result += float(m['price']) * kg * km
            elif m3 and m['measure__name'] == 'm3':
                result += float(m['price']) * m3 * km
        return round(result, 2)

class ApiClientAvailablePerformersView(ApiServicePriceMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    def get(self, request):
        """
        Получить список возможных исполнителей работы
        
        Выбираются исполнители, подписавшиеся на сервис.
            - если сервис требует транспортных расходов, то еще и подписавшиеся
              на сервис delivery.
        Из них выбираются те, кто имеют склады с коодинатами
        Из этих складов выбираются ближайший
        """
        message = self.check_input_message(request)
        if message:
            return Response(data=dict(status='error', message=message), status=400)

        q = Q(
            loru__orgservice__service=self.data.service,
            loru__orgservice__enabled=True,
        )
        if self.data.need_delivery:
            q &= Q(
                address__gps_x__isnull=False,
                address__gps_y__isnull=False,
            )
            if self.data.service_name != 'delivery':
                orgs = [orgservice.org for orgservice in OrgService.objects.filter(
                    service=self.data.service,
                    enabled=True,
                )]
                q &= Q(loru__in=orgs)
            customer_loc = LatLon(Latitude(self.data.latitude), Longitude(self.data.longitude))

        data = []
        org = None
        for store in Store.objects.filter(q).order_by('loru'):
            # Идем по складам одного поставщика, потом по складам другого поставщика...
            if org is None:
                org = store.loru
                # Цена за любую услугу, кроме delivery
                price_org = self.get_price_service(org)
                # Больше длины экватора
                distance = 41000.0

            if store.loru != org:
                if self.data.need_delivery:
                    kwargs = dict(km=distance)
                    price_org += self.get_price_delivery(org, **kwargs)
                data.append(dict(
                    id=org.pk,
                    name=org.name,
                    price=round(price_org, 2),
                    currency=org.currency.code,
                ))
                org = store.loru
                price_org = self.get_price_service(org)
                distance = 41000.0

            if self.data.need_delivery:
                store_loc = LatLon(Latitude(store.address.gps_y), Longitude(store.address.gps_x))
                distance = min(distance, store_loc.distance(customer_loc))

        if org:
            if self.data.need_delivery:
                kwargs = dict(km=distance)
                price_org += self.get_price_delivery(org, **kwargs)
            data.append(dict(
                id=org.pk,
                name=org.name,
                price=round(price_org, 2),
                currency=org.currency.code,
            ))

        return Response(data=data, status=200)

api_client_available_performers = ApiClientAvailablePerformersView.as_view()

class ApiClientOrdersView(ApiServicePriceMixin, APIView):
    permission_classes = (PermitIfCabinet,)

    @transaction.commit_on_success
    def post(self, request):
        """
        Принять предложение о создании заказа

        Вх. данные, пример:
        {
            "type": "photo",
            "performerId": 19,
            "placeId": 43,
            "location": {
                "latitude": 52.70,
                "longitude": 27.35
            },
            "comment": "Коментарий к заказу"
        }
        """
        message = self.check_input_message(request)
        if message:
            return Response(data=dict(status='error', message=message), status=400)

        distance = 41000.0
        price_org = self.get_price_service(self.data.org)
        closest_store = dict(lat=0, lng=0)
        if self.data.need_delivery:
            customer_loc = LatLon(Latitude(self.data.latitude), Longitude(self.data.longitude))
            for store in self.data.org.store_set.filter(
                address__gps_x__isnull=False,
                address__gps_y__isnull=False,
            ):
                store_loc = LatLon(Latitude(store.address.gps_y), Longitude(store.address.gps_x))
                distance_store = store_loc.distance(customer_loc)
                if distance_store < distance:
                    distance = distance_store
                    closest_store=dict(lat=store.address.gps_y, lng=store.address.gps_x)

            kwargs = dict(km=distance)
            price_delivery = self.get_price_delivery(self.data.org, **kwargs)
        else:
            price_delivery = 0.00

        login_phone = request.user.customerprofile.login_phone
        applicant = AlivePerson.objects.create(
            user=request.user,
            phones=u"+%s" % login_phone if login_phone else None,
            login_phone=login_phone,
            last_name=request.user.customerprofile.user_last_name,
            first_name=request.user.customerprofile.user_first_name,
            middle_name=request.user.customerprofile.user_middle_name,
        )
        cost=round(price_org +price_delivery, 2)
        order = Order(
            loru=self.data.org,
            applicant=applicant,
            cost=cost,
            dt=datetime.date.today(),
            customplace=self.data.customplace,
        )
        # так будет назначен loru_number:
        order.save()
        if self.data.service_name != 'delivery':
            item_service = ServiceItem.objects.create(
                order=order,
                orgservice=self.data.orgservice,
                cost=price_org,
            )
        if self.data.need_delivery:
            item_service = ServiceItem.objects.create(
                order=order,
                orgservice=self.data.orgservice_delivery,
                cost=price_delivery,
            )
            Route.objects.create(order=order, index=0, **closest_store)
            Route.objects.create(
                order=order,
                index=1,
                lat=self.data.latitude,
                lng=self.data.longitude,
            )
        comment = request.DATA.get('comment')
        if comment:
            OrderComment.objects.create(
                order=order,
                user=request.user,
                comment=comment,
            )

        return Response(
            data=dict(status='success', price=cost, currency=self.data.org.currency.code),
            status=200,
        )

api_client_orders = ApiClientOrdersView.as_view()
