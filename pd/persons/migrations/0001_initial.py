from django.db import models, migrations
import geo.models
import users.models
import pd.models
import django.db.models.deletion
from django.conf import settings
import persons.models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BasePerson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_name', models.CharField(max_length=255, verbose_name='\u0424\u0430\u043c\u0438\u043b\u0438\u044f', blank=True)),
                ('first_name', models.CharField(max_length=255, verbose_name='\u0418\u043c\u044f', blank=True)),
                ('middle_name', models.CharField(max_length=255, verbose_name='\u041e\u0442\u0447\u0435\u0441\u0442\u0432\u043e', blank=True)),
                ('birth_date_no_month', models.BooleanField(default=False, editable=False)),
                ('birth_date_no_day', models.BooleanField(default=False, editable=False)),
                ('birth_date', pd.models.UnclearDateModelField(serialize=False, null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f', blank=True)),
                ('ident_number', models.CharField(max_length=255, verbose_name='\u0418\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u043e\u043d\u043d\u044b\u0439 \u043d\u043e\u043c\u0435\u0440', blank=True)),
            ],
            options={
                'ordering': ['last_name', 'first_name', 'middle_name'],
                'verbose_name': '\u0444\u0438\u0437. \u043b\u0438\u0446\u043e',
                'verbose_name_plural': '\u0444\u0438\u0437. \u043b\u0438\u0446\u0430',
            },
            bases=(persons.models.PersonMixin, models.Model),
        ),
        migrations.CreateModel(
            name='AlivePerson',
            fields=[
                ('baseperson_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='persons.BasePerson', on_delete=models.CASCADE)),
                ('phones', models.TextField(null=True, verbose_name='\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u044b (\u0435\u0441\u043b\u0438 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u043e, \u0442\u043e \u0447\u0435\u0440\u0435\u0437 ; \u0438\u043b\u0438 ,)', blank=True)),
                ('login_phone', models.DecimalField(decimal_places=0, validators=[pd.models.validate_phone_as_number], editable=False, max_digits=15, blank=True, help_text='\u0412 \u043c\u0435\u0436\u0434\u0443\u043d\u0430\u0440\u043e\u0434\u043d\u043e\u043c \u0444\u043e\u0440\u043c\u0430\u0442\u0435, \u043d\u0430\u0447\u0438\u043d\u0430\u044f \u0441 \u043a\u043e\u0434\u0430 \u0441\u0442\u0440\u0430\u043d\u044b, \u0431\u0435\u0437 "+", \u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440 79101234567', null=True, verbose_name='\u041c\u043e\u0431\u0438\u043b\u044c\u043d\u044b\u0439 \u0442\u0435\u043b\u0435\u0444\u043e\u043d \u0434\u043b\u044f \u0432\u0445\u043e\u0434\u0430 \u0432 \u043a\u0430\u0431\u0438\u043d\u0435\u0442', db_index=True)),
                ('is_inbook', models.BooleanField(default=False, verbose_name='\u0421\u0434\u0435\u043b\u0430\u043d\u0430 \u043e\u0442\u043c\u0435\u0442\u043a\u0430 \u043e\u0431 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u043c \u0432 \u0436\u0443\u0440\u043d\u0430\u043b\u0435 \u0437\u0430\u0445\u043e\u0440\u043e\u043d\u0435\u043d\u0438\u0439 (\u0431\u0443\u043c\u0430\u0436\u043d\u043e\u043c!)', editable=False)),
            ],
            options={
            },
            bases=('persons.baseperson', users.models.PhonesMixin),
        ),
        migrations.CreateModel(
            name='CustomPerson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('photo', models.ImageField(max_length=255, upload_to=pd.models.files_upload_to, null=True, verbose_name='\u0424\u043e\u0442\u043e', blank=True)),
                ('original_filename', models.CharField(max_length=255, null=True, editable=False)),
                ('last_name', models.CharField(max_length=255, verbose_name='\u0424\u0430\u043c\u0438\u043b\u0438\u044f', blank=True)),
                ('first_name', models.CharField(max_length=255, verbose_name='\u0418\u043c\u044f', blank=True)),
                ('middle_name', models.CharField(max_length=255, verbose_name='\u041e\u0442\u0447\u0435\u0441\u0442\u0432\u043e', blank=True)),
                ('birth_date_no_month', models.BooleanField(default=False, editable=False)),
                ('birth_date_no_day', models.BooleanField(default=False, editable=False)),
                ('birth_date', pd.models.UnclearDateModelField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f', blank=True)),
                ('death_date_no_month', models.BooleanField(default=False, editable=False)),
                ('death_date_no_day', models.BooleanField(default=False, editable=False)),
                ('death_date', pd.models.UnclearDateModelField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0441\u043c\u0435\u0440\u0442\u0438', blank=True)),
                ('is_dead', models.BooleanField(default=True, verbose_name='\u0423c\u043e\u043f\u0448\u0438\u0439')),
                ('memory_text', models.TextField(null=True, verbose_name='\u041f\u0430\u043c\u044f\u0442\u043d\u044b\u0439 \u0442\u0435\u043a\u0441\u0442')),
                ('permission', models.CharField(default='private', max_length=255, verbose_name='\u0420\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u0438\u0435', choices=[('private', '\u041b\u0438\u0447\u043d\u043e\u0435'), ('public', '\u0412 \u043f\u0443\u0431\u043b\u0438\u0447\u043d\u043e\u043c \u0434\u043e\u0441\u0442\u0443\u043f\u0435'), ('selected', '\u0412\u044b\u0431\u043e\u0440\u043e\u0447\u043d\u043e')])),
                ('token', models.CharField(verbose_name='\u0422\u043e\u043a\u0435\u043d', max_length=255, unique=True, null=True, editable=False)),
                ('thank_site', models.URLField(verbose_name='\u0421\u0430\u0439\u0442 \u0434\u043b\u044f \u0431\u043b\u0430\u0433\u043e\u0434\u0430\u0440\u043d\u043e\u0441\u0442\u0435\u0439', null=True, editable=False)),
            ],
            options={
                'ordering': ('last_name', 'first_name', 'middle_name'),
            },
            bases=(persons.models.PersonMixin, pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='CustomPersonPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75, null=True, verbose_name='Email')),
                ('login_phone', models.DecimalField(null=True, verbose_name='\u041c\u043e\u0431\u0438\u043b\u044c\u043d\u044b\u0439 \u0442\u0435\u043b\u0435\u0444\u043e\u043d \u0434\u043b\u044f \u0432\u0445\u043e\u0434\u0430 \u0432 \u043a\u0430\u0431\u0438\u043d\u0435\u0442', max_digits=15, decimal_places=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomPlace',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('name', models.CharField(max_length=255, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435', blank=True)),
                ('title_photo', models.ImageField(upload_to='.', null=True, verbose_name='\u041e\u0441\u043d\u043e\u0432\u043d\u043e\u0435 \u0424\u043e\u0442\u043e')),
                ('comment', models.TextField(null=True, verbose_name='\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439')),
            ],
            options={
            },
            bases=(geo.models.LocationMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DeadPerson',
            fields=[
                ('baseperson_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='persons.BasePerson', on_delete=models.CASCADE)),
                ('death_date_no_month', models.BooleanField(default=False, editable=False)),
                ('death_date_no_day', models.BooleanField(default=False, editable=False)),
                ('death_date', pd.models.UnclearDateModelField(serialize=False, null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0441\u043c\u0435\u0440\u0442\u0438', blank=True)),
            ],
            options={
            },
            bases=(persons.models.DeadPersonMixin, 'persons.baseperson'),
        ),
        migrations.CreateModel(
            name='DeathCertificate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('type', models.CharField(default='zags', max_length=255, verbose_name='\u0422\u0438\u043f', choices=[('zags', '\u0421\u0432\u0438\u0434\u0435\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u043e \u043e \u0441\u043c\u0435\u0440\u0442\u0438'), ('medic', '\u041c\u0435\u0434\u0438\u0446\u0438\u043d\u0441\u043a\u0430\u044f \u0441\u043f\u0440\u0430\u0432\u043a\u0430')])),
                ('s_number', models.CharField(max_length=255, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440', blank=True)),
                ('series', models.CharField(max_length=255, null=True, verbose_name='\u0421\u0435\u0440\u0438\u044f', blank=True)),
                ('release_date', models.DateField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0432\u044b\u0434\u0430\u0447\u0438', blank=True)),
                ('person', models.OneToOneField(to='persons.DeadPerson', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': '\u0441\u0432\u0438\u0434\u0435\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u043e \u043e \u0441\u043c\u0435\u0440\u0442\u0438',
                'verbose_name_plural': '\u0441\u0432\u0438\u0434\u0435\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u0430 \u043e \u0441\u043c\u0435\u0440\u0442\u0438',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DeathCertificateScan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('deathcertificate', models.OneToOneField(to='persons.DeathCertificate', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DocumentSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043e\u0440\u0433\u0430\u043d\u0430')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IDDocumentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='\u0422\u0438\u043f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430', db_index=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': '\u0442\u0438\u043f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430',
                'verbose_name_plural': '\u0442\u0438\u043f\u044b \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MemoryGallery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bfile', models.FileField(upload_to=pd.models.files_upload_to, max_length=255, verbose_name='\u0424\u0430\u0439\u043b', blank=True)),
                ('comment', models.CharField(max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('original_name', models.CharField(max_length=255, editable=False)),
                ('date_of_creation', models.DateTimeField(auto_now_add=True)),
                ('type', models.CharField(max_length=255, verbose_name='\u0422\u0438\u043f', choices=[('image', '\u0424\u043e\u0442\u043e'), ('video', '\u0412\u0438\u0434\u0435\u043e'), ('text', '\u0422\u0435\u043a\u0441\u0442'), ('link', '\u0421\u0441\u044b\u043b\u043a\u0430')])),
                ('text', models.TextField(null=True, verbose_name='\u0422\u0435\u043a\u0441\u0442')),
                ('event_date_no_month', models.BooleanField(default=False, editable=False)),
                ('event_date_no_day', models.BooleanField(default=False, editable=False)),
                ('event_date', pd.models.UnclearDateModelField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0441\u043e\u0431\u044b\u0442\u0438\u044f')),
                ('permission', models.CharField(default='private', max_length=255, verbose_name='\u0420\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u0438\u0435', choices=[('private', '\u041b\u0438\u0447\u043d\u043e\u0435'), ('public', '\u0412 \u043f\u0443\u0431\u043b\u0438\u0447\u043d\u043e\u043c \u0434\u043e\u0441\u0442\u0443\u043f\u0435'), ('selected', '\u0412\u044b\u0431\u043e\u0440\u043e\u0447\u043d\u043e')])),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u0442\u0435\u043b\u044c')),
                ('customperson', models.ForeignKey(to='persons.CustomPerson', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(pd.models.FilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='MemoryGalleryPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75, null=True, verbose_name='Email')),
                ('login_phone', models.DecimalField(null=True, verbose_name='\u041c\u043e\u0431\u0438\u043b\u044c\u043d\u044b\u0439 \u0442\u0435\u043b\u0435\u0444\u043e\u043d \u0434\u043b\u044f \u0432\u0445\u043e\u0434\u0430 \u0432 \u043a\u0430\u0431\u0438\u043d\u0435\u0442', max_digits=15, decimal_places=0)),
                ('memorygallery', models.ForeignKey(to='persons.MemoryGallery', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderDeadPerson',
            fields=[
                ('baseperson_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='persons.BasePerson', on_delete=models.CASCADE)),
                ('death_date_no_month', models.BooleanField(default=False, editable=False)),
                ('death_date_no_day', models.BooleanField(default=False, editable=False)),
                ('death_date', pd.models.UnclearDateModelField(serialize=False, null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0441\u043c\u0435\u0440\u0442\u0438', blank=True)),
                ('order', models.OneToOneField(verbose_name='\u0417\u0430\u043a\u0430\u0437', to='orders.Order', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(persons.models.DeadPersonMixin, 'persons.baseperson'),
        ),
        migrations.CreateModel(
            name='PersonID',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('series', models.CharField(max_length=255, null=True, verbose_name='\u0421\u0435\u0440\u0438\u044f', blank=True)),
                ('number', models.CharField(max_length=255, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440', blank=True)),
                ('date', models.DateField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0432\u044b\u0434\u0430\u0447\u0438', blank=True)),
                ('date_expire', models.DateField(null=True, verbose_name='\u0421\u0440\u043e\u043a \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f', blank=True)),
                ('id_type', models.ForeignKey(verbose_name='\u0422\u0438\u043f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430', blank=True, to='persons.IDDocumentType', null=True, on_delete=models.CASCADE)),
                ('person', models.OneToOneField(to='persons.BasePerson', on_delete=models.CASCADE)),
                ('source', models.ForeignKey(verbose_name='\u041a\u0435\u043c \u0432\u044b\u0434\u0430\u043d', blank=True, to='persons.DocumentSource', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': '\u0423\u0434\u043e\u0441\u0442\u043e\u0432\u0435\u0440\u0435\u043d\u0438\u0435 \u043b\u0438\u0447\u043d\u043e\u0441\u0442\u0438',
                'verbose_name_plural': '\u0423\u0434\u043e\u0441\u0442\u043e\u0432\u0435\u0440\u0435\u043d\u0438\u044f \u043b\u0438\u0447\u043d\u043e\u0441\u0442\u0438',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Phone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt_created', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('dt_modified', models.DateTimeField(auto_now=True, verbose_name='\u0414\u0430\u0442\u0430/\u0432\u0440\u0435\u043c\u044f \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438')),
                ('obj_id', models.PositiveIntegerField(db_index=True, verbose_name='ID \u043e\u0431\u044a\u0435\u043a\u0442\u0430', null=True, editable=False, blank=True)),
                ('number', models.CharField(max_length=50, verbose_name='\u041d\u043e\u043c\u0435\u0440', blank=True)),
                ('phonetype', models.SmallIntegerField(default=1, verbose_name='\u0422\u0438\u043f \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430', choices=[(0, '\u041c\u043e\u0431\u0438\u043b\u044c\u043d\u044b\u0439'), (1, '\u0413\u043e\u0440\u043e\u0434\u0441\u043a\u043e\u0439'), (2, '\u0424\u0430\u043a\u0441'), (3, '\u0418\u043d\u043e\u0439')])),
                ('ct', models.ForeignKey(blank=True, editable=False, to='contenttypes.ContentType', null=True, verbose_name='\u0422\u0438\u043f', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': '\u0442\u0435\u043b\u0435\u0444\u043e\u043d',
                'verbose_name_plural': '\u0422\u0435\u043b\u0435\u0444\u043e\u043d\u044b',
            },
            bases=(models.Model,),
        ),
    ]
