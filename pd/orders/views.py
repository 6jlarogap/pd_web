# coding=utf-8

import datetime
import decimal
import json

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.aggregates import Count, Sum
from django.db.models.query_utils import Q
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.template.context import RequestContext
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.shortcuts import get_object_or_404

from logs.models import write_log
from burials.forms import AddOrgForm, AddAgentForm, AddDoverForm, AddDocTypeForm
from burials.models import Burial, Place, Grave, GravePhoto, PlacePhoto
from users.models import CustomerProfile, CustomerProfilePhoto, Org, ProfileLORU
from orders.forms import ProductForm, OrderForm, OrderItemFormset, CoffinForm, CatafalqueForm, \
                         AddInfoForm, OrderSearchForm, OrderBurialForm
from orders.models import Product, Order, OrderItem, ProductCategory, ProductStatus, ProductHistory
from pd.forms import CommentForm
from pd.views import PaginateListView, RequestToFormMixin
from reports.models import make_report

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from serializers import ProductCategorySerializer, ProductsSerializer, ProductInfoSerializer


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

class ProductCreate(LORURequiredMixin, CreateView):
    template_name = 'product_create.html'
    form_class = ProductForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.loru = self.request.user.profile.org
        self.object.save()
        write_log(self.request, self.object, _(u'Товар создан'))
        msg = _(u"<a href='%s'>Товар %s</a> создан") % (
            reverse('manage_products_edit', args=[self.object.pk]),
            self.object.name,
        )
        messages.success(self.request, msg)
        return redirect('manage_products')

manage_products_create = ProductCreate.as_view()

class ProductEdit(LORURequiredMixin, UpdateView):
    template_name = 'product_edit.html'
    form_class = ProductForm

    def get_queryset(self):
        return Product.objects.filter(loru=self.request.user.profile.org)

    def form_valid(self, form):
        self.object = form.save()
        write_log(self.request, self.object, _(u'Товар изменен'))
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
        orders = Order.objects.filter(loru=self.request.user.profile.org) 
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
    permission_classes = (IsAuthenticated,)

class CustomerDataMixin:
    def get_customer_data(self, request):
        username = request.user.username
        places = []
        lorus = set()
        is_customer = True
        try:
            request.user.customerprofile
        except CustomerProfile.DoesNotExist:
            is_customer = False
        else:
            try:
                login_phone = decimal.Decimal(username)
            except decimal.InvalidOperation:
                is_customer = False
            else:
                lorus = set()
                for p in Place.objects.filter(responsible__login_phone=login_phone):
                    places.append(p)
                    lorus.update(p.cemetery.ugh.get_loru_list())
        return is_customer, places, lorus
        

class CatalogFiltersViewSet(CustomerDataMixin, viewsets.ViewSet):
    queryset = Place.objects.none()
    permission_classes = (IsAuthenticated,)
    
    def list(self, request):
        is_customer, places, lorus = self.get_customer_data(request)
        places = [{'id': p.pk, 'place': p.place, } for p in places]
        suppliers = [{'id': l.pk, 'name': l.name, } for l in lorus]
        data = {
            'supplier': suppliers,
            'place': places,
        }
        return Response(status=200 if is_customer else 400, data=data)

class ProductsViewSet(CustomerDataMixin, viewsets.ModelViewSet):
    model = Product
    serializer_class = ProductsSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        is_customer, places, lorus = self.get_customer_data(self.request)
        if not is_customer or not places:
            return Product.objects.none()

        place_id = self.request.GET.get('filter[place]')
        loru_id = self.request.GET.get('filter[supplier]')
        qs = Q(loru__in=lorus) if not place_id and not loru_id else Q()

        if place_id:
            for p in places:
                if p.pk == int(place_id):
                    place = p
                    break
            else:
                return Product.objects.none()
            qs &= Q(loru__ugh_list__ugh=place.cemetery.ugh)

        if loru_id:
            for l in lorus:
                if l.pk == int(loru_id):
                    loru = l
                    break
            else:
                return Product.objects.none()
            qs &= Q(loru=loru)

        if self.request.GET.get('filter[price_from]'):
            qs &= Q(price__gte=self.request.GET.get('filter[price_from]'))
        if self.request.GET.get('filter[price_to]'):
            qs &= Q(price__lte=self.request.GET.get('filter[price_to]'))
        if self.request.GET.get('filter[category]'):
            qs &= Q(productcategory__pk=self.request.GET.get('filter[category]'))
        
        offset = self.request.GET.get('offset') and int(self.request.GET.get('offset'))
        limit = self.request.GET.get('limit') and int(self.request.GET.get('limit'))
        
        filter = Product.objects.filter(qs)
        if offset and limit:
            filter = filter[offset:offset+limit]
        elif offset:
            filter = filter[offset:]
        elif limit:
            filter = filter[:limit]
        
        return filter
        
