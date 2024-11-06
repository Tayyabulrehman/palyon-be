from django.db import models

# Create your models here.
from config.utils import combine_date_time, find_overlapping_intervals
from main.models import Log


class BookingStatusConst:
    pending = 'pending'
    confirmed = 'confirmed'
    cancelled = 'cancelled'
    # cancelled_by_customer = 'cancelled-by-customer'


class Booking(Log):
    venue = models.ForeignKey("vendor.Venue", on_delete=models.SET_NULL, related_name='venue_bookings', null=True)
    customer = models.ForeignKey("customer.Customer", on_delete=models.SET_NULL, related_name='customer_bookings',
                                 null=True)
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    amount = models.FloatField(default=0.0)

    class Meta:
        db_table = 'bookings'


class BookingSlots(Log):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_slots', null=True)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    date = models.DateField(null=True)
    slot = models.ForeignKey("vendor.Slots", on_delete=models.SET_NULL, related_name='slot_bookings', null=True)

    @classmethod
    def is_booking_already_exists(cls, slots: list) -> bool:
        if len(slots) > 1:
            slot_ids = [x.get("slot_id") for x in slots]
            dates =[x.get("date") for x in slots]

            booked_slots = cls.objects \
                .filter(slot_id__in=slot_ids,date__in=dates) \
                .exclude(booking__booking_status__status__in=[BookingStatusConst.cancelled, ]) \
                .values("start_time", "end_time", "date")

            booked_slots = combine_date_time(booked_slots)
            slots = combine_date_time(slots)
            overlap = find_overlapping_intervals(booked_slots, slots)
            return overlap

        else:
            slots = slots[0]
            return cls.objects.filter(
                slot_id=slots.get("slot_id"),
                start_time__lt=slots.get('end_time'),
                end_time__gt=slots.get('start_time'),
                date=slots.get('date'), ).exists()


class BookingStatus(Log):
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, related_name='booking_status', null=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=50, null=True)

    class Meta:
        db_table = 'booking_status'


class Reviews(Log):
    venue = models.ForeignKey("vendor.Venue", on_delete=models.SET_NULL, related_name='venue_reviews', null=True)
    customer = models.ForeignKey("customer.Customer", on_delete=models.SET_NULL, related_name='customer_reviews',
                                 null=True)
    rating = models.IntegerField(default=4)
    description = models.TextField(null=True)

    class Meta:
        db_table = 'reviews'
        unique_together = ['venue', 'customer']
