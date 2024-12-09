from django.contrib.gis.geos import Point
from django.db import transaction

from api.users.models import Role, AccessLevel
from api.vendor.models import Vendor, Venue, VenusImages, Slots


def create_vendor(validated_data):
    with transaction.atomic():
        password = validated_data.pop("password")
        obj = Vendor.objects.create(**validated_data, is_active=True,
                                    role_id=Role.objects.get(code=AccessLevel.VENDOR_CODE).id)
        obj.set_password(password)
        obj.save(update_fields=["password"])
        return obj


def create_venues(validated_data):
    with transaction.atomic():
        slots = validated_data.pop("slots", [])
        images = validated_data.pop("image_ids", None)
        # validated_data["loc"]=Point(validated_data["longitude"],validated_data["latitude"])
        venue = Venue.objects.create(**validated_data)
        if images:
            VenusImages.objects.filter(id__in=images).update(venus=venue)
        slots = [Slots(venue_id=venue.id, **x) for x in slots]
        Slots.objects.bulk_create(slots)
        return venue



