# Generated by Django 4.2.13 on 2024-08-28 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0002_venue_alter_vendor_table_venusimages_venue_vendor_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='slots',
            name='unique_timeslot_for_venue',
        ),
        migrations.AddConstraint(
            model_name='slots',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('start_time__gte', models.F('end_time')), _negated=True), models.Q(('end_time__lte', models.F('start_time')), _negated=True)), name='unique_timeslot_for_venue'),
        ),
    ]
