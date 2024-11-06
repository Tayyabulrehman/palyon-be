from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# Create your views here.
import requests
from django.conf import settings
from oauth2_provider.views import TokenView
from requests.auth import HTTPBasicAuth
from rest_framework import status, renderers
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import is_server_error
from rest_framework.views import APIView


class ImageUploadParser(FileUploadParser):
    media_type = 'image/*'


class BaseAPIView(APIView):
    """
    Base class for API views.
    """
    authentication_classes = ()
    permission_classes = (IsAuthenticated,)
    renderer_classes = [renderers.JSONRenderer]

    def send_response(
            self,
            success=False,
            code='',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            payload={},
            description='',
            exception=None,
            count=0,
            log_description=""
    ):
        """
        Generates response.
        :param success: bool tells if call is successful or not.
        :param code: str status code.
        :param status_code: int HTTP status code.
        :param payload: list data generated for respective API call.
        :param description: str description.
        :param exception: str description.
        :rtype: dict.
        """
        if not success and is_server_error(status_code):
            if settings.DEBUG:
                description = f'error message: {description}'
            else:
                description = 'Internal server error.'
        return Response(
            data={
                'success': success,
                'code': status_code,
                'payload': payload,
                'description': description,
                'exception': exception,
                'count': count,
            },
            status=status_code
        )

    def send_data_response(
            self,
            success=False,
            code='',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            payload={},
            description=''):
        """
        Generates response for data tables.
        :param success: bool tells if call is successful or not.
        :param code: str status code.
        :param status_code: int HTTP status code.
        :param payload: list data generated for respective API call.
        :param description: str description.
        :rtype: dict.
        """
        if not success and is_server_error(status_code):
            if settings.DEBUG:
                description = f'error message: {description}'
            else:
                description = 'Internal server error.'
        return Response(
            data={
                'data': {
                    'success': success,
                    'code': code,
                    'payload': payload,
                    'description': description}
            },
            status=status_code
        )

    @staticmethod
    def get_oauth_token(email='', password='', grant_type='password'):
        try:
            url = settings.AUTHORIZATION_SERVER_URL
            # url ='http://192.168.100.10:8000/api/oauth/token/'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'username': email.lower(),
                'password': password,
                'grant_type': grant_type,
                'scope':"openid profile"
            }
            auth = HTTPBasicAuth(
                settings.OAUTH_CLIENT_ID,
                settings.OAUTH_CLIENT_SECRET
            )
            response = requests.post(
                url=url,
                headers=headers,
                data=data,
                auth=auth
            )
            if response.ok:
                json_response = response.json()
                return {
                    'access_token': json_response.get('access_token', ''),
                    'refresh_token': json_response.get('refresh_token', '')
                }
            else:
                return {'error': response.json().get('error')}
        except Exception as e:
            # fixme: Add logger to log this exception
            return {'exception': str(e)}

    @staticmethod
    def revoke_oauth_token(token):
        try:
            url = settings.REVOKE_TOKEN_URL
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'token': token,
                'client_secret': settings.OAUTH_CLIENT_SECRET,
                'client_id': settings.OAUTH_CLIENT_ID
            }
            response = requests.post(
                url=url,
                headers=headers,
                data=data
            )
            if response.ok:
                return True
            else:
                return False
        except Exception:
            # fixme: Add logger to log this exception
            return False

    def get_sorting_query(self, order, column):
        order = '-' if order == 'desc' else ""
        return f'{order}{column}'
# views.py
# from oauth2_provider
#
# class CustomTokenSerializer(TokenSerializer):
#     def validate(self, attrs):
#         # Call the parent class's validation
#         data = super().validate(attrs)
#
#         # Add custom data to the token response (e.g., user info, roles, etc.)
#         data['user'] = {
#             'id': self.user.id,
#             'email': self.user.email,
#             'username': self.user.username,
#         }
#
#         return data
# from oauth2_provider.serializers import TokenSerializer

class CustomTokenView(TokenView):
    """
    Custom Token View to override the default behavior.
    """

    def post(self, request, *args, **kwargs):
        # Call the parent method to get the token response
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            data = response.json()
            # Modify the token response if needed
            data['custom_message'] = "Token issued successfully!"
            return JsonResponse(data)

        return response
