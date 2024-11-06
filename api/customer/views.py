from django.core.exceptions import FieldError
from django.db.models import Q, Prefetch
from django.shortcuts import render

# Create your views here.
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import serializers, status

from api.customer.models import Customer, Teams, Players, Activity
from api.customer.serailizer import CustomerSerializer, TeamSerializer
from api.customer.service import create_customer, create_teams
from api.views import BaseAPIView
from django.utils.translation import gettext as _
from api.permissions import IsCustomerAuthenticated


class CustomerSignupView(BaseAPIView):
    authentication_classes = ()
    permission_classes = ()

    class InputSerializer(serializers.ModelSerializer):
        first_name = serializers.CharField()
        last_name = serializers.CharField()
        password = serializers.CharField()
        email = serializers.EmailField()
        username = serializers.CharField(required=False, allow_null=True, allow_blank=True)

        class Meta:
            model = Customer
            fields = (
                "first_name",
                "last_name",
                "email",
                "password",
                "username"
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
                obj = create_customer(data)
                # data = serializer.data
                # data["role"] = Role.objects.get(code=AccessLevel.B2C_USER)
                # serializer.save()
                username = obj.email if obj.email else obj.username
                oauth_token = self.get_oauth_token(username, request.data['password'])
                if 'access_token' in oauth_token:
                    user_data = data
                    user_data['access_token'] = oauth_token.get('access_token')
                    user_data['refresh_token'] = oauth_token.get('refresh_token')
                    return self.send_response(
                        success=True,
                        code=f'201',
                        status_code=status.HTTP_201_CREATED,
                        payload=user_data,
                        description=_("Customer Account Created Successfully"),
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
                    description=_("User with email or phone number already exists")
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )


class ImageUploadView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsCustomerAuthenticated,)

    def post(self, request):
        try:
            request.user.image = request.data["image"]
            request.user.save()
            return self.send_response(
                success=True,
                code=f'201',
                status_code=status.HTTP_200_OK,
                description=_("Profile Image updated"),
            )

        except Exception as e:
            return self.send_response(
                description=str(e)
            )


class ProfileView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsCustomerAuthenticated,)

    def get(self, request, pk=None):
        try:
            data = CustomerSerializer(request.user).data
            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                code='200',
                payload=data,

            )
        except Customer.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Customer Does`t Exist')
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))

    def put(self, request, pk=None):
        try:

            serializer = CustomerSerializer(instance=request.user,
                                            data=request.data,
                                            partial=True)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                serializer.save(**validated_data)
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Customer Profile Updated Successfully'),
                    payload=CustomerSerializer(serializer.instance).data
                )
            else:
                return self.send_response(
                    success=False,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors
                )
        except Customer.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Customer Does`t Exist')
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
    #             .filter(id=pk) \
    #             .update(deleted=True)
    #         if is_updated:
    #             return self.send_response(
    #                 success=True,
    #                 code=f'201',
    #                 status_code=status.HTTP_201_CREATED,
    #                 description=_('Venue deleted Successfully')
    #             )
    #         else:
    #             return self.send_response(
    #                 success=False,
    #                 code='422',
    #                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #                 description=_('Category Does`t Exist')
    #             )
    #
    #     except Exception as e:
    #         return self.send_response(
    #             success=False,
    #             description=str(e)
    #         )


