from oauth2_provider.models import IDToken
from oauth2_provider.oauth2_validators import OAuth2Validator


# class CustomOAuth2Validator(OAuth2Validator):
#     def get_additional_claims(self, request):
#         return {
#             "given_name": request.user.first_name,
#             "family_name": request.user.last_name,
#             "name": ' '.join([request.user.first_name, request.user.last_name]),
#             "preferred_username": request.user.username,
#             "email": request.user.email,
#         }
class CustomOAuth2Validator(OAuth2Validator):
    def get_additional_claims(self, request):
        """
        Add custom claims (e.g., user identity data) to the ID token.
        """
        user = request.user
        return {
            'sub': str(user.id),
            'name': user.get_full_name(),
            'email': user.email,
            'preferred_username': user.username,
        }

    def get_id_token(self, token, token_handler, request):
        """
        Create an ID token based on the token and request.
        """
        claims = self.get_additional_claims(request)
        id_token = IDToken(
            client_id=request.client.client_id,
            subject=request.user.id,
            issue=request.client.redirect_uri,
            nonce=request.nonce,
        )
        return id_token

    # def get_userinfo_claims(self, request):
    #     claims = super().get_userinfo_claims(request)
    #     claims["color_scheme"] = ""
    #     return claims