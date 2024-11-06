# Generated by Django 4.2.13 on 2024-10-18 08:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0006_booking_venue'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookingslots',
            name='booking',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='booking_slots', to='bookings.booking'),
        ),
    ]