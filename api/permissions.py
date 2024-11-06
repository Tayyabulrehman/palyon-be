from django.contrib.auth import authenticate
from oauth2_provider.models import AccessToken
from rest_framework import permissions
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import exception_handler

from api.customer.models import Customer
from api.users.models import AccessLevel
from api.vendor.models import Vendor


class IsVendorAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if not user.is_anonymous and user.role.code == AccessLevel.VENDOR_CODE:
            request.user = Vendor.objects.get(id=request.user.id)
            return True
        return False


class IsCustomerAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if not user.is_anonymous and user.role.code == AccessLevel.CUSTOMER_CODE:
            request.user = Customer.objects.get(id=request.user.id)
            return True
        return False


class IsAdminAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if not user.is_anonymous and user.role.code == AccessLevel.SUPER_ADMIN_CODE:
            return True
        return False


# class IsCustomerAuthenticated(permissions.BasePermission):
#
#     def has_permission(self, request, view):
#         user = request.user
#         if not user.is_anonymous and user.role.code in [AccessLevel.B2C_USER_CODE, AccessLevel.B2B_USER_CODE]:
#             return True
#         return False


# class IsAdminOrPUTAuthenticated(BaseAuthPermission):
#
#     def has_permission(self, request, view):
#         # allow all POST requests
#
#         if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
#             if not hasattr(request, "user") or request.user.is_anonymous:
#                 user = authenticate(request=request)
#                 if user:
#                     if request.method == "PUT":
#                         return True
#                     if user.role.code == AccessLevel.SUPER_ADMIN_CODE:
#                         request.user = request._cached_user = user
#                         return True
#                 return False
#         else:
#             try:
#                 access_token = request.COOKIES.get('u-at', None)
#                 if access_token:
#                     request.user = AccessToken.objects.get(token=access_token).user
#                     request.user.access_token = access_token
#                     # request.data['created_by'] = request.user.id
#                     return True
#                 else:
#                     return False
#             except AccessToken.DoesNotExist:
#                 return False


def custom_exception_handler(exc, context):
    if isinstance(exc, NotAuthenticated):
        return Response({"description": "Authentication credentials were not provided."},
                        status=401)

    # else
    # default case
    return exception_handler(exc, context)


# class IsSuperAdminOrLocalAdminAuthenticated(BaseAuthPermission):
#     def has_permission(self, request, view):
#         # allow all POST requests
#
#         if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
#             if not hasattr(request, "user") or request.user.is_anonymous:
#                 user = authenticate(request=request)
#                 if user and user.role.code in [AccessLevel.SUPER_ADMIN_CODE, AccessLevel.LOCAL_ADMIN_CODE]:
#                     request.user = request._cached_user = user
#                     return True
#                 return False
#         else:
#             try:
#                 access_token = request.COOKIES.get('u-at', None)
#                 if access_token:
#                     request.user = AccessToken.objects.get(token=access_token).user
#                     request.user.access_token = access_token
#                     # request.data['created_by'] = request.user.id
#                     return True
#                 else:
#                     return False
#             except AccessToken.DoesNotExist:
#                 return False
#
#
# class IsAuthenticatedOrGuestUser(BaseAuthPermission):
#
#     def has_permission(self, request, view):
#         # allow all POST requests
#
#         if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
#             if not hasattr(request, "user") or request.user.is_anonymous:
#                 user = authenticate(request=request)
#                 if user:
#                     request.user = request._cached_user = user
#                     request.data["owner_id"] = request.user.id
#                     return True
#                 return False
#             else:
#                 if request.user:
#                     return True
#         else:
#             try:
#                 if request.user.is_anonymous:
#                     token = request.data.pop("token", None)
#                     if Files.objects.filter(unique_uuid=token[0], id=request.data["parent_file"], is_active=True).exists():
#                         return True
#
#                 return False
#             except AccessToken.DoesNotExist:
#                 return False


class IsGetOrAuthenticatedSuperAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == "GET":
            request.user = authenticate(request=request)
            return True
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code == AccessLevel.SUPER_ADMIN_CODE:
                        request.user = request._cached_user = user
                        return True
                    else:
                        return False
        else:
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False


class IsAuthenticatedOrAllow(permissions.BasePermission):

    def has_permission(self, request, view):
        # allow all POST requests

        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    request.user = request._cached_user = user
                    return True
                return True
        return True


class IsGetOrOauthAuthenticatedCustomer(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code in [AccessLevel.B2C_USER_CODE,
                                          AccessLevel.B2B_USER_CODE]:
                        request.user = request._cached_user = user
                        # request.data['created_by'] = request.user.id
                        return True

                    else:
                        return False
        else:
            if request.method == 'GET':
                return True
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False
