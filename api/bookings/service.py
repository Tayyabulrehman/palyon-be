import os
from abc import ABC, abstractmethod
from functools import reduce

from django.db import transaction

from api.bookings.messages_content import get_push_notification_content, MsgTyp
from api.bookings.models import Booking, BookingSlots
from api.vendor.models import Venue
from config.tasks import cancel_booking, async_push_notification
from config.utils import calaculate_hours


class BookingsBuilder(ABC):
    def __init__(self, validated_data):
        self.data = validated_data
        self.booking = None
        self.slot = None

    def checking_slot_availability(self):
        if BookingSlots.is_booking_already_exists(
                slots=self.data.get('slots')
        ):
            raise ValueError("Booking already exists")

    def calculate_total_amount(self):
        id = self.data.get("slots")[0]["slot_id"]
        venue = Venue.objects.filter(venue_slots__id=id).first()
        total_hours = calaculate_hours(self.data.get("slots"))
        self.data["amount"] = venue.price * total_hours
        self.data["venue_id"] = venue.id

    def create(self):
        # with transaction.atomic():
        slots = self.data.pop("slots")
        booking = Booking.objects.create(**self.data)
        booking.booking_slots.bulk_create([BookingSlots(booking=booking, **x) for x in slots])
        # booking.booking_status.create(status='pending')
        self.booking = booking
        return self.booking

    @abstractmethod
    def notify(self):
        pass

    def build(self):
        self.checking_slot_availability()
        self.calculate_total_amount()
        self.create()
        # self.notify()
        return self.booking


class CustomerBookingBuilder(BookingsBuilder):

    def create(self):
        with transaction.atomic():
            booking = super().create()
            booking.booking_status.create(status='pending')
            transaction.on_commit(self.notify)
            cancel_booking.apply_async(args=[booking.id], countdown=int(eval(os.getenv("BOOKING_DELETE_COUNT_DOWN"))))

    def notify(self):
        args = {
            "name": self.booking.venue.name,
        }
        title, body = get_push_notification_content(MsgTyp.booking_created, **args)
        fcm = self.booking.customer.fcm
        async_push_notification(title, body, fcm, data={})


class VendorBookingBuilder(BookingsBuilder):

    def create(self):
        booking = super().create()
        booking.booking_status.create(status='confirmed')

    def notify(self):
        pass
