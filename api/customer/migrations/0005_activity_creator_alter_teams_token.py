# Generated by Django 4.2.13 on 2024-09-26 09:11

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0004_teams_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='creator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='customer_activity', to='customer.customer'),
        ),
        migrations.AlterField(
            model_name='teams',
            name='token',
            field=models.UUIDField(default=uuid.UUID('f658b84e-245f-4998-9cc0-d1302d472e60'), null=True),
        ),
    ]
