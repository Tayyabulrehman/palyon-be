from celery import shared_task
from django.apps import apps

from api.bookings.models import Booking


@shared_task()
def cancel_booking(booking_id):
    booking = apps.get_model("bookings", "Booking")
    booking = booking.objects.get(id=booking_id)
    if booking.booking_status.last().status == 'pending':
        booking.delete()

    # query = booking_status.objects.filter(booking_id=booking_id, is_active=True)
    # status = query.last()
    # if status.status == 'pending':
    #     query.update(is_active=False)
    #     booking_status.objects.create(status='cancelled',booking_id=booking_id)
