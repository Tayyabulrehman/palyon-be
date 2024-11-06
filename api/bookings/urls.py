from django.urls import path

from .views import CustomerBookingsView, \
    CustomerReviews, VendorBookingsView, \
    BookingsStatusView, BookingsAdminView

urlpatterns = [

    # customer
    path('customer', CustomerBookingsView.as_view()),
    path('customer/<int:pk>', CustomerBookingsView.as_view()),
    path('customer/reviews/', CustomerReviews.as_view()),
    path('customer/reviews/<int:pk>', CustomerReviews.as_view()),

    #  Vendor

    path("vendor", VendorBookingsView.as_view()),
    path("vendor/<int:pk>", VendorBookingsView.as_view()),
    path("status/", BookingsStatusView.as_view()),

    #     Admin

    path("admin/", BookingsAdminView.as_view()),
    path("admin/<int:pk>", BookingsAdminView.as_view())

]
