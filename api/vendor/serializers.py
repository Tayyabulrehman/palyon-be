import datetime
from datetime import timedelta

from rest_framework import serializers

from api.serializers import DynamicFieldsModelSerializer
from api.vendor.models import VenusImages, Slots, Venue, Vendor


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "username",
            "business_name",
            "owner_name",
            "image"
        )


class VenueImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    image = serializers.ImageField(required=True, allow_null=False)
    is_featured = serializers.BooleanField()

    # product_slug = serializers.CharField(read_only=True, source='product.slug')

    class Meta:
        model = VenusImages
        fields = (
            "id",
            "image",
            "is_featured",

        )

    def create(self, validated_data):
        # validated_data['image_tab'] = _convert_to_webp(validated_data["image"], 80)
        # validated_data['image_mobile'] = _convert_to_webp(validated_data["image"], 75)
        # validated_data['image_low'] = _convert_to_webp(validated_data["image"], 50)
        # validated_data['image'] = _convert_to_webp(validated_data["image"], 100)
        return VenusImages.objects.create(**validated_data)


class SlotSerializer(serializers.ModelSerializer):
    day = serializers.IntegerField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    # active = serializers.BooleanField(required=False)
    is_engaged = serializers.BooleanField(read_only=True)

    class Meta:
        model = Slots
        fields = (
            "id",
            "day",
            "start_time",
            "end_time",
            "active",
            "is_engaged"
        )

    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        date = datetime.datetime(2024, 10, 12)

        start_datetime = datetime.datetime.combine(date, start_time)
        end_datetime = datetime.datetime.combine(date, end_time)

        # Get the time difference
        time_difference = end_datetime - start_datetime

        # Get the difference in seconds
        seconds_difference = time_difference.total_seconds()
        if seconds_difference % (60 * 60) != 0:
            raise serializers.ValidationError(
                "The time difference between start_date and end_date must be exactly 1 hour.")

        return data


class VenueSerializer(DynamicFieldsModelSerializer):
    name = serializers.CharField()
    location = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    price = serializers.FloatField()
    description = serializers.CharField()
    type = serializers.ListField(child=serializers.CharField())
    image_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    slots = SlotSerializer(allow_null=True, many=True, required=False, write_only=True)
    images = VenueImageSerializer(many=True, read_only=True)
    facilities = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Venue
        fields = (
            "id",
            "name",
            "location",
            "latitude",
            "longitude",
            "price",
            "description",
            "type",
            "image_ids",
            "slots",
            "images",
            "facilities"
        )

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.location = validated_data.get("location", instance.location)
        instance.latitude = validated_data.get("latitude", instance.latitude, )
        instance.longitude = validated_data.get("longitude", instance.longitude)
        instance.price = validated_data.get("price", instance.price)
        instance.description = validated_data.get("description", instance.description)
        instance.type = validated_data.get("type", instance.type)
        instance.facilities = validated_data.get("facilities", instance.facilities)
        images = validated_data.get("image_ids", None)

        if images:
            instance.venue_images.exclude(id__in=images).delete()
            VenusImages.objects.filter(id__in=images).update(venus=instance)
        instance.save()
        return instance
