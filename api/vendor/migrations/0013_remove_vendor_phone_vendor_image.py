# Generated by Django 4.2.13 on 2024-12-07 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0012_venue_facilities_alter_venue_latitude_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vendor',
            name='phone',
        ),
        migrations.AddField(
            model_name='vendor',
            name='image',
            field=models.ImageField(null=True, upload_to='vendor-profile/'),
        ),
    ]
