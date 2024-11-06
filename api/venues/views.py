import os

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Q, Prefetch
from django.shortcuts import render

# Create your views here.
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import status

from api.permissions import IsCustomerAuthenticated, IsAdminAuthenticated
from api.vendor.models import Venue
from api.vendor.serializers import VenueSerializer
from api.views import BaseAPIView
from django.utils.translation import gettext as _


class CustomersVenuesView(BaseAPIView):
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
            type = request.query_params.get('type', None)
            latitude = float(request.query_params.get('latitude', 0))
            longitude = float(request.query_params.get('longitude', 0))

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

                if type:
                    query_set &= Q(type__contains=[type])

                if search:
                    query_set &= Q(name__icontains=search) | Q(id__contains=search)

                if latitude and longitude:
                    query_set &= Q(distance__lte=float(os.getenv("RECOMMENDATION_DIAMETER")))

                # .annotate(distance=Distance('loc', Point(longitude, latitude, srid=4326))) \

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
                        "images",
                        "type"
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


class VenuesAdminView(BaseAPIView):
    authentication_classes = (OAuth2Authentication,)
    permission_classes = (IsAdminAuthenticated,)

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # is_active = request.query_params.get('is-active', None)
            column = request.query_params.get('column', "id")
            order_by = request.query_params.get('order-by', "desc")
            search = request.query_params.get('search', None)
            order_by = self.get_sorting_query(order_by, column)
            type = request.query_params.get('type', None)
            vendor_id = request.query_params.get("vendor_id")
            # latitude = float(request.query_params.get('latitude', 0))
            # longitude = float(request.query_params.get('longitude', 0))

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

                if vendor_id:
                    query_set &= Q(vendor_id=vendor_id)

                if type:
                    query_set &= Q(type__contains=[type])

                if search:
                    query_set &= Q(name__icontains=search) | Q(id__contains=search)

                # if latitude and longitude:
                #     query_set &= Q(distance__lte=float(os.getenv("RECOMMENDATION_DIAMETER")))

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
                        "images",
                        "type"
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
