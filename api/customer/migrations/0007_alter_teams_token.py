# Generated by Django 4.2.13 on 2024-09-28 10:55

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0006_badges_active_alter_teams_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teams',
            name='token',
            field=models.UUIDField(default=uuid.UUID('4eea4d20-7874-4026-867d-e31158136340'), null=True),
        ),
    ]