class TeamView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsCustomerAuthenticated,)

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # is_active = request.query_params.get('is-active', None)
            column = request.query_params.get('column', "id")
            order_by = request.query_params.get('order-by', "desc")
            search = request.query_params.get('search', None)
            order_by = self.get_sorting_query(order_by, column)
            query_set = Q(customer_id=request.user.id)
            if pk:
                query = Teams. \
                    objects \
                    .prefetch_related(Prefetch("team_players", to_attr="players")) \
                    .get(id=pk)
                serializer = TeamSerializer(query)
                count = 1

            else:
                # if is_active:
                #     query_set &= Q(is_active=boolean(is_active))

                if search:
                    query_set &= Q(name__icontains=search) | Q(id__contains=search)

                query = Teams \
                    .objects \
                    .filter(query_set) \
                    .distinct() \
                    .order_by(order_by)
                serializer = TeamSerializer(
                    query[offset:limit + offset],
                    many=True,
                    fields=(
                        "id",
                        "name",
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
        except Teams.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Team Does`t Exist')
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))

    def post(self, request):
        try:
            serializer = TeamSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                validated_data["customer_id"] = request.user.id
                create_teams(validated_data)
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Team Created Successfully'),

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
                    description=_("Team  already exist")
                )
            return self.send_response(
                code=f'500',
                description=str(e)
            )

    def put(self, request, pk=None):
        try:

            serializer = TeamSerializer(instance=Teams.objects.get(id=pk, deleted=False),
                                        data=request.data,
                                        partial=True)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                # validated_data["modified_by"] = request.user.id
                serializer.save(**validated_data)
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Teams details Updated Successfully')
                )
            else:
                return self.send_response(
                    success=False,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors
                )
        except Teams.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Team Does`t Exist')
            )
        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e)
            )

    def delete(self, request, pk):
        try:
            Teams.objects.get(id=pk).delete()
            return self.send_response(
                success=True,
                code=f'201',
                status_code=status.HTTP_201_CREATED,
                description=_('Venue deleted Successfully')
            )
        except Teams.DoesNotExist:
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


class TeamPlayersView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsCustomerAuthenticated,)

    # def post(self, request,team_id,user_id):
    #     try:
    #         serializer = TeamSerializer(data=request.data)
    #         if serializer.is_valid():
    #             validated_data = serializer.validated_data
    #             validated_data["vendor_id"] = request.user.id
    #             create_teams(validated_data)
    #             return self.send_response(
    #                 success=True,
    #                 code=f'201',
    #                 status_code=status.HTTP_201_CREATED,
    #                 description=_('Team Created Successfully'),
    #
    #             )
    #         else:
    #             return self.send_response(
    #                 success=False,
    #                 code=f'422',
    #                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #                 description=serializer.errors
    #             )
    #     except ValueError as e:
    #         return self.send_response(
    #             code=f'422',
    #             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #             description=str(e)
    #         )
    #
    #     except Exception as e:
    #         if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
    #             return self.send_response(
    #                 code=f'422',
    #                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #                 description=_("Team  already exist")
    #             )
    #         return self.send_response(
    #             code=f'500',
    #             description=str(e)
    #         )

    def delete(self, request, team_id, customer_id):
        try:
            Players.objects \
                .get(team_id=team_id, customer_id=customer_id, team__customer_id=request.user.id) \
                .delete()
            return self.send_response(
                success=True,
                code=f'201',
                status_code=status.HTTP_201_CREATED,
                description=_('Player deleted Successfully')
            )
        except Players.DoesNotExist:
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


class InvitationVerificationView(BaseAPIView):
    authentication_classes = ()
    permission_classes = ()


