# Generated by Django 4.2.13 on 2024-08-28 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0005_remove_slots_unique_timeslot_for_venue_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='slots',
            name='unique_timeslot_for_venue',
        ),
        migrations.AddField(
            model_name='slots',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]