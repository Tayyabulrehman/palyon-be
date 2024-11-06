import datetime

from api.bookings.models import BookingSlots
from api.vendor.models import Slots
from config.utils import generate_time_slots_with_object, generate_time_slots


class SlotsList:
    def __init__(self, venue_id, dat):
        self.venue_id = venue_id
        # self.day = day
        if isinstance(dat, str):
            dat = datetime.datetime.strptime(dat, "%Y-%m-%d")
        self.dat = dat

    def get_slots_dates(self):
        dates = {}

        query = Slots \
            .objects \
            .filter(venue_id=self.venue_id, day=self.dat.weekday() + 1, active=True) \
            .values("start_time", "end_time", "id")

        for x in query:
            y = generate_time_slots_with_object(
                start=x["start_time"],
                end=x["end_time"],
                data={"id": x["id"], "booked": False}
            )
            dates = {**dates, **y}

        return dates

    def get_booked_slots_dates(self):
        arr = []
        query = BookingSlots. \
            objects \
            .filter(slot__venue__id=self.venue_id, date=self.dat.date()) \
            .exclude(booking__booking_status__status__in=["cancelled"],booking__booking_status__is_active=True) \
            .values("start_time", "end_time")

        for x in query:
            a = generate_time_slots(start=x["start_time"], end=x["end_time"])
            arr += a
        return arr

    def get(self):
        total_slots = self.get_slots_dates()
        booked_slots = self.get_booked_slots_dates()
        for x in booked_slots:
            total_slots[x]["booked"] = True

        return total_slots
