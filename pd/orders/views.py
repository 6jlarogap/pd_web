from django.views.generic.edit import CreateView
from orders.models import Order


class CreateOrder(CreateView):
    model = Order
    template_name = 'orders/create.html'
