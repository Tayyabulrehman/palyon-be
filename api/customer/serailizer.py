from rest_framework import serializers

from api.customer.models import Customer, Teams, Badges
from api.serializers import DynamicFieldsModelSerializer


class BatchSerializers(serializers.ModelSerializer):
    class Meta:
        model = Badges
        fields = (
            "created_on",
            "level"
        )


class CustomerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(read_only=True)
    image = serializers.ImageField(read_only=True)
    username = serializers.CharField(read_only=True)
    batch = BatchSerializers(read_only=True, many=True)

    class Meta:
        model = Customer
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "username",
            "image",
            "batch"
        )


class TeamSerializer(DynamicFieldsModelSerializer):
    name = serializers.CharField()
    typ = serializers.CharField()
    invitee = serializers.ListSerializer(child=serializers.IntegerField(), write_only=True)
    players = CustomerSerializer(read_only=True, many=True)

    class Meta:
        model = Teams
        fields = (
            "id",
            "name",
            "typ",
            "invitee",
            "players"
        )