class ActivityView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsCustomerAuthenticated,)

    class ActivitySerializer(serializers.ModelSerializer):
        class Meta:
            model = Activity
            fields = '__all__'

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # is_active = request.query_params.get('is-active', None)
            column = request.query_params.get('column', "id")
            order_by = request.query_params.get('order-by', "desc")
            search = request.query_params.get('search', None)
            order_by = self.get_sorting_query(order_by, column)
            query_set = Q(customer_id=request.user.id)
            if pk:
                query = Teams. \
                    objects \
                    .prefetch_related(Prefetch("team_players", to_attr="players")) \
                    .get(id=pk)
                serializer = TeamSerializer(query)
                count = 1

            else:
                # if is_active:
                #     query_set &= Q(is_active=boolean(is_active))

                if search:
                    query_set &= Q(name__icontains=search) | Q(id__contains=search)

                query = Teams \
                    .objects \
                    .filter(query_set) \
                    .distinct() \
                    .order_by(order_by)
                serializer = TeamSerializer(
                    query[offset:limit + offset],
                    many=True,
                    fields=(
                        "id",
                        "name",
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
        except Teams.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Team Does`t Exist')
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e))

    def post(self, request):
        try:
            serializer = self.ActivitySerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                validated_data["creator_id"] = request.user.id
                serializer.save()
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Activity Created Successfully'),

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
                    description=_("Team  already exist")
                )
            return self.send_response(
                code=f'500',
                description=str(e)
            )

    def put(self, request, pk=None):
        try:

            serializer = self.ActivitySerializer(instance=Activity.objects.get(id=pk),
                                        data=request.data,
                                        partial=True)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                # validated_data["modified_by"] = request.user.id
                serializer.save(**validated_data)
                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description=_('Activity details Updated Successfully')
                )
            else:
                return self.send_response(
                    success=False,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors
                )
        except Activity.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Activity Does`t Exist')
            )
        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e)
            )

    def delete(self, request, pk):
        try:
            Activity.objects.get(id=pk,creator_id=request.user.id).delete()
            return self.send_response(
                success=True,
                code=f'201',
                status_code=status.HTTP_201_CREATED,
                description=_('Activity deleted Successfully')
            )
        except Activity.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=_('Activity Does`t Exist')
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e)
            )









# class DashboardView(BaseAPIView, ):
#     authentication_classes = (OAuth2Authentication,)
#     permission_classes = (IsCustomerAuthenticated,)
#
#     def get(self, request):
#         try:
#             start_date = request.query_params.get("start_date", "2024-01-01")
#             end_date = request.query_params.get("end_date", "2024-12-30")
#             base_query = Booking.objects.filter(venue__vendor=request.user, booking_status__status='confirmed')
#             total_revenue = base_query.aggregate(t=Sum("amount", default=0)).get("t")
#             revenue_monthly = base_query.filter(created_on__gte=start_date, created_on__lte=end_date) \
#                 .annotate(month=TruncMonth('created_on')) \
#                 .values('month') \
#                 .annotate(total_revenue=Sum('amount')) \
#                 .order_by('month')
#             total_booking = base_query.aggregate(t=Count("id")).get("t")
#             booking_monthly = base_query.filter(created_on__gte=start_date, created_on__lte=end_date) \
#                 .annotate(month=TruncMonth('created_on')) \
#                 .values('month') \
#                 .annotate(total_revenue=Count('id')) \
#                 .order_by('month')
#
#             offline_total_booking = base_query.filter(customer_id__isnull=True).aggregate(t=Count("id")).get(
#                 "t")
#             offline_booking_monthly = base_query.filter(created_on__gte=start_date, created_on__lte=end_date,
#                                                         customer_id__isnull=True) \
#                 .annotate(month=TruncMonth('created_on')) \
#                 .values('month') \
#                 .annotate(total_revenue=Count('id')) \
#                 .order_by('month')
#
#             base_rating = Reviews.objects.filter(venue__vendor__id=request.user.id)
#
#             total_rating = base_rating.aggregate(t=Avg("rating", default=0)).get("t")
#             rating_monthly = base_rating.filter(created_on__gte=start_date, created_on__lte=end_date) \
#                 .annotate(month=TruncMonth('created_on')) \
#                 .values('month') \
#                 .annotate(rating=Avg('rating')) \
#                 .order_by('month')
#
#             return self.send_response(
#                 success=True,
#                 status_code=status.HTTP_200_OK,
#                 payload={
#                     "revenue": {
#                         "total": total_revenue,
#                         "monthly": revenue_monthly
#                     },
#                     "bookings": {
#                         "total": total_booking,
#                         "monthly": booking_monthly
#
#                     },
#                     "offline_bookings": {
#                         "total": offline_total_booking,
#                         "monthly": offline_booking_monthly
#                     },
#                     "rating": {
#                         "total": total_rating,
#                         "rating_monthly": rating_monthly
#                     }
#                 }
#             )
#
#         except ValidationError as e:
#             return self.send_response(
#                 success=False,
#                 code='422',
#                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                 description=str(e)
#             )
#
#         except Exception as e:
#             return self.send_response(
#                 success=False,
#                 description=str(e))
