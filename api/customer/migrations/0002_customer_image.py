# Generated by Django 4.2.13 on 2024-09-22 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='image',
            field=models.ImageField(null=True, upload_to=''),
        ),
    ]
