# Create your views here.
from django.urls import path

# app_name will help us do a reverse look-up latter.
from api.users.views import LoginView, UpdatePassword, ForgotPasswordView, LogoutView, UserView

urlpatterns = [
    path("login", LoginView.as_view(), name="users_admin_login"),
    #
    path("", UserView.as_view(), name="user"),
    path("<int:pk>", UserView.as_view(), name="user"),
    # path("update-profile", UserProfileUpdateView.as_view(), ),
    # path("update-profile/<int:pk>", UserProfileUpdateView.as_view(), ),
    # path("update-password", UserProfilePasswordView.as_view()),
    path("reset-password", UpdatePassword.as_view(), ),
    path("forgot-password", ForgotPasswordView.as_view(), ),

    path("logout", LogoutView.as_view(), name='logout'),
    # path("social-token", SocialTokenView.as_view(), name='logout'),
    # path("authorization-url", SocialAuthUrlView.as_view(), name='logout'),

]
