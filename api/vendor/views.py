import datetime

from django.core.exceptions import FieldError, ValidationError
from django.db.models import Q, Prefetch, OuterRef, Exists, Sum, Count, Avg
from django.db.models.functions import TruncMonth
from django.shortcuts import render

# Create your views here.
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from api.bookings.models import Booking, BookingSlots, Reviews
from api.permissions import IsVendorAuthenticated
from api.vendor.models import Vendor, Venue, Slots
from api.vendor.selector import SlotsList
from api.vendor.serializers import VenueImageSerializer, VenueSerializer, SlotSerializer
from api.vendor.service import create_vendor, create_venues
from api.views import APIView, BaseAPIView
from rest_framework import serializers, status

from config.utils import parse_email

from django.utils.translation import gettext as _


class VendorSignupView(BaseAPIView):
    authentication_classes = ()
    permission_classes = ()

    class InputSerializer(serializers.ModelSerializer):
        first_name = serializers.CharField()
        last_name = serializers.CharField()
        password = serializers.CharField()
        email = serializers.EmailField()
        business_name = serializers.CharField()
        owner_name = serializers.CharField()
        phone = serializers.CharField()

        class Meta:
            model = Vendor
            fields = (
                "first_name",
                "last_name",
                "email",
                "password",
                "business_name",
                "owner_name",
                "phone"
            )

    def post(self, request, pk=None):

        """
        In this api, only **Super Admin** and **Local Admin** can login. Other users won't be able to login through this API.
        **Mandatory Fields**
        * email
        * password
        """
        try:
            # with transaction.atomic():
            serializer = self.InputSerializer(data=request.data)
            if serializer.is_valid():
                data = serializer.validated_data
                create_vendor(data)
                # data = serializer.data
                # data["role"] = Role.objects.get(code=AccessLevel.B2C_USER)
                # serializer.save()
                oauth_token = self.get_oauth_token(parse_email(request.data['email']), request.data['password'])
                if 'access_token' in oauth_token:
                    user_data = data
                    user_data['access_token'] = oauth_token.get('access_token')
                    user_data['refresh_token'] = oauth_token.get('refresh_token')
                    return self.send_response(
                        success=True,
                        code=f'201',
                        status_code=status.HTTP_201_CREATED,
                        payload=user_data,
                        description=_("Vendor Account Created Successfully"),
                    )
            else:
                return self.send_response(
                    success=True,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="Invalid form data",
                    exception=serializer.errors,
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
                    description=_("User with email already exists")
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )


class ImageUploadView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsVendorAuthenticated,)

    def post(self, request):
        try:
            serializer = VenueImageSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return self.send_response(
                    success=True,
                    code=status.HTTP_201_CREATED,
                    payload=serializer.data,
                    status_code=status.HTTP_201_CREATED,
                    description=_('Image Uploaded')
                )
            else:
                return self.send_response(
                    code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description='Unable to upload image. Try again.',
                    exception=serializer.errors
                )
        except Exception as e:
            return self.send_response(
                description=str(e)
            )


