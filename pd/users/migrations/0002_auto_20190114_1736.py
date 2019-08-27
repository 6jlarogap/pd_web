from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='org',
            name='email',
            field=models.EmailField(max_length=254, null=True, verbose_name='Email', blank=True),
        ),
        migrations.AlterField(
            model_name='registerprofile',
            name='user_email',
            field=models.EmailField(max_length=254, verbose_name='Email'),
        ),
    ]
