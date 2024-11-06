from django.urls import path
from api.vendor.views import VendorSignupView, ImageUploadView,\
    VendorVenuesView,VenuesSlotView,SlotAvailabilityView,DashboardView

urlpatterns = [
    path("sign-up", VendorSignupView.as_view()),
    path("upload-images", ImageUploadView.as_view()),
    path("dashboard",DashboardView.as_view()),
    path("venues", VendorVenuesView.as_view()),
    path("venues/<int:pk>", VendorVenuesView.as_view()),
    path("venues/<int:pk>/slots", VenuesSlotView.as_view()),
    path("venues/slots/<int:pk>", VenuesSlotView.as_view()),
    path("venues/<int:pk>/available-slots", SlotAvailabilityView.as_view()),
]
