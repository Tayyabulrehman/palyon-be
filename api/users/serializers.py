import os

from django.db import transaction
from oauth2_provider.models import AccessToken
from rest_framework import serializers

from api.serializers import DynamicFieldsModelSerializer
from api.users.models import User, Role, AccessLevel, EmailVerificationLink


class AuthenticateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, allow_blank=False, allow_null=False)
    password = serializers.CharField(required=True, allow_blank=False, allow_null=False)

    class Meta:
        model = User
        fields = ('email', 'password')





class UserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.EmailField(read_only=True)
    role = serializers.CharField(source='role.code', read_only=True)
    is_active = serializers.BooleanField(required=False)

    # date_of_birth = serializers.DateField(required=False, allow_null=True)
    # gender = serializers.CharField(required=False, allow_null=True)
    # phone = serializers.CharField(required=False, allow_null=True)
    # city = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "created_on",
            'id',
            'first_name',
            'last_name',
            "email",
            'role',
            'is_active',
            "is_email_verified",
            "is_approved",
            "username",
            # "date_of_birth",
            # "gender",
            # "phone",
            # "city"
        ]

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance


class SocialAuthenticateSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, allow_blank=False, allow_null=False)
    backend = serializers.CharField(required=True, allow_blank=False, allow_null=False)
    sign_up = serializers.BooleanField()