class ProductInfoViewSet(CustomerDataMixin, viewsets.ModelViewSet):
    model = Product
    serializer_class = ProductInfoSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        is_customer, places, lorus = self.get_customer_data(self.request)
        if not is_customer or not places or not self.request.GET.get('id'):
            return Product.objects.none()
        return Product.objects.filter(loru__in=lorus, pk=self.request.GET.get('id'))

class CabinetViewSet(CustomerDataMixin, viewsets.ViewSet):
    queryset = CustomerProfile.objects.none()
    permission_classes = (IsAuthenticated,)
    
    def list(self, request):
        is_customer, places, lorus = self.get_customer_data(request)
        if not is_customer:
            return Response(status=400, data=[])
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
        data['loginPhone'] = request.user.username
        data['places'] = []
        for p in places:
            place={'id': p.pk}
            place['address'] = p.cemetery.address and p.cemetery.address.__unicode__() or ''
            place['location'] = {
                'latitude': p.lat,
                'longitude': p.lng,
            }
            place['graves'] = []
            gallery = []
            for pph in PlacePhoto.objects.filter(place=p):
                if pph.bfile:
                    gallery.append(
                        {
                            'photo': request.build_absolute_uri(pph.bfile.url),
                            'addedAt': pph.date_of_creation,
                        }
                    )
            for g in Grave.objects.filter(place=p).order_by('grave_number'):
                grave = {'graveNumber': g.grave_number}
                for gph in GravePhoto.objects.filter(grave=g):
                    if gph.bfile:
                        gallery.append(
                            {
                                'photo': request.build_absolute_uri(gph.bfile.url),
                                'addedAt': gph.date_of_creation,
                            }
                        )
                burials = []
                for b in g.burial_set.all():
                    burials.append(
                        {
                            'id': b.pk,
                            'fio': b.deadman and b.deadman.full_name_complete() or _(u"Неизвестный"),
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

class UserLoruMixin:
    ivalid_user_data = { "detail": "User denied access: not LORU" }
    
    def check_if_loru(self, request):
        try:
            request.user and request.user.profile
        except (AttributeError, Profile.DoesNotExist):
            return False
        else:
            return request.user.profile.is_loru()

class LoruProductPlaces(UserLoruMixin, APIView):
    """
    Обновление статусов продуктов на площадках (ОМС)

    Пример:
    [
        {
            “id”: 1,
            “places”: [
            {
                “id”: 5, 
                “status”: “disable”
            },
            {
                “id”: 8, 
                “status”: “up”
            }
            ]
        },
        {
            “id”: 2,
            “places”: [
            {
                “id”: 5, 
                “status”: “enable”
            }
            ]
        }
    ]
    """
    
    permission_classes = (IsAuthenticated,)

    @transaction.commit_on_success
    def post(self, request, format=None):
        if not self.check_if_loru(request):
            return Response(data=self.ivalid_user_data, status=403)
        data = []
        for p in request.DATA:
            if Product.objects.filter(pk=p['id'], loru=request.user.profile.org).count():
                data_p = { 'id': p['id'], 'places': [] }
                for o in p['places']:
                    if ProfileLORU.objects.filter(ugh_id=o['id'], loru=request.user.profile.org).count():
                        ugh = Org.objects.get(pk=o['id'])
                        data_p['places'].append(o)
                        dt = datetime.datetime.now()
                        status, created = ProductStatus.objects.get_or_create(
                                            product_id=p['id'],
                                            ugh=ugh,
                                            defaults={'status': o['status'],
                                                      'dt': dt,
                                            }
                        )
                        if not created:
                            status.status=o['status']
                            status.dt=dt
                            status.save()
                        publish_cost = '0.0' if o['status'] == ProductHistory.PRODUCT_OPERATION_DISABLE \
                                           else ugh.publish_cost
                        ProductHistory.objects.create(
                                        product_id=p['id'],
                                        ugh=ugh,
                                        operation=o['status'],
                                        dt=dt,
                                        publish_cost=publish_cost,
                                        currency=ugh.currency,
                        )
                data.append(data_p)
        return Response(data=data, status=200)

loru_product_places = LoruProductPlaces.as_view()

class UghPublishedProductsViewSet(viewsets.ViewSet):
    queryset = Product.objects.none()
    permission_classes = (IsAuthenticated,)
    
    def list(self, request):
        data=[]
        try:
            profile=request.user.profile
        except AttributeError:
            return Response(status=400, data=data)
        if not profile.is_loru():
            return Response(status=400, data=data)
        ugh_list = [ pl.ugh for pl in ProfileLORU.objects.filter(loru=profile.org)]
        for p in Product.objects.filter(loru=profile.org).order_by('pk'):
            data_p = { 'id': p.pk, 'name': p.name, 'availableOnPlaces': [] }
            for ps in ProductStatus.objects.filter(product=p, ugh__in=ugh_list):
                if ps.status in (ProductHistory.PRODUCT_OPERATION_ENABLE,
                                 ProductHistory.PRODUCT_OPERATION_UP):
                    data_p['availableOnPlaces'].append(ps.ugh.pk)
            data.append(data_p)
        return Response(status=200, data=data)
