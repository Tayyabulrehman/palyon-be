from django.urls import path
from .views import CustomersVenuesView, VenuesAdminView

urlpatterns = [
    path("", CustomersVenuesView.as_view()),
    path("admin", VenuesAdminView.as_view()),
    path("admin/<int:pk>", VenuesAdminView.as_view()),

]
