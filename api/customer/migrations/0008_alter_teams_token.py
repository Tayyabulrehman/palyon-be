# Generated by Django 4.2.13 on 2024-10-12 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0007_alter_teams_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teams',
            name='token',
            field=models.UUIDField(null=True),
        ),
    ]
