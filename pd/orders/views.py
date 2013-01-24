# coding=utf-8

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import CreateView
from django.utils.translation import ugettext_lazy as _

from orders.forms import OrderForm
from orders.models import Order, OrderItem, Product, PT_BURIAL
from orgs.views import get_user_org


class CreateOrder(CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/create.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            org = get_user_org(request.user)
            if not org or not org.is_loru():
                messages.error(request, _(u'Только ЛОРУ может добавлять заказы'))
                return redirect('/')

            return super(CreateOrder, self).dispatch(request, *args, **kwargs)

        messages.error(request, _(u'Доступно только для пользователей'))
        return redirect('ulogin')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, _(u'Заказ сохранен, добавляем товары и услуги'))
        return reverse('new_order_item', args=[self.object.pk])

new_order = CreateOrder.as_view()

class CreateOrderItem(CreateView):
    model = OrderItem
    template_name = 'orders/create_item.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated() :
            self.order = get_object_or_404(Order, creator=request.user, pk=args[0])
            return super(CreateOrderItem, self).dispatch(request, *args, **kwargs)

        messages.success(request, _(u'Доступно только для пользователей'))
        return redirect('ulogin')

    def get_context_data(self, **kwargs):
        data = super(CreateOrderItem, self).get_context_data(**kwargs)
        data.update(order=self.order)
        data['form'].fields['product'].queryset = Product.objects.filter(
            Q(creator__isnull=True) | Q(creator=self.request.user)
        )
        return data

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.order = self.order
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.object.product.type == PT_BURIAL:
            messages.info(self.request, _(u'Переходим к созданию захоронения'))
            return reverse('new_burial')+'?order_item_pk=%s' % self.object.pk

        messages.success(self.request, _(u'Заказ сохранен, добавляем товары и услуги'))
        return reverse('new_order_item', args=[self.order.pk])

new_order_item = CreateOrderItem.as_view()
