# Generated by Django 4.2.13 on 2024-09-14 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0009_alter_venusimages_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='venue',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='venue',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
