""" This file includes utilities."""
import asyncio
import copy
import io
import json
import os
import random
from datetime import time

import tempfile
# import time
import uuid
import zipfile

import stripe
from django.contrib.staticfiles.storage import staticfiles_storage
from concurrent.futures.thread import ThreadPoolExecutor
from django.core.cache import caches

# import boto3
import requests
import sendgrid
# from __future__ import print_function

# from PIL.Image import Image
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage, FileSystemStorage

import hmac
import hashlib
import base64

import requests
from urllib.parse import urlparse, unquote
from os.path import basename, splitext

from firebase_admin import messaging, credentials


def get_epoch_time(to_string=False):
    """
    return epoch time
    :param to_string: Boolean, True means convert to String
    :return:
    """
    seconds = int(time.time())
    if to_string:
        return str(seconds)
    return seconds


def slugify_name(string_):
    """
    Convert given string into slugify
    :param string_: String
    :return: String
    """
    if string_:
        slugify_str = '_'.join(string_.split(' '))
        return slugify_str
    return string_


def boolean(value):
    """Parse the string ``"true"`` or ``"false"`` as a boolean (case
    insensitive). Also accepts ``"1"`` and ``"0"`` as ``True``/``False``
    (respectively). If the input is from the request JSON body, the type is
    already a native python boolean, and will be passed through without
    further parsing.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        raise ValueError("boolean type must be non-null")
    value = str(value).lower()
    if value in ('true', 'yes', '1', 1):
        return True
    if value in ('false', 'no', '0', 0, ''):
        return False
    raise ValueError("Invalid literal for boolean(): {0}".format(value))


def parse_email(obj):
    return obj.replace(" ", "").lower()


def parse_integer(obj):
    return obj if obj else 0


from datetime import datetime, timedelta


def time_difference(start_time, end_time):
    date_today = datetime.today().date()
    datetime_start = datetime.combine(date_today, start_time)
    datetime_end = datetime.combine(date_today, end_time)
    if datetime_end < datetime_start:
        datetime_end += timedelta(days=1)

        # Calculate the time difference
    return datetime_end - datetime_start


def calaculate_hours(time_records):
    # Initialize total time to 0
    total_duration = timedelta()

    # Iterate over each record in the array of objects
    for record in time_records:
        start_time = record['start_time']  # TimeField (e.g., 08:00:00)
        end_time = record['end_time']  # TimeField (e.g., 15:30:00)
        total_duration += time_difference(start_time, end_time)

    # Convert total duration to hours
    return total_duration.total_seconds() / 3600


def combine_date_time(arr):
    return list(map(lambda x: {"start_time": datetime.strptime(f'{x["date"]} {x["start_time"]}', "%Y-%m-%d %H:%M:%S"),
                               "end_time": datetime.strptime(f'{x["date"]} {x["end_time"]}', "%Y-%m-%d %H:%M:%S")},
                    arr))


from datetime import datetime


def is_overlap(start1, end1, start2, end2):
    # Returns True if two intervals overlap
    return start1 < end2 and end1 > start2


# Sort the arrays by 'start_time'
def find_overlapping_intervals(array1, array2):
    array1 = sorted(array1, key=lambda x: x['start_time'])
    array2 = sorted(array2, key=lambda x: x['start_time'])

    overlapping_objects = []
    i, j = 0, 0

    # Use two pointers to find overlaps
    while i < len(array1) and j < len(array2):
        obj1 = array1[i]
        obj2 = array2[j]

        start1, end1 = obj1['start_time'], obj1['end_time']
        start2, end2 = obj2['start_time'], obj2['end_time']

        # Check if obj1 overlaps with obj2
        if is_overlap(start1, end1, start2, end2):
            overlapping_objects.append(obj1)

        # Move the pointer that has the earlier end time
        if end1 < end2:
            i += 1
        else:
            j += 1

    return overlapping_objects


# Example arrays of time intervals
# array1 = [
#     {'start_time': datetime(2024, 9, 21, 10, 0), 'end_time': datetime(2024, 9, 21, 12, 0)},
#     {'start_time': datetime(2024, 9, 21, 14, 0), 'end_time': datetime(2024, 9, 21, 16, 0)},
# ]
#
# array2 = [
#     {'start_time': datetime(2024, 9, 21, 11, 30), 'end_time': datetime(2024, 9, 21, 13, 30)},
#     {'start_time': datetime(2024, 9, 21, 15, 0), 'end_time': datetime(2024, 9, 21, 17, 0)},
# ]
#
# # Find overlapping objects
# overlapping_objects = find_overlapping_intervals(array1, array2)


class SingletonMetaclass(type):
    instance = {}

    def __call__(cls):
        if cls not in cls.instance:
            cls.instance[cls] = super().__call__()
        return cls.instance[cls]


class FCMNotifications(metaclass=SingletonMetaclass):

    def __init__(self):
        self.cred = credentials.Certificate(
            staticfiles_storage.path('playon-6dfe3-firebase-adminsdk-1zok1-8855bf7152'))
        firebase_admin.initialize_app(self.cred)

    def send_fcm_notification(self, token, title, body, data):
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
            data=data
        )

        # Send the message
        response = messaging.send(message)
        print('Successfully sent message:', response)

    def send_bulk_notification(self, token, title, body, data):
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,

            ),
            tokens=token,
            data=data

        )

        # Send the message
        response = messaging.send_each_for_multicast(message)
        print('Successfully sent message:', response)


def generate_time_slots_with_object(start, end, data):
    slots = {}
    current_time = start
    while current_time < end:
        new_hour = (current_time.hour + 1) % 24  # Ensure it wraps around 24 hours
        next_time = time(new_hour, current_time.minute, current_time.second)
        slots[f"{current_time}_{next_time}"] = copy.copy(data)
        current_time = next_time
    return slots


def generate_time_slots(start, end):
    slots = []
    current_time = start
    while current_time < end:
        new_hour = (current_time.hour + 1) % 24  # Ensure it wraps around 24 hours
        next_time = time(new_hour, current_time.minute, current_time.second)
        slots.append(f"{current_time}_{next_time}")
        current_time = next_time
    return slots