class VendorVenuesView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsVendorAuthenticated,)

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # is_active = request.query_params.get('is-active', None)
            column = request.query_params.get('column', "id")
            order_by = request.query_params.get('order-by', "desc")
            search = request.query_params.get('search', None)
            order_by = self.get_sorting_query(order_by, column)
            query_set = Q(deleted=False)
            if pk:
                query = Venue. \
                    objects \
                    .prefetch_related(Prefetch("venue_images", to_attr="images")) \
                    .get(id=pk)
                serializer = VenueSerializer(query)
                count = 1

            else:
                # if is_active:
                #     query_set &= Q(is_active=boolean(is_active))

                if search:
                    query_set &= Q(name__icontains=search) | Q(id__contains=search)

                query = Venue \
                    .objects \
                    .prefetch_related(Prefetch("venue_images", to_attr="images")) \
                    .filter(query_set) \
                    .distinct() \
                    .order_by(order_by)
                serializer = VenueSerializer(
                    query[offset:limit + offset],
                    many=True,
                    fields=(
                        "id",
                        "name",
                        "location",
                        "images"
                    )

                )
                count = query.count()

            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                code='200',
                payload=serializer.data,
                count=count

            )
        except Venue.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Venus Does`t Exist')
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))

    def post(self, request):
        try:
            serializer = VenueSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                validated_data["vendor_id"] = request.user.id
                create_venues(validated_data)
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Venus Added Successfully'),

                )
            else:
                return self.send_response(
                    success=False,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors
                )
        except ValueError as e:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=str(e)
            )

        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_("Venue already exist")
                )
            return self.send_response(
                code=f'500',
                description=str(e)
            )

    def put(self, request, pk=None):
        try:

            serializer = VenueSerializer(instance=Venue.objects.get(id=pk, deleted=False),
                                         data=request.data,
                                         partial=True)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                validated_data["modified_by"] = request.user.id
                serializer.save(**validated_data)
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Venue details Updated Successfully')
                )
            else:
                return self.send_response(
                    success=False,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors
                )
        except Venue.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Venue Does`t Exist')
            )
        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e)
            )

    def delete(self, request, pk):
        try:
            is_updated = Venue \
                .objects \
                .filter(id=pk) \
                .update(deleted=True)
            if is_updated:
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Venue deleted Successfully')
                )
            else:
                return self.send_response(
                    success=False,
                    code='422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_('Category Does`t Exist')
                )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e)
            )


class VenuesSlotView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsVendorAuthenticated,)

    def get(self, request, pk):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # is_active = request.query_params.get('is-active', None)
            column = request.query_params.get('column', "id")
            order_by = request.query_params.get('order-by', "desc")
            date = request.query_params.get('date', datetime.datetime.today())
            search = request.query_params.get('search', None)
            order_by = self.get_sorting_query(order_by, column)

            # if pk:
            #     query = Venue.objects.get(id=pk)
            #     serializer = VenueSerializer(query)
            #     count = 1
            #
            # else:
            # if is_active:
            #     query_set &= Q(is_active=boolean(is_active))

            # if search:
            #     query_set &= Q(name__icontains=search) | Q(id__contains=search)
            if date and isinstance(date, str):
                date = datetime.datetime.strptime(date, "%Y-%m-%d")

            query_set = Q(venue_id=pk, day=date.weekday() + 1)

            subquery = BookingSlots.objects.filter(slot=OuterRef("pk"), date=date)

            query = Slots.objects \
                .annotate(is_engaged=Exists(subquery)) \
                .filter(query_set) \
                .distinct() \
                .order_by(order_by)
            serializer = SlotSerializer(query[offset:limit + offset], many=True, )
            count = query.count()

            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                code='200',
                payload=serializer.data,
                count=count

            )
        except Slots.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Slot Does`t Exist')
            )

        except ValidationError as e:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=str(e)
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))

    def post(self, request, pk):
        try:
            serializer = SlotSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                validated_data["venue_id"] = pk
                serializer.save(**validated_data)
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Slot Added Successfully'),

                )
            else:
                return self.send_response(
                    success=False,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors
                )
        except ValueError as e:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=str(e)
            )
        except ValidationError as e:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=str(e)
            )

        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_("Slot already exist")
                )
            return self.send_response(
                code=f'500',
                description=str(e)
            )

    def put(self, request, pk=None):
        try:

            serializer = VenueSerializer(instance=Venue.objects.get(id=pk, is_active=True),
                                         data=request.data,
                                         partial=True)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                validated_data["modified_by"] = request.user.id
                serializer.save(**validated_data)
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Venue details Updated Successfully')
                )
            else:
                return self.send_response(
                    success=False,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors
                )
        except Venue.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Venue Does`t Exist')
            )
        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e)
            )

    # def delete(self, request, pk):
    #     try:
    #         is_updated = Venue \
    #             .objects \
    #             .filter(is_active=True, id=pk) \
    #             .update(is_active=False)
    #         if is_updated:
    #             Product.objects.filter(company_id=pk).update(company_id=None)
    #
    #         else:
    #             return self.send_response(
    #                 success=False,
    #                 code='422',
    #                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #                 description=_('Company Does`t Exist')
    #             )
    #
    #         return self.send_response(
    #             success=True,
    #             code=f'201',
    #             status_code=status.HTTP_201_CREATED,
    #             description=_('Company deleted Successfully')
    #         )
    #
    #     except Company.DoesNotExist:
    #         return self.send_response(
    #             success=False,
    #             code='422',
    #             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #             description=_('Category Does`t Exist')
    #         )
    #     except Exception as e:
    #         return self.send_response(
    #             success=False,
    #             description=str(e)
    #         )


class SlotAvailabilityView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = ()

    def get(self, request, pk):
        try:

            date = request.query_params.get('date', datetime.datetime.today())
            search = request.query_params.get('search', None)
            data = SlotsList(venue_id=pk, dat=date).get()
            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                code='200',
                payload=data,

            )
        except Slots.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Slot Does`t Exist')
            )

        except ValidationError as e:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=str(e)
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))


class DashboardView(BaseAPIView, ):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsVendorAuthenticated,)

    def get(self, request):
        try:
            start_date = request.query_params.get("start_date", "2024-01-01")
            end_date = request.query_params.get("end_date", "2024-12-30")
            base_query = Booking.objects.filter(venue__vendor=request.user, booking_status__status='confirmed')
            total_revenue = base_query.aggregate(t=Sum("amount", default=0)).get("t")
            revenue_monthly = base_query.filter(created_on__gte=start_date, created_on__lte=end_date) \
                .annotate(month=TruncMonth('created_on')) \
                .values('month') \
                .annotate(total_revenue=Sum('amount')) \
                .order_by('month')
            total_booking = base_query.aggregate(t=Count("id")).get("t")
            booking_monthly = base_query.filter(created_on__gte=start_date, created_on__lte=end_date) \
                .annotate(month=TruncMonth('created_on')) \
                .values('month') \
                .annotate(total_revenue=Count('id')) \
                .order_by('month')

            offline_total_booking = base_query.filter(customer_id__isnull=True).aggregate(t=Count("id")).get(
                "t")
            offline_booking_monthly = base_query.filter(created_on__gte=start_date, created_on__lte=end_date,
                                                        customer_id__isnull=True) \
                .annotate(month=TruncMonth('created_on')) \
                .values('month') \
                .annotate(total_revenue=Count('id')) \
                .order_by('month')

            base_rating = Reviews.objects.filter(venue__vendor__id=request.user.id)

            total_rating = base_rating.aggregate(t=Avg("rating", default=0)).get("t")
            rating_monthly = base_rating.filter(created_on__gte=start_date, created_on__lte=end_date) \
                .annotate(month=TruncMonth('created_on')) \
                .values('month') \
                .annotate(rating=Avg('rating')) \
                .order_by('month')

            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                payload={
                    "revenue": {
                        "total": total_revenue,
                        "monthly": revenue_monthly
                    },
                    "bookings": {
                        "total": total_booking,
                        "monthly": booking_monthly

                    },
                    "offline_bookings": {
                        "total": offline_total_booking,
                        "monthly": offline_booking_monthly
                    },
                    "rating": {
                        "total": total_rating,
                        "rating_monthly": rating_monthly
                    }
                }
            )

        except ValidationError as e:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=str(e)
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))
