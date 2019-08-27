from django.db import models, migrations
import autoslug.fields
import pd.models
import django.db.models.deletion
from django.conf import settings
import orders.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AddInfoData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('add_info', models.TextField(verbose_name='\u0414\u043e\u043f.\u0438\u043d\u0444\u043e', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CatafalqueData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('route', models.TextField(verbose_name='\u041c\u0430\u0440\u0448\u0440\u0443\u0442')),
                ('start_time', models.TimeField(verbose_name='\u0412\u0440\u0435\u043c\u044f \u043f\u043e\u0434\u0430\u0447\u0438')),
                ('start_place', models.TextField(null=True, verbose_name='\u041c\u0435\u0441\u0442\u043e \u043f\u043e\u0434\u0430\u0447\u0438')),
                ('end_time', models.TimeField(null=True, verbose_name='\u0412\u0440\u0435\u043c\u044f \u043e\u0442\u043f\u0443\u0441\u043a\u0430 \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u043c')),
                ('cemetery_time', models.TimeField(null=True, verbose_name='\u0412\u0440\u0435\u043c\u044f \u0437\u0430\u0435\u0437\u0434\u0430 \u043d\u0430 \u043a\u043b\u0430\u0434\u0431\u0438\u0449\u0435')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CoffinData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('size', models.TextField(verbose_name='\u0420\u0430\u0437\u043c\u0435\u0440')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Measure',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('title', models.CharField(max_length=255, verbose_name='\u0417\u0430\u0433\u043b\u0430\u0432\u0438\u0435')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('type', models.CharField(default='burial', verbose_name='\u0422\u0438\u043f \u0417\u0430\u043a\u0430\u0437', max_length=255, editable=False, choices=[('burial', '\u0417\u0430\u043a\u0430\u0437 \u043d\u0430 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0435'), ('trade', '\u041e\u043f\u0442\u043e\u0432\u044b\u0439 \u0437\u0430\u043a\u0430\u0437'), ('customer', '\u0417\u0430\u043a\u0430\u0437 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f')])),
                ('loru_number', models.PositiveIntegerField(verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0432 \u043f\u0435\u0440\u0435\u0434\u0435\u043b\u0430\u0445 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044f \u0437\u0430\u043a\u0430\u0437\u0430', null=True, editable=False)),
                ('number', models.PositiveIntegerField(verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0432 \u043f\u0435\u0440\u0435\u0434\u0435\u043b\u0430\u0445 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044f \u0437\u0430\u043a\u0430\u0437\u0430 \u0438 \u0433\u043e\u0434\u0430', null=True, editable=False)),
                ('payment', models.CharField(default='cash', max_length=255, verbose_name='\u0422\u0438\u043f \u043f\u043b\u0430\u0442\u0435\u0436\u0430', choices=[('cash', '\u041d\u0430\u043b\u0438\u0447\u043d\u044b\u0439'), ('wire', '\u0411\u0435\u0437\u043d\u0430\u043b\u0438\u0447\u043d\u044b\u0439')])),
                ('agent_director', models.BooleanField(default=False, verbose_name='\u0414\u0438\u0440\u0435\u043a\u0442\u043e\u0440-\u0410\u0433\u0435\u043d\u0442')),
                ('annulated', models.BooleanField(default=False, verbose_name='\u0410\u043d\u043d\u0443\u043b\u0438\u0440\u043e\u0432\u0430\u043d', editable=False)),
                ('archived', models.BooleanField(default=False, verbose_name='\u0410\u0440\u0445\u0438\u0432\u0438\u0440\u043e\u0432\u0430\u043d', editable=False)),
                ('cost', models.DecimalField(verbose_name='\u0426\u0435\u043d\u0430', editable=False, max_digits=20, decimal_places=2)),
                ('dt', models.DateField(verbose_name='\u0414\u0430\u0442\u0430 \u0437\u0430\u043a\u0430\u0437\u0430')),
                ('status', models.CharField(default='posted', verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', max_length=255, editable=False, choices=[('posted', '\u0420\u0430\u0437\u043c\u0435\u0449\u0435\u043d'), ('accepted', '\u041f\u0440\u0438\u043d\u044f\u0442'), ('advanced', '\u0412\u044b\u043f\u043b\u0430\u0447\u0435\u043d \u0430\u0432\u0430\u043d\u0441'), ('paid', '\u041e\u043f\u043b\u0430\u0447\u0435\u043d'), ('done', '\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d')])),
                ('applicant_approved', models.NullBooleanField(verbose_name='\u041e\u0434\u043e\u0431\u0440\u0435\u043d\u043e \u0437\u0430\u043a\u0430\u0437\u0447\u0438\u043a\u043e\u043c', editable=False)),
                ('title', models.CharField(default='', verbose_name='\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u043e\u043a\u0443\u043f\u0430\u0442\u0435\u043b\u044f', max_length=255, editable=False)),
                ('phones', models.TextField(verbose_name='\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u044b', null=True, editable=False)),
                ('dt_due', models.DateField(verbose_name='\u0414\u0430\u0442\u0430 \u043f\u043e\u0445\u043e\u0440\u043e\u043d', null=True, editable=False)),
                ('burial_plan_time', models.TimeField(verbose_name='\u041f\u043b\u0430\u043d. \u0432\u0440\u0435\u043c\u044f \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f', null=True, editable=False)),
                ('initial_place', models.CharField(default='', verbose_name='\u041c\u0435\u0441\u0442\u043e \u043f\u043e\u0434\u0430\u0447\u0438 \u043a\u0430\u0442\u0430\u0444\u0430\u043b\u043a\u0430', max_length=255, editable=False)),
                ('initial_time', models.TimeField(verbose_name='\u0412\u0440\u0435\u043c\u044f \u043f\u043e\u0434\u0430\u0447\u0438 \u043a\u0430\u0442\u0430\u0444\u0430\u043b\u043a\u0430', null=True, editable=False)),
                ('service_place', models.CharField(default='', verbose_name='\u041c\u0435\u0441\u0442\u043e \u043e\u0442\u043f\u0435\u0432\u0430\u043d\u0438\u044f', max_length=255, editable=False)),
                ('service_time', models.TimeField(verbose_name='\u0412\u0440\u0435\u043c\u044f \u043e\u0442\u043f\u0435\u0432\u0430\u043d\u0438\u044f', null=True, editable=False)),
                ('repast_place', models.CharField(default='', verbose_name='\u041c\u0435\u0441\u0442\u043e \u043e\u0442\u043f\u0435\u0432\u0430\u043d\u0438\u044f', max_length=255, editable=False)),
                ('repast_time', models.TimeField(verbose_name='\u0412\u0440\u0435\u043c\u044f \u043e\u0442\u043f\u0435\u0432\u0430\u043d\u0438\u044f', null=True, editable=False)),
            ],
            options={
                'verbose_name': '\u0417\u0430\u043a\u0430\u0437',
                'verbose_name_plural': '\u0417\u0430\u043a\u0430\u0437\u044b',
            },
            bases=(pd.models.GetLogsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='OrderComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('type', models.CharField(default='shared', max_length=255, verbose_name='\u0422\u0438\u043f', choices=[('private', '\u041b\u0438\u0447\u043d\u044b\u0439'), ('shared', '\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0439 \u0430\u0432\u0442\u043e\u0440\u0443 \u0438 \u0441\u043e\u0431\u0435\u0441\u0435\u0434\u043d\u0438\u043a\u0443'), ('public', '\u041e\u0431\u0449\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0439')])),
                ('comment', models.TextField(verbose_name='\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.DecimalField(default=1, verbose_name='\u041a\u043e\u043b-\u0432\u043e', max_digits=20, decimal_places=2)),
                ('cost', models.DecimalField(verbose_name='\u0426\u0435\u043d\u0430', max_digits=20, decimal_places=2)),
                ('discount', models.DecimalField(default='0.00', verbose_name='\u0421\u043a\u0438\u0434\u043a\u0430', editable=False, max_digits=4, decimal_places=2)),
                ('name', models.CharField(verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435', max_length=255, editable=False)),
                ('measure', models.CharField(default='\u0448\u0442', max_length=255, verbose_name='\u0415\u0434. \u0438\u0437\u043c.')),
                ('description', models.TextField(default='', verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('productcategory_name', models.CharField(verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438', max_length=255, editable=False)),
                ('productgroup_name', models.CharField(default='', verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043f\u043e\u0434\u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438', max_length=255, editable=False)),
                ('productgroup_description', models.TextField(default='', verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u043f\u043e\u0434\u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438', editable=False, blank=True)),
                ('comment', models.TextField(default='', verbose_name='\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439', editable=False, blank=True)),
                ('is_wholesale_with_vat', models.BooleanField(default=False, verbose_name='\u0426\u0435\u043d\u0430 \u0441 \u041d\u0414\u0421', editable=False)),
            ],
            options={
                'verbose_name': '\u041f\u043e\u0437\u0438\u0446\u0438\u044f',
                'verbose_name_plural': '\u041f\u043e\u0437\u0438\u0446\u0438\u0438',
            },
            bases=(orders.models.OrderItemMixin, models.Model),
        ),
        migrations.CreateModel(
            name='OrderWebPay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('wsb_order_num', models.CharField(max_length=255, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0437\u0430\u043a\u0430\u0437\u0430', db_index=True)),
                ('transaction_id', models.CharField(max_length=255, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0442\u0440\u0430\u043d\u0437\u0430\u043a\u0446\u0438\u0438')),
                ('batch_timestamp', models.CharField(max_length=255, null=True, verbose_name='\u0412\u0440\u0435\u043c\u044f \u0441\u043e\u0432\u0435\u0440\u0448\u0435\u043d\u0438\u044f \u0442\u0440\u0430\u043d\u0437\u0430\u043a\u0446\u0438\u0438')),
                ('currency_id', models.CharField(max_length=255, null=True, verbose_name='\u041a\u043e\u0434 \u0432\u0430\u043b\u044e\u0442\u044b \u0441\u043e\u0433\u043b\u0430\u0441\u043d\u043e ISO4271')),
                ('amount', models.CharField(max_length=255, null=True, verbose_name='\u0421\u0443\u043c\u043c\u0430')),
                ('payment_method', models.CharField(max_length=255, null=True, verbose_name='\u041c\u0435\u0442\u043e\u0434 \u043f\u043b\u0430\u0442\u0435\u0436\u0430', choices=[('test', '\u0422\u0435\u0441\u0442, \u0431\u0435\u0437 \u0440\u0435\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u043f\u043b\u0430\u0442\u0435\u0436\u0430'), ('cc', '\u041f\u043b\u0430\u0442\u0435\u0436\u043d\u0430\u044f \u043a\u0430\u0440\u0442\u043e\u0447\u043a\u0430')])),
                ('payment_type', models.CharField(max_length=255, null=True, verbose_name='\u0422\u0438\u043f \u0442\u0440\u0430\u043d\u0437\u0430\u043a\u0446\u0438\u0438', choices=[('1', 'Completed (\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043d\u0430\u044f)'), ('2', 'Declined (\u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u043d\u0430\u044f)'), ('3', 'Pending (\u0412 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0435)'), ('4', 'Authorized (\u0410\u0432\u0442\u043e\u0440\u0438\u0437\u043e\u0432\u0430\u043d\u043d\u0430\u044f)'), ('5', 'Refunded (\u0412\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u043d\u0430\u044f)'), ('6', 'System (\u0421\u0438\u0441\u0442\u0435\u043c\u043d\u0430\u044f))'), ('7', 'Voided (\u0421\u0431\u0440\u043e\u0448\u0435\u043d\u043d\u0430\u044f \u043f\u043e\u0441\u043b\u0435 \u0430\u0432\u0442\u043e\u0440\u0438\u0437\u0430\u0446\u0438\u0438)'), ('8', 'Failed (\u041e\u0448\u0438\u0431\u043a\u0430 \u0432 \u043f\u0440\u043e\u0432\u0435\u0434\u0435\u043d\u0438\u0438 \u0442\u0440\u0430\u043d\u0437\u0430\u043a\u0446\u0438\u0438)')])),
                ('order_ident', models.CharField(max_length=255, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0437\u0430\u043a\u0430\u0437\u0430 \u0432 \u0441\u0438\u0441\u0442\u0435\u043c\u0435 WebPay (order_id)')),
                ('rrn', models.CharField(max_length=255, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0442\u0440\u0430\u043d\u0437\u0430\u043a\u0446\u0438\u0438 \u0432 \u0441\u0438\u0441\u0442\u0435\u043c\u0435 Visa/MasterCard')),
                ('wsb_signature', models.CharField(max_length=255, null=True, verbose_name='\u042d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u0430\u044f \u043f\u043e\u0434\u043f\u0438\u0441\u044c')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrgService',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=True, verbose_name='\u0412\u043a\u043b\u044e\u0447\u0435\u043d')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrgServicePrice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('price', models.DecimalField(default='0.00', verbose_name='\u0426\u0435\u043d\u0430', max_digits=20, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('slug', autoslug.fields.AutoSlugField(null=True, editable=False, populate_from='name', max_length=255, always_update=True, unique=True)),
                ('description', models.TextField(default='', verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('measure', models.CharField(default='\u0448\u0442', max_length=255, verbose_name='\u0415\u0434. \u0438\u0437\u043c.')),
                ('price', models.DecimalField(verbose_name='\u0426\u0435\u043d\u0430 \u0440\u043e\u0437\u043d\u0438\u0447\u043d\u0430\u044f', max_digits=20, decimal_places=2)),
                ('price_wholesale', models.DecimalField(verbose_name='\u0426\u0435\u043d\u0430 \u043e\u043f\u0442\u043e\u0432\u0430\u044f', max_digits=20, decimal_places=2)),
                ('ptype', models.CharField(blank=True, max_length=255, null=True, verbose_name='\u0422\u0438\u043f', choices=[('catafalque', '\u0410\u0432\u0442\u043e\u043a\u0430\u0442\u0430\u0444\u0430\u043b\u043a'), ('catafalque_comfort', '\u041a\u0430\u0442\u0430\u0444\u0430\u043b\u043a \u043f\u043e\u0432\u044b\u0448. \u043a\u043e\u043c\u0444\u043e\u0440\u0442\u043d\u043e\u0441\u0442\u0438'), ('loaders', '\u0413\u0440\u0443\u0437\u0447\u0438\u043a\u0438'), ('diggers', '\u0420\u044b\u0442\u044c\u0435 \u043c\u043e\u0433\u0438\u043b\u044b'), ('SIGN', '\u041d\u0430\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u043d\u0430\u0434\u043c\u043e\u0433\u0438\u043b\u044c\u043d\u043e\u0439 \u0442\u0430\u0431\u043b\u0438\u0447\u043a\u0438'), ('VIP', '\u0412\u0418\u041f \u0431\u0440\u0438\u0433\u0430\u0434\u0430 \u043f\u043e\u0441\u043b\u0435\u043f\u043e\u0445\u043e\u0440\u043e\u043d\u043d\u043e\u0433\u043e \u043e\u0431\u0441\u043b\u0443\u0436\u0438\u0432\u0430\u043d\u0438\u044f')])),
                ('default', models.BooleanField(default=False, verbose_name='\u041f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e')),
                ('stockable', models.BooleanField(default=True, verbose_name='\u0422\u043e\u0432\u0430\u0440')),
                ('photo', models.ImageField(max_length=255, upload_to=pd.models.upload_slugified, null=True, verbose_name='\u0424\u043e\u0442\u043e', blank=True)),
                ('sku', models.CharField(default='', max_length=255, verbose_name='\u0410\u0440\u0442\u0438\u043a\u0443\u043b', blank=True)),
                ('is_public_catalog', models.BooleanField(default=False, verbose_name='\u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u0432 \u043f\u0443\u0431\u043b\u0438\u0447\u043d\u043e\u043c \u043a\u0430\u0442\u0430\u043b\u043e\u0433\u0435')),
                ('is_wholesale', models.BooleanField(default=False, verbose_name='\u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u0432 \u043a\u0430\u0442\u0430\u043b\u043e\u0433\u0435 \u043e\u043f\u0442\u043e\u0432\u0438\u043a\u0430\u043c')),
                ('is_for_visit', models.BooleanField(default=False, verbose_name='\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u043e \u0434\u043b\u044f \u043f\u043e\u0441\u0435\u0449\u0435\u043d\u0438\u044f \u043c\u0435\u0441\u0442\u0430 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u044f')),
                ('is_archived', models.BooleanField(default=False, verbose_name='\u0410\u0440\u0445\u0438\u0432\u0438\u0440\u043e\u0432\u0430\u043d')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': '\u0422\u043e\u0432\u0430\u0440',
                'verbose_name_plural': '\u0422\u043e\u0432\u0430\u0440\u044b',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('sorting', models.CharField(default='ZZ', verbose_name='\u041f\u043e\u0440\u044f\u0434\u043e\u043a \u0441\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u043a\u0438', max_length=2, editable=False)),
                ('icon', models.ImageField(upload_to=pd.models.upload_slugified, null=True, verbose_name='\u0418\u043a\u043e\u043d\u043a\u0430', blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': '\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f',
                'verbose_name_plural': '\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('description', models.TextField(default='', verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('icon', models.FileField(upload_to=pd.models.upload_slugified, null=True, verbose_name='\u0418\u043a\u043e\u043d\u043a\u0430', blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': '\u041f\u043e\u0434\u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f',
                'verbose_name_plural': '\u041f\u043e\u0434\u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResultFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('type', models.CharField(default='image', max_length=255, verbose_name='\u0422\u0438\u043f', choices=[('image', '\u0418\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435'), ('video', '\u0412\u0438\u0434\u0435\u043e')])),
                ('is_title', models.BooleanField(default=False, verbose_name='\u0422\u0438\u0442\u0443\u043b\u044c\u043d\u043e\u0435 \u0444\u043e\u0442\u043e', editable=False)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('order', models.ForeignKey(verbose_name='\u0417\u0430\u043a\u0430\u0437', to='orders.Order', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.PositiveIntegerField(verbose_name='\u041f\u043e\u0440\u044f\u0434\u043e\u043a \u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u044f \u0442\u043e\u0447\u0435\u043a, \u043d\u0430\u0447\u0438\u043d\u0430\u044f \u0441 0')),
                ('lat', models.FloatField(verbose_name='\u0428\u0438\u0440\u043e\u0442\u0430')),
                ('lng', models.FloatField(verbose_name='\u0414\u043e\u043b\u0433\u043e\u0442\u0430')),
                ('order', models.ForeignKey(to='orders.Order', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('title', models.CharField(max_length=255, verbose_name='\u0417\u0430\u0433\u043b\u0430\u0432\u0438\u0435')),
                ('description', models.TextField(default='', verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServiceItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cost', models.DecimalField(verbose_name='\u0426\u0435\u043d\u0430', max_digits=20, decimal_places=2)),
                ('order', models.ForeignKey(to='orders.Order', on_delete=models.CASCADE)),
                ('orgservice', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='\u0423\u0441\u043b\u0443\u0433\u0430', to='orders.OrgService')),
            ],
            options={
            },
            bases=(orders.models.OrderItemMixin, models.Model),
        ),
        migrations.AlterUniqueTogether(
            name='route',
            unique_together=set([('order', 'index')]),
        ),
    ]
