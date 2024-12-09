from django.shortcuts import render

# Create your views here.
import os

from django.shortcuts import render, redirect

# Create your views here.
from datetime import datetime

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as login_auth
from django.contrib.auth import logout
from django.core.exceptions import FieldError
from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext as _
from oauth2_provider.models import AccessToken
from rest_framework import status, serializers
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

# from api.customers.serializers import CustomerSerializer
from rest_framework.permissions import IsAuthenticated

from api.customer.serailizer import CustomerSerializer
from api.permissions import IsAdminAuthenticated
from api.users.models import User, EmailVerificationLink, AccessLevel
from api.users.serializers import UserSerializer
from api.views import BaseAPIView
from rest_framework.serializers import ModelSerializer

from config.tasks import send_sms_brevo
from config.utils import parse_email, boolean


class LoginView(BaseAPIView):
    class AuthenticateSerializer(ModelSerializer):
        email = serializers.CharField(required=True, allow_blank=False, allow_null=False)
        password = serializers.CharField(required=True, allow_blank=False, allow_null=False)

        class Meta:
            model = User
            fields = ('email', 'password')

    """
    API View for Login Super Admin and Admin
    """
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, pk=None):
        try:
            serializer = self.AuthenticateSerializer(data=request.data)
            if serializer.is_valid():
                email = parse_email(serializer.data.get('email'))
                password = serializer.data.get('password')
                user = authenticate(request, username=email, password=password)
                if user:

                    if user.is_active:

                        oauth_token = self.get_oauth_token(email, password)
                        if 'access_token' in oauth_token:
                            # user_data = {'access_token': oauth_token.get('access_token'),
                            #              'refresh_token': oauth_token.get('refresh_token')}
                            user = User.objects.get(id=user.id)
                            serialized = UserSerializer(user)
                            user_data = serialized.data
                            user_data['access_token'] = oauth_token.get('access_token')
                            user_data['refresh_token'] = oauth_token.get('refresh_token')
                            return self.send_response(success=True,
                                                      code=f'200',
                                                      status_code=status.HTTP_200_OK,
                                                      payload=user_data,
                                                      description=_('You are logged in!'),
                                                      )
                        else:
                            return self.send_response(description='Something went wrong with Oauth token generation.',
                                                      code=f'500')
                    else:
                        description = _('Your account is blocked or deleted.')
                        return self.send_response(success=False,
                                                  code=f'422',
                                                  status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                                  payload={},
                                                  description=description)
                else:
                    return self.send_response(
                        success=False,
                        code=f'422',
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        payload={},
                        description=_('Email or password is incorrect.')
                    )
            else:
                return self.send_response(
                    success=False,
                    code='422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors
                )


        except Exception as e:
            return self.send_response(code=f'500',
                                      description=e)


class LogoutView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = ()

    def get(self, request):
        try:
            token = request.META.get("HTTP_AUTHORIZATION", "").replace("Bearer ", "")
            if not self.revoke_oauth_token(token):
                return self.send_response(code=f'422',
                                          status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                          description=_("User doesn't logout")
                                          )
            logout(request)
            return self.send_response(success=True,
                                      code=f'201', status_code=status.HTTP_201_CREATED,
                                      payload={},
                                      description=_('User logout successfully')
                                      )
        except User.DoesNotExist:
            return self.send_response(code=f'422',
                                      status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                      description=_("User doesn't exists"))
        except FieldError:
            return self.send_response(code=f'500',
                                      description="Cannot resolve keyword given in 'order_by' into field")
        except Exception as e:
            return self.send_response(code=f'500',
                                      description=e)


class ForgotPasswordView(BaseAPIView):
    parser_class = ()
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, pk=None):
        try:
            user = User.objects.get(username__exact=request.data.get("phone"))

            email_link = EmailVerificationLink.generate_verification_code(user, days=1, )

            # send_sms_brevo(
            #     recipient=email_link.user.username,
            #     content=f"Your Password Reset Code is {email_link.code} \n"
            #             f" If you didn’t request a password reset, please ignore this message or contact support."
            # )
            message = _("Reset password code has been sent to your phone number for verification")
            return self.send_response(
                success=True,
                code='201',
                status_code=status.HTTP_201_CREATED,
                description=message,
            )


        except User.DoesNotExist:
            return self.send_response(
                code="409",
                status_code=status.HTTP_409_CONFLICT,
                description=_("User with this phone number does not exists in our system.")
            )

        except Exception as e:
            return self.send_response(
                description=e
            )


class VerifyInvitationLink(BaseAPIView):
    """
    Verify the Link of the Local Admin
    """
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, pk=None):
        """
        In this API, we will validate the **Local Admin** token. Whether it is a valid token, or unexpired.
        If it is, it will return the user_id using which **Local Admin** will update his/her password
        """
        try:
            verify = EmailVerificationLink.objects.get(token=request.data['token'], code=request.data['code'])
            if datetime.date(verify.expiry_at) <= datetime.date(datetime.now()):
                EmailVerificationLink.add_email_token_link(verify.user)
                verify.delete()
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_("The link is expired. New link has been sent to your email")
                )
            else:
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    payload={"user_id": verify.user_id},
                    description=_("Token Verified Successfully")
                )
        except EmailVerificationLink.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_("Verification token doesn't exists")
            )
        except Exception as e:
            return self.send_response(
                code=f'500',
                description=e
            )


