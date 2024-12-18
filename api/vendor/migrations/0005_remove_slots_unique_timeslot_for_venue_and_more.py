# Generated by Django 4.2.13 on 2024-08-28 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0004_remove_slots_unique_timeslot_for_venue_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='slots',
            name='unique_timeslot_for_venue',
        ),
        migrations.AddConstraint(
            model_name='slots',
            constraint=models.CheckConstraint(check=models.Q(('start_time__lte', models.F('end_time')), ('end_time__gte', models.F('start_time'))), name='unique_timeslot_for_venue'),
        ),
    ]
