class MsgTyp:
    booking_created = 'booking-created'
    booking_confirmed = 'confirmed'
    booking_cancelled = 'cancelled'


def get_push_notification_content(typ, **kwargs):
    if MsgTyp.booking_created == typ:
        return "Booking Pending Confirmation", \
               f"Your booking for {kwargs.get('name')}   is created" \
               f" but not confirmed yet. Please complete the confirmation process to secure your spot"

    if MsgTyp.booking_confirmed == typ:
        return "Booking Confirmed", f"Great news! Your booking for {kwargs.get('name')} " \
               f" has been confirmed. Get ready to enjoy your session!"

    if MsgTyp.booking_cancelled == typ:
        return "Booking Canceled",\
            f"We're sorry to inform you that your booking for {kwargs.get('name')} " \
            f"  has been " \
            f"canceled. If you have any questions or need assistance, please contact us."
