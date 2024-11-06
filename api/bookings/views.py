from datetime import date

from django.db.models import Q, Prefetch
from django.shortcuts import render
from rest_framework import serializers, status
# Create your views here.
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.permissions import IsAuthenticated

from api.bookings.models import Booking, Reviews
from api.bookings.serializer import BookingSerializer, StatusSerializer
from api.bookings.service import CustomerBookingBuilder, VendorBookingBuilder
from api.permissions import IsCustomerAuthenticated, IsVendorAuthenticated, IsAdminAuthenticated
from api.views import BaseAPIView
from django.utils.translation import gettext_lazy as _


class CustomerBookingsView(BaseAPIView):
    class Const:
        upcoming = 'upcoming'
        today = 'today'
        past = 'past'

    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsCustomerAuthenticated,)

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # is_active = request.query_params.get('is-active', None)
            column = request.query_params.get('column', "id")
            order_by = request.query_params.get('order-by', "desc")
            typ = request.query_params.get('typ', None)
            search = request.query_params.get('search', None)
            order_by = self.get_sorting_query(order_by, column)
            query_set = Q(customer_id=request.user.id)

            if pk:
                query_set &= Q(id=pk)
                query = Booking.objects \
                    .prefetch_related(Prefetch('booking_slots', to_attr='slots')) \
                    .get(query_set)
                serializer = BookingSerializer(query)
                count = 1

            else:
                if search:
                    query_set &= Q(first_name__icontains=search) \
                                 | Q(last_name__contains=search) \
                                 | Q(phone__contains=search) \
                                 | Q(id__contains=search)
                if typ:
                    if typ == self.Const.today:
                        query_set &= Q(date=date.today())
                    elif typ == self.Const.past:
                        query_set &= Q(date__lt=date.today())
                    elif typ == self.Const.upcoming:
                        query_set &= Q(date__gt=date.today())

                query = Booking.objects.select_related('venue') \
                    .filter(query_set) \
                    .distinct() \
                    .order_by(order_by)
                serializer = BookingSerializer(query[offset:limit + offset], many=True, )
                count = query.count()

            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                code='200',
                payload=serializer.data,
                count=count

            )
        except Booking.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Booking Does`t Exist')
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))

    def post(self, request):
        try:
            serializer = BookingSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                validated_data["customer_id"] = request.user.id
                booking = CustomerBookingBuilder(validated_data).build()
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Booking Created Successfully'),

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
        # except ValidationError as e:
        #     return self.send_response(
        #     success = False,
        #     code = '422',
        #     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
        #     description = str(e)
        # )

        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_("Booking already exist")
                )
            return self.send_response(
                code=f'500',
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


class CustomerReviews(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsCustomerAuthenticated,)

    class InputSerializer(serializers.ModelSerializer):
        rating = serializers.IntegerField()
        description = serializers.CharField()
        venue_id = serializers.IntegerField()

        class Meta:
            model = Reviews
            fields = (
                "rating",
                "description",
                "venue_id"

            )

    def get(self, request, pk):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # is_active = request.query_params.get('is-active', None)
            column = request.query_params.get('column', "id")
            order_by = request.query_params.get('order-by', "desc")
            typ = request.query_params.get('typ', None)
            search = request.query_params.get('search', None)
            order_by = self.get_sorting_query(order_by, column)
            query_set = Q(venue_id=pk)

            # if pk:
            #     query_set &= Q(id=pk)
            #     query = Booking.objects \
            #         .prefetch_related(Prefetch('booking_slots', to_attr='slots')) \
            #         .get(query_set)
            #     serializer = BookingSerializer(query)
            #     count = 1

            # else:
            #     if search:
            #         query_set &= Q(first_name__icontains=search) \
            #                      | Q(last_name__contains=search) \
            #                      | Q(phone__contains=search) \
            #                      | Q(id__contains=search)
            #     if typ:
            #         if typ == self.Const.today:
            #             query_set &= Q(date=date.today())
            #         elif typ == self.Const.past:
            #             query_set &= Q(date__lt=date.today())
            #         elif typ == self.Const.upcoming:
            #             query_set &= Q(date__gt=date.today())

            query = Reviews.objects \
                .filter(query_set) \
                .distinct() \
                .order_by(order_by)
            serializer = self.InputSerializer(query[offset:limit + offset], many=True, )
            count = query.count()

            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                code='200',
                payload=serializer.data,
                count=count

            )
        except Reviews.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Reviews Does`t Exist')
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))

    def post(self, request):
        try:
            serializer = self.InputSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                validated_data["customer_id"] = request.user.id
                serializer.save()
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Review Added Successfully'),

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
        # except ValidationError as e:
        #     return self.send_response(
        #     success = False,
        #     code = '422',
        #     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
        #     description = str(e)
        # )

        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_("Review already added")
                )
            return self.send_response(
                code=f'500',
                description=str(e)
            )


