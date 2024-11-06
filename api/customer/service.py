from django.db import transaction

from api.customer.models import Customer, Teams
from api.users.models import Role, AccessLevel


def create_customer(validated_data):
    with transaction.atomic():
        password = validated_data.pop("password")
        obj = Customer.objects.create(**validated_data, is_active=True,
                                      role_id=Role.objects.get(code=AccessLevel.CUSTOMER_CODE).id)
        obj.set_password(password)
        obj.save(update_fields=["password"])
        return obj


def create_teams(validated_date):
    with transaction.atomic():
        invitee = validated_date.pop("invitee", None)
        team = Teams.objects.create(**validated_date)
        # send invitation to all invitee
        return team
