from django.db import models

# Create your models here.
from datetime import datetime, timedelta
from uuid import uuid4

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

# Create your models here.
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from oauth2_provider.models import AccessToken

from config.utils import parse_email, generate_otp
from main.models import Log


class AccessLevel:
    """
    Access levels for user roles.
    """
    VENDOR = 100
    CUSTOMER = 200
    SUPER_ADMIN = 300

    CUSTOMER_CODE = 'customer'
    VENDOR_CODE = 'vendor'
    SUPER_ADMIN_CODE = 'super-admin'

    CHOICES = (
        (CUSTOMER, "Customer"),
        (SUPER_ADMIN, 'Super Admin'),
        (VENDOR, 'Vendor'),
    )

    CODES = (
        (CUSTOMER, "customer"),
        (SUPER_ADMIN, 'super-admin'),
        (VENDOR, 'vendor')
    )
    DICT = dict(CHOICES)
    CODES_DICT = dict(CODES)


class Role(Log):
    """ Role model."""
    name = models.CharField(db_column='Name', max_length=255, unique=True)
    code = models.SlugField(db_column='Code', default='')
    description = models.TextField(db_column='Description', null=True, blank=True)
    access_level = models.IntegerField(db_column='AccessLevel', choices=AccessLevel.CHOICES,
                                       default=AccessLevel.VENDOR)

    class Meta:
        db_table = 'Roles'

    def __str__(self):
        return f'{self.name}'

    def save(self, *args, **kwargs):
        try:
            if not self.pk:
                self.code = slugify(self.name)
            super().save()
        except Exception:
            raise

    @staticmethod
    def get_role_by_code(code=None):
        try:
            return Role.objects.get(code__exact=code)
        except Exception as e:
            print(e)
            return e


class CustomAccountManager(BaseUserManager):

    def create_user(self, email, password):
        user = self.model(email=email, password=password)
        passw = password
        user.set_password(passw)
        user.is_superuser = False
        user.is_approved = False
        user.is_active = False
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email=email, password=password)
        passw = password
        user.set_password(passw)
        user.is_superuser = True
        user.is_approved = True
        user.is_active = True
        user.role = Role.objects.get(code=AccessLevel.SUPER_ADMIN_CODE)
        # Group.objects.get_or_create(name='Super_Admin')
        # user.groups.add(Super_Admin)
        user.save()
        return user





class User(AbstractBaseUser, Log, PermissionsMixin):
    """ User model."""
    first_name = models.TextField(db_column='FirstName', default="")
    last_name = models.TextField(db_column='LastName', default="")
    is_active = models.BooleanField(
        db_column='IsActive',
        default=False,
        help_text='Designates whether this user should be treated as active. '
                  'Unselect this instead of deleting accounts.',
    )
    is_approved = models.BooleanField(
        db_column='IsApproved',
        default=True,
        help_text='Designates whether this user is approved or not.',
    )
    email = models.EmailField(unique=True, db_column="Email", help_text="Email Field")
    username = models.CharField(default=None, db_column="Username", null=True, blank=True, max_length=255)
    is_email_verified = models.BooleanField(db_column='IsEmailVerified', default=False)
    role = models.ForeignKey(Role, db_column='RoleId', related_name='user_role', on_delete=models.CASCADE,
                             default=None,
                             null=True, blank=True)
    is_staff = models.BooleanField(
        default=True,
        help_text='Designates whether the user can log into this admin site.',
    )
    is_deleted = models.BooleanField(
        default=False,
        db_column='IsDeleted'
    )
    fcm =models.TextField(null=True)
    objects = CustomAccountManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    class Meta:
        db_table = 'Users'

    def save(self, *args, **kwargs):
        try:
            if not self.pk:
                self.email = parse_email(self.email)
            super().save()
        except Exception:
            raise

    def delete_account(self, assigned_to=None):
        self.status = self.is_active = False
        self.is_deleted = True
        self.email = f"{self.email}__{self.id}__{get_random_string(6)}"
        self.password = get_random_string(6)
        AccessToken.objects.filter(user_id=self.id).delete()
        self.save()


class EmailVerificationLink(Log):
    token = models.CharField(db_column='Token', primary_key=True, unique=True, max_length=255)
    code = models.IntegerField(db_column="Code", null=True, blank=True, default=None)
    user = models.ForeignKey(User, db_column='UserId', related_name='user_email_verification', on_delete=models.CASCADE)
    expiry_at = models.DateTimeField(db_column="ExpireDate", null=True, default=None)
    # expiry_time = models.TimeField(db_column='ExpireTime', null=True, default=None)

    class Meta:
        db_table = "Email_Verification"

    def save(self, *args, **kwargs):
        try:
            if not self.pk:
                self.token = uuid4()
            super().save()
        except Exception:
            raise

    @classmethod
    def generate_verification_code(cls, user, days=1, minutes=1):
        try:
            cls.objects.filter(user=user).delete()
            date = datetime.now()
            object = {}
            object["user"] = user
            object["expiry_at"]=date+timedelta(days=days)
            # object["expire_date"] = date.date() + timedelta(days)
            # object["expiry_time"] = (date + timedelta(minutes=minutes)).time()
            object['code'] = generate_otp()
            email_link = cls.objects.create(**object)
            return email_link
        except Exception as e:
            return e

    @staticmethod
    def add_email_token_link(user):
        try:
            object = {"user": user, "expiry_at": datetime.now() + timedelta(+5)}
            email_link = EmailVerificationLink.objects.create(**object)
            print(email_link)

            # send_email_sendgrid_template(
            #     from_email=settings.CONTACT_US_EMAIL,
            #     to_email=user.email,
            #     subject="Forgot Password",
            #     data=data,
            #     template=settings.FORGOT_PASSWORD_TEMPLATE_ID
            # )
            return email_link
        except Exception as e:
            return e