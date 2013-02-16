# coding=utf-8
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.shortcuts import redirect
from django.views.generic.base import View
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _
from logs.models import write_log
from orders.forms import ProductForm, OrderForm, OrderItemFormset
from orders.models import Product, Order


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
        return super(OrderEdit, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(OrderEdit, self).get_context_data(**kwargs)
        data['formset'] = self.formset
        return data

    def form_valid(self, form):
        self.formset.save()
        self.object = form.save()
        write_log(self.request, self.object, _(u'Заказ изменен'))
        msg = _(u"<a href='%s'>Заказ %s</a> изменен") % (
            reverse('order_edit', args=[self.object.pk]),
            self.object.pk,
        )
        messages.success(self.request, msg)
        return redirect('order_list')

order_edit = OrderEdit.as_view()
