import datetime

from django.db import migrations

def reverse_it(apps, schema_editor):
    pass

def operation(apps, schema_editor):
    print('')
    Order = apps.get_model('orders', 'Order')
    Log = apps.get_model('logs', 'Log')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ct = ContentType.objects.get_for_model(Order)
    n = 0
    for order in Order.objects.filter(status='paid').order_by('pk'):
        try:
            log_rec = Log.objects.filter(
                ct=ct,
                obj_id=order.pk,
                msg='Заказ: оплачен',
            ).order_by('-dt')[0]
            Order.objects.filter(pk=order.pk).update(dt_paid=log_rec.dt)
            n += 1
        except IndexError:
            print(
                'WARNING: Paid order, pk=%s, dt=%s, not found a payment record in Log' % (
                    order.pk,
                    order.dt.strftime("%d.%m.%Y")
            ))
    print('%s paid orders updated' % n)

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_order_dt_paid'),
    ]

    operations = [
        migrations.RunPython(operation, reverse_it),
    ]
