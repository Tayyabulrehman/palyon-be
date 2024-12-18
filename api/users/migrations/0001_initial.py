# Generated by Django 4.2.13 on 2024-08-26 18:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('created_by', models.BigIntegerField(blank=True, db_column='CreatedBy', default=0, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, db_column='CreatedOn')),
                ('modified_by', models.BigIntegerField(blank=True, db_column='ModifiedBy', default=0, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, db_column='ModifiedOn')),
                ('first_name', models.TextField(db_column='FirstName', default='')),
                ('last_name', models.TextField(db_column='LastName', default='')),
                ('is_active', models.BooleanField(db_column='IsActive', default=False, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')),
                ('is_approved', models.BooleanField(db_column='IsApproved', default=True, help_text='Designates whether this user is approved or not.')),
                ('email', models.EmailField(db_column='Email', help_text='Email Field', max_length=254, unique=True)),
                ('username', models.CharField(blank=True, db_column='Username', default=None, max_length=255, null=True)),
                ('is_email_verified', models.BooleanField(db_column='IsEmailVerified', default=False)),
                ('is_staff', models.BooleanField(default=True, help_text='Designates whether the user can log into this admin site.')),
                ('is_deleted', models.BooleanField(db_column='IsDeleted', default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
            ],
            options={
                'db_table': 'Users',
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.BigIntegerField(blank=True, db_column='CreatedBy', default=0, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, db_column='CreatedOn')),
                ('modified_by', models.BigIntegerField(blank=True, db_column='ModifiedBy', default=0, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, db_column='ModifiedOn')),
                ('name', models.CharField(db_column='Name', max_length=255, unique=True)),
                ('code', models.SlugField(db_column='Code', default='')),
                ('description', models.TextField(blank=True, db_column='Description', null=True)),
                ('access_level', models.IntegerField(choices=[(200, 'Customer'), (300, 'Super Admin'), (100, 'Vendor')], db_column='AccessLevel', default=100)),
            ],
            options={
                'db_table': 'Roles',
            },
        ),
        migrations.CreateModel(
            name='EmailVerificationLink',
            fields=[
                ('created_by', models.BigIntegerField(blank=True, db_column='CreatedBy', default=0, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, db_column='CreatedOn')),
                ('modified_by', models.BigIntegerField(blank=True, db_column='ModifiedBy', default=0, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, db_column='ModifiedOn')),
                ('token', models.CharField(db_column='Token', max_length=255, primary_key=True, serialize=False, unique=True)),
                ('code', models.IntegerField(blank=True, db_column='Code', default=None, null=True)),
                ('expiry_at', models.DateTimeField(db_column='ExpireDate', default=None, null=True)),
                ('user', models.ForeignKey(db_column='UserId', on_delete=django.db.models.deletion.CASCADE, related_name='user_email_verification', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'Email_Verification',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.ForeignKey(blank=True, db_column='RoleId', default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_role', to='users.role'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
    ]
