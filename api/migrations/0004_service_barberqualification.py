# Generated by Django 5.1.1 on 2024-10-01 12:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_barber_emergencycontactname_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Service Name')),
                ('price', models.FloatField(verbose_name='Service Price')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Service Description')),
                ('image', models.ImageField(blank=True, null=True, upload_to='service_images/', verbose_name='Service Image')),
                ('duration', models.CharField(max_length=50, verbose_name='Service Duration')),
                ('durationTime', models.TimeField(verbose_name='Service Duration Time')),
            ],
            options={
                'verbose_name': 'Service',
                'verbose_name_plural': 'Services',
            },
        ),
        migrations.CreateModel(
            name='BarberQualification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(help_text='The barber associated with this qualification.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User Account')),
                ('serviceId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.service', verbose_name='Service Name')),
            ],
            options={
                'verbose_name': 'Barber Qualification',
                'verbose_name_plural': 'Barber Qualifications',
            },
        ),
    ]