#


class UserProfileView(BaseAPIView):
    """
    API View for Login Super Admin and Admin
    """
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAdminAuthenticated,)

    def get(self, request):
        try:
            # query = User.objects.get(id=pk)
            serializer = UserSerializer(request.user)
            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                payload=serializer.data
            )
        except User.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description="User doesn't exist"
            )
        except FieldError:
            return self.send_response(
                code=f'500',
                description="Cannot resolve keyword given in 'order_by' into field"
            )
        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="User with this email already exists in the system."
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )

    def put(self, request, pk=None):
        """
        In this api, only **Super Admin** and **Local Admin** can login. Other users won't be able to login through this API.
        **Mandatory Fields**
        * email
        * password
        """
        try:
            user_data = User.objects.get(id=request.user.id)
            # user = User
            serializer = UserSerializer(
                instance=user_data,
                data=request.data
            )
            if serializer.is_valid():
                serializer.save()
                return self.send_response(
                    success=True,
                    code=f'200',
                    status_code=status.HTTP_200_OK,
                    payload=UserSerializer(serializer.instance).data,
                    description=_("User Updated Successfully"),
                )
            else:
                return self.send_response(
                    success=True,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors,
                )

        except User.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_("User doesn't exist")
            )
        except FieldError:
            return self.send_response(
                code=f'500',
                description="Cannot resolve keyword given in 'order_by' into field"
            )
        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_("User with this email already exists in the system.")
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )


class UserProfilePasswordView(BaseAPIView):
    """
    API View for Login Super Admin and Admin
    """
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def put(self, request, pk=None):
        """
        In this api, only **Super Admin** and **Local Admin** can login. Other users won't be able to login through this API.
        **Mandatory Fields**
        * email
        * password
        """
        try:
            user_data = User.objects.get(id=request.user.id)
            if not request.data['new_password']:
                return self.send_response(
                    success=True,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_("Password Required"),
                )
            else:
                if user_data.check_password(request.data['old_password']):
                    user_data.set_password(request.data['new_password'])
                    user_data.save()
                    # user = User
                    return self.send_response(
                        success=True,
                        code=f'200',
                        status_code=status.HTTP_200_OK,
                        description=_("Password Updated Successfully"),
                    )
                else:
                    return self.send_response(
                        success=True,
                        code=f'422',
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        description=_("Invalid Password"),
                    )
        except User.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_("User doesn't exist")
            )
        except FieldError:
            return self.send_response(
                code=f'500',
                description="Cannot resolve keyword given in 'order_by' into field"
            )
        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_("User with this email already exists in the system.")
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )


class UserView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAdminAuthenticated,)

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            active = request.query_params.get('is_active', None)
            role = request.query_params.get('role', None)
            order_by = request.query_params.get('order-by', 'desc')
            column = request.query_params.get('column', 'id')
            order_by = f'{"-" if order_by == "desc" else ""}{column}'
            q = request.query_params.get('q', None)
            query_set = Q(is_deleted=False)

            if q:
                query_set &= Q(first_name__icontains=q) | \
                             Q(last_name__icontains=q) | \
                             Q(email__icontains=q) | Q(id__contains=q)
            if active:
                query_set &= Q(is_active=boolean(active))
            if role:
                query_set &= Q(role__code=role)

            if pk:
                query_set &= Q(id=pk)
                query = User.objects.get(query_set)
                serializer = UserSerializer(query)
                # if query.role.code == AccessLevel.CUSTOMER_CODE:
                #     serializer = CustomerSerializer(query)
                # else:
                #     serializers = UserSerializer(query)
                count = 1
            else:
                query = User.objects.filter(
                    query_set
                ).exclude(is_superuser=True).order_by(order_by)
                serializer = UserSerializer(
                    query[offset:limit + offset],
                    many=True,
                )

                count = query.count()
            return self.send_response(
                success=True,
                code='200',
                status_code=status.HTTP_200_OK,
                payload=serializer.data,
                count=count
            )
        except User.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('User Does`t Exist')
            )
        except FieldError as e:
            return self.send_response(
                success=False,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=f'422',
                description=str(e)
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=e)


class ResetAPIPassword(BaseAPIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, pk=None):
        """
        """
        try:

            code = request.data.get('code')
            # token = request.data.get('token')
            user = User.objects.get(
                user_email_verification__code__exact=code,

            )
            password = request.data['password']
            user.set_password(password)
            user.save()
            EmailVerificationLink.objects.get(code=request.data.get('code')).delete()
            message = _("Password Reset Successfully.")
            return self.send_response(
                success=True,
                status_code=status.HTTP_201_CREATED,
                description=message
            )

        except User.DoesNotExist:
            return self.send_response(
                code="409",
                status_code=status.HTTP_409_CONFLICT,
                description=_("The link has been used before. Please try to reset your password again.")
            )
        except Exception as e:
            return self.send_response(
                description=e
            )



class SyncFCMTokenView(BaseAPIView):
    """
    API View for Login Super Admin and Admin
    """
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request,token):
        try:
            # query = User.objects.get(id=pk)
            request.user.fcm=token
            request.user.save()
            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                description="FCM token synced successfully."

            )
        except User.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description="User doesn't exist"
            )
        except FieldError:
            return self.send_response(
                code=f'500',
                description="Cannot resolve keyword given in 'order_by' into field"
            )
        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="User with this email already exists in the system."
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )

