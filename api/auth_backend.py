# backends.py
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend, BaseBackend

UserModel = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend to allow login with either email or username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Check if the username is an email or a username
        if '@' in username:
            # Attempt to find the user by email
            try:
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                return None
        else:
            # Attempt to find the user by username
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                return None

        # Verify the user's password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
