from rest_framework import serializers

from api.bookings.models import BookingSlots, Booking, BookingStatus
from api.serializers import DynamicFieldsModelSerializer
from api.vendor.models import Venue
from api.vendor.serializers import VenueImageSerializer


class SlotSerializer(serializers.ModelSerializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    date = serializers.DateField()
    slot_id = serializers.IntegerField()

    class Meta:
        model = BookingSlots
        fields = (
            "start_time",
            "end_time",
            "date",
            "slot_id"
        )

    # def validate(self, attrs):
    #     if not (attrs["end_time"] - attrs['start_time'] / 3600) % 60 == 0:
    #         raise ValueError("time span should 1 hour")
    #     return attrs


class StatusSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(write_only=True)
    status = serializers.CharField()

    class Meta:
        model = BookingStatus
        fields = (
            "booking_id",
            "created_on",
            "status"
        )


class VenueSerializer(DynamicFieldsModelSerializer):
    venue_images = VenueImageSerializer(many=True, read_only=True)

    class Meta:
        model = Venue
        fields = (
            "id",
            "name",
            "location",
            # "latitude",
            # "longitude",
            "venue_images"
        )

    # def update(self, instance, validated_data):
    #     instance.name = validated_data.get("name", instance.name)
    #     instance.location = validated_data.get("location", instance.location)
    #     instance.latitude = validated_data.get("latitude", instance.latitude, )
    #     instance.longitude = validated_data.get("longitude", instance.longitude)
    #     instance.price = validated_data.get("price", instance.price)
    #     instance.description = validated_data.get("description", instance.description)
    #     instance.type = validated_data.get("type", instance.type)
    #     images = validated_data.get("image_ids", None)
    #     if images:
    #         instance.venue_images.exclude(id__in=images).delete()
    #         VenusImages.objects.filter(id__in=images).update(venus=instance)
    #     instance.save()
    #     return instance


class BookingSerializer(DynamicFieldsModelSerializer):
    # slot_id = serializers.IntegerField()
    # customer_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField()
    amount = serializers.FloatField(read_only=True)
    slots = SlotSerializer(many=True,default=None)
    venue = VenueSerializer(read_only=True)
    booking_status = StatusSerializer(read_only=True, many=True)

    class Meta:
        model = Booking
        fields = '__all__'
