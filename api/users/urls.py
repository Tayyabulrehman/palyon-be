# Create your views here.
from django.urls import path

# app_name will help us do a reverse look-up latter.
from api.users.views import LoginView, \
    ResetAPIPassword, ForgotPasswordView, \
    LogoutView, UserView,UserProfileView,SyncFCMTokenView

urlpatterns = [
    path("login", LoginView.as_view(), name="users_admin_login"),
    #
    path("", UserView.as_view(), name="user"),
    path("<int:pk>", UserView.as_view(), name="user"),
    # path("update-profile", UserProfileUpdateView.as_view(), ),
    # path("update-profile/<int:pk>", UserProfileUpdateView.as_view(), ),
    # path("update-password", UserProfilePasswordView.as_view()),
    path("reset-password", ResetAPIPassword.as_view(), ),
    path("forgot-password", ForgotPasswordView.as_view(), ),
    path("me", UserProfileView.as_view(), ),

    path("logout", LogoutView.as_view(), name='logout'),
    path("sync-fcm-token/<str:token>", SyncFCMTokenView.as_view(), name='logout'),
    # path("social-token", SocialTokenView.as_view(), name='logout'),
    # path("authorization-url", SocialAuthUrlView.as_view(), name='logout'),

]
