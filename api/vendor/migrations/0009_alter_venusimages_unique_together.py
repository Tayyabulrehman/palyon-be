# Generated by Django 4.2.13 on 2024-09-14 14:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0008_venue_type'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='venusimages',
            unique_together=set(),
        ),
    ]
