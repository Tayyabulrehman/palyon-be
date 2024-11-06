from django.urls import path
from .views import CustomerSignupView, ProfileView, ImageUploadView

urlpatterns = [
    path("sign-up", CustomerSignupView.as_view()),
    path("profile/image", ImageUploadView.as_view()),
    path("profile", ProfileView.as_view()),

]
