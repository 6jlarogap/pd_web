# coding=utf-8
import datetime
from burials.forms import AddOrgForm

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.template.context import RequestContext
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _

from logs.models import write_log
from orders.forms import ProductForm, OrderForm, OrderItemFormset, CoffinForm, CatafalqueForm
from orders.models import Product, Order, OrderItem
from pd.forms import CommentForm
from reports.models import make_report


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

class OrderList(LORURequiredMixin, ListView):
    template_name = 'order_list.html'
    model = Order

    def get_queryset(self):
        return Order.objects.filter(loru=self.request.user.profile.org)

order_list = OrderList.as_view()

class OrderCreate(LORURequiredMixin, CreateView):
    template_name = 'order_create.html'
    form_class = OrderForm

    def get_context_data(self, **kwargs):
        data = super(OrderCreate, self).get_context_data(**kwargs)
        data['org_form'] = AddOrgForm(prefix='loru')
        return data

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.loru = self.request.user.profile.org
        self.object.save()

        for p in Product.objects.filter(loru=self.request.user.profile.org, default=True):
            OrderItem.objects.create(order=self.object, product=p)

        write_log(self.request, self.object, _(u'Заказ создан'))
        msg = _(u"<a href='%s'>Заказ %s</a> создан") % (
            reverse('order_edit', args=[self.object.pk]),
            self.object.pk,
        )
        messages.success(self.request, msg)
        return redirect('order_products', self.object.pk)

order_create = OrderCreate.as_view()

class OrderEdit(LORURequiredMixin, UpdateView):
    template_name = 'order_edit_applicant.html'
    form_class = OrderForm

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

        write_log(self.request, self.object, _(u'Заказ изменен'))
        msg = _(u"<a href='%s'>Заказ %s</a> изменен") % (
            reverse('order_edit', args=[self.object.pk]),
            self.object.pk,
        )
        messages.success(self.request, msg)
        return redirect('order_list')

order_edit = OrderEdit.as_view()

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
            formset.save()

            self.object = self.get_object()

            write_log(self.request, self.object, _(u'Заказ изменен'))
            msg = _(u"<a href='%s'>Заказ %s</a> изменен") % (
                reverse('order_edit', args=[self.object.pk]),
                self.object.pk,
            )
            messages.success(self.request, msg)
            if self.object.has_burial() and not self.object.get_burial():
                return redirect(reverse('create_burial', args=[]) + '?order=%s' % self.object.pk)
            if self.object.has_services() and not self.object.get_coffindata() and not self.object.get_catafalquedata():
                return redirect('order_services', self.object.pk)
            return redirect('order_list')
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

    def get_coffin_form(self):
        return CoffinForm(data=self.request.POST or None, instance=self.get_object().get_coffindata())

    def get_context_data(self, **kwargs):
        data = {'order': self.get_object()}
        if self.get_object().has_catafalque():
            data.update({'catafalque_form': self.get_catafalque_form()})
        if self.get_object().has_coffin():
            data.update({'coffin_form': self.get_coffin_form()})
        return data

    def post(self, request, *args, **kwargs):
        self.request = request
        self.catafalque_form = self.get_catafalque_form()
        self.coffin_form = self.get_coffin_form()
        catafalque_ok = not self.get_object().has_catafalque() or self.catafalque_form.is_valid()
        coffin_ok = not self.get_object().has_coffin() or self.coffin_form.is_valid()
        if catafalque_ok and coffin_ok:
            self.object = self.get_object()

            if self.catafalque_form.is_valid():
                cat = self.catafalque_form.save(commit=False)
                cat.order = self.object
                cat.save()

            if self.coffin_form.is_valid():
                coffin = self.coffin_form.save(commit=False)
                coffin.order = self.object
                coffin.save()

            write_log(self.request, self.object, _(u'Заказ изменен'))
            msg = _(u"<a href='%s'>Заказ %s</a> изменен") % (
                reverse('order_edit', args=[self.object.pk]),
                self.object.pk,
            )
            messages.success(self.request, msg)
            return redirect('order_info', self.object.pk)
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