from enum import Enum

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
from django.db.models import Q, F

from api import users
from api.users.models import User
from main.models import Log


class Vendor(User):
    # meta_data = models.OneToOneField('users.User', on_delete=models.CASCADE, null=True, related_name='user_vendor')
    business_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    image = models.ImageField(null=True, upload_to='vendor-profile/')

    class Meta:
        db_table = 'vendor'

    def __str__(self):
        return self.business_name


class Venue(Log):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, related_name='vendor_grounds', )
    name = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)
    latitude = models.FloatField(null=True, )
    longitude = models.FloatField(null=True)
    price = models.FloatField(default=0.0)
    active = models.BooleanField(default=True)
    description = models.TextField(null=True)
    type = ArrayField(base_field=models.CharField(max_length=255), null=True)
    deleted = models.BooleanField(default=False)
    facilities = ArrayField(base_field=models.CharField(max_length=255), null=True)

    # loc = PointField(null=True)

    class Meta:
        db_table = 'venues'


class VenusImages(Log):
    venus = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='venue_images', null=True)
    image = models.ImageField(
        db_column='Image',
        null=True,
        upload_to="venue-images/"
    )
    is_featured = models.BooleanField(default=False)

    class Meta:
        db_table = 'venue_images'
        # unique_together = ["venus", "is_featured"]


class WeekDay(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class Slots(Log):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, null=True, related_name='venue_slots', )
    day = models.IntegerField(default=WeekDay.MONDAY)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'slots'

    # @staticmethod
    # def check_unique_constraint(venue_id, start_time, end_time, day):
    #     return not Slots.objects \
    #         .filter(venue_id=venue_id, start_time__lt=end_time,end_time__gt=start_time, day=day, active=True)\
    #         .exists()

    def clean(self):
        # Ensure end_time is after start_time
        if self.end_time <= self.start_time:
            raise ValidationError(_('End time must be after start time.'))

        # Check for overlapping slots across the week
        overlapping_slots = Slots.objects.filter(
            venue=self.venue,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            day=self.day,

        ).exclude(id=self.pk)

        if overlapping_slots.exists():
            raise ValidationError(_('This time slot overlaps with another existing slot.'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