class VendorBookingsView(BaseAPIView):
    class Const:
        upcoming = 'upcoming'
        today = 'today'
        past = 'past'

    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsVendorAuthenticated,)

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # is_active = request.query_params.get('is-active', None)
            column = request.query_params.get('column', "id")
            order_by = request.query_params.get('order-by', "desc")
            typ = request.query_params.get('typ', None)
            search = request.query_params.get('search', None)
            order_by = self.get_sorting_query(order_by, column)
            query_set = Q(venue__vendor__id=request.user.id)
            venue_id = request.query_params.get('venue_id', None)
            # booking_slots__venue__vendor__id=request.user.id

            if pk:
                query_set &= Q(id=pk)
                query = Booking.objects \
                    .prefetch_related(Prefetch('booking_slots', to_attr='slots')) \
                    .get(query_set)
                serializer = BookingSerializer(query)
                count = 1

            else:
                if search:
                    query_set &= Q(first_name__icontains=search) \
                                 | Q(last_name__contains=search) \
                                 | Q(phone__contains=search) \
                                 | Q(id__contains=search)
                if typ:
                    if typ == self.Const.today:
                        query_set &= Q(date=date.today())
                    elif typ == self.Const.past:
                        query_set &= Q(date__lt=date.today())
                    elif typ == self.Const.upcoming:
                        query_set &= Q(date__gt=date.today())
                if venue_id:
                    query_set &= Q(venue_id=venue_id)

                query = Booking.objects \
                    .prefetch_related(Prefetch('booking_slots', to_attr='slots')) \
                    .filter(query_set) \
                    .distinct() \
                    .order_by(order_by)
                serializer = BookingSerializer(query[offset:limit + offset], many=True, )
                count = query.count()

            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                code='200',
                payload=serializer.data,
                count=count

            )
        except Booking.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Booking Does`t Exist')
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))

    def post(self, request):
        try:
            serializer = BookingSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                # validated_data["customer_id"] = request.user.id
                booking = VendorBookingBuilder(validated_data).build()
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Booking Created Successfully'),

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
        # except ValidationError as e:
        #     return self.send_response(
        #     success = False,
        #     code = '422',
        #     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
        #     description = str(e)
        # )

        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_("Booking already exist")
                )
            return self.send_response(
                code=f'500',
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


class BookingsStatusView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            serializer = StatusSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Booking Status updated Successfully'),

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
        # except ValidationError as e:
        #     return self.send_response(
        #     success = False,
        #     code = '422',
        #     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
        #     description = str(e)
        # )

        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=_("Status already exist")
                )
            return self.send_response(
                code=f'500',
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


class BookingsAdminView(BaseAPIView):
    class Const:
        upcoming = 'upcoming'
        today = 'today'
        past = 'past'

    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAdminAuthenticated,)

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # is_active = request.query_params.get('is-active', None)
            column = request.query_params.get('column', "id")
            order_by = request.query_params.get('order-by', "desc")
            typ = request.query_params.get('typ', None)
            search = request.query_params.get('search', None)
            order_by = self.get_sorting_query(order_by, column)
            query_set = Q()
            venue_id = request.query_params.get('venue_id', None)
            customer_id = request.query_params.get('customer_id', None)
            status_ = request.query_params.get("status", None)
            # booking_slots__venue__vendor__id=request.user.id

            if pk:
                query_set &= Q(id=pk)
                query = Booking.objects \
                    .prefetch_related(Prefetch('booking_slots', to_attr='slots')) \
                    .get(query_set)
                serializer = BookingSerializer(query)
                count = 1

            else:
                if search:
                    query_set &= Q(first_name__icontains=search) \
                                 | Q(last_name__contains=search) \
                                 | Q(phone__contains=search) \
                                 | Q(id__contains=search)
                if typ:
                    if typ == self.Const.today:
                        query_set &= Q(date=date.today())
                    elif typ == self.Const.past:
                        query_set &= Q(date__lt=date.today())
                    elif typ == self.Const.upcoming:
                        query_set &= Q(date__gt=date.today())
                if venue_id:
                    query_set &= Q(venue_id=venue_id)

                if customer_id:
                    query_set &= Q(customer_id=customer_id)

                if status_:
                    query_set &= Q(booking_status__status=status_, booking_status__is_active=True)

                query = Booking.objects \
                    .prefetch_related(Prefetch('booking_slots', to_attr='slots')) \
                    .filter(query_set) \
                    .distinct() \
                    .order_by(order_by)
                serializer = BookingSerializer(
                    query[offset:limit + offset],
                    many=True,
                    fields=(
                        "id",
                        "create_on",
                        "first_name",
                        "last_name",
                        "phone",
                        "amount",
                        "booking_status",
                        "venue"

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
        except Booking.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Booking Does`t Exist')
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))
