# coding=utf-8
import datetime

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.template.context import RequestContext
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _

from logs.models import write_log
from orders.forms import ProductForm, OrderForm, OrderItemFormset, CoffinForm, CatafalqueForm
from orders.models import Product, Order, OrderItem
from reports.models import make_report


class LORURequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if not request.user.is_authenticated():
            return redirect('/')
        if not getattr(self.request.user, 'profile', None):
            return redirect('/')
        if not self.request.user.profile.is_loru():
            return redirect('/')
        return View.dispatch(self, request, *args, **kwargs)

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
        return redirect('order_edit', self.object.pk)

order_create = OrderCreate.as_view()

class OrderEdit(LORURequiredMixin, UpdateView):
    template_name = 'order_edit.html'
    form_class = OrderForm

    def get_queryset(self):
        return Order.objects.filter(loru=self.request.user.profile.org)

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.formset = OrderItemFormset(request=self.request, data=request.POST or None, instance=self.get_object())
        self.catafalque_form = CatafalqueForm(data=request.POST or None, instance=self.get_object().get_catafalquedata())
        self.coffin_form = CoffinForm(data=request.POST or None, instance=self.get_object().get_coffindata())
        return super(OrderEdit, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(OrderEdit, self).get_context_data(**kwargs)
        data.update({'formset': self.formset})
        if self.get_object().has_catafalque():
            data.update({'catafalque_form': self.catafalque_form})
        if self.get_object().has_coffin():
            data.update({'coffin_form': self.coffin_form})
        return data

    def form_valid(self, form):
        catafalque_ok = not self.get_object().has_catafalque() or self.catafalque_form.is_valid()
        coffin_ok = not self.get_object().has_coffin() or self.coffin_form.is_valid()
        if self.formset.is_valid() and catafalque_ok and coffin_ok:
            self.formset.save()
            self.object = form.save()

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
            return redirect('order_list')
        else:
            messages.error(self.request, _(u"Обнаружены ошибки"))
            return self.form_invalid(form)

order_edit = OrderEdit.as_view()

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

