from django.db import migrations


def reverse_it(apps, schema_editor):
    pass

def operation(apps, schema_editor):
    Hall = apps.get_model('halls', 'Hall')
    HallWeekly = apps.get_model('halls', 'HallWeekly')
    for hall in Hall.objects.all():
        for dow in (1, 2, 3, 4, 5, 6, 7):
            HallWeekly.objects.create(
                hall=hall,
                dow=dow,
                time_start=hall.time_start,
                time_end=hall.time_end,
                interval=hall.interval,
                is_dayoff=False,
            )

class Migration(migrations.Migration):

    dependencies = [
        ('halls', '0003_auto_20191001_1429'),
    ]

    operations = [
        migrations.RunPython(operation, reverse_it),
    ]
