import os

from celery import shared_task
from django.apps import apps

from api.bookings.models import Booking
import sendgrid
import sib_api_v3_sdk
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from sib_api_v3_sdk.rest import ApiException

from config.utils import FCMNotifications


@shared_task()
def cancel_booking(booking_id):
    booking = apps.get_model("bookings", "Booking")
    booking = booking.objects.get(id=booking_id)
    if booking.booking_status.last().status == 'pending':
        booking.delete()

    # query = booking_status.objects.filter(booking_id=booking_id, is_active=True)
    # status = query.last()
    # if status.status == 'pending':
    #     query.update(is_active=False)
    #     booking_status.objects.create(status='cancelled',booking_id=booking_id)



import datetime
import json
import logging

import requests


send_email_logger = logging.getLogger('send_email')


# print(f'CELERY LOGGER {str(logger.name)}')




#
@shared_task
def send_sms_brevo(recipient, content):
    """
    sender: Name of the sender. The number of characters is limited to 11 for alphanumeric characters and 15 for numeric characters
    sms: Mobile number to send SMS with the country code (33689965433)
    content: Content of the message. If more than 160 characters long, will be sent as multiple text messages
    type: transactional : marketing
    """
    recipient =recipient.replace("+","")
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv('BREVO_API_KEY')

    api_instance = sib_api_v3_sdk.TransactionalSMSApi(sib_api_v3_sdk.ApiClient(configuration))
    send_transac_sms = sib_api_v3_sdk.SendTransacSms(
        sender=os.getenv('SMS_SENDER'),
        # recipient="923418389849",
        recipient=recipient,
        content=content,
        type="transactional",
        unicode_enabled=True
    )
    try:
        api_response = api_instance.send_transac_sms(send_transac_sms)
        print(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


@shared_task()
def send_async_emil(recipient, template_id, params):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    sender = {"email": settings.BREVO_CONTACT_US_EMAIL}
    to = [{"email": recipient}]
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, sender=sender, template_id=template_id,
                                                   params=params)

    try:
        if recipient:
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)


@shared_task()
def async_push_notification(title, msg, tokens, data):
    try:
        a = FCMNotifications()
        if type(tokens) is list:
            a.send_bulk_notification(
                token=tokens,
                title=title,
                body=msg,
                data=data
            )
        else:
            a.send_fcm_notification(
                token=tokens,
                title=title,
                body=msg,
                data=data
            )
    except Exception as e:
        return